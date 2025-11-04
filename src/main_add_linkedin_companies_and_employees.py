import sys
import os
import argparse
import time
import random
import webbrowser
from typing import Iterable

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_prospection import ProspectionDB, CompanyDB


DEFAULT_DB_PATH = os.getenv('PROSPECTION_DB_PATH', 'prospection_data.db')


def _normalise_company_link(link: str) -> str:
    """Ensure LinkedIn URLs include a protocol and trim whitespace."""

    cleaned = (link or '').strip()
    if cleaned.startswith(('http://', 'https://')):
        return cleaned

    return f'https://{cleaned.lstrip('/')}'


def _open_company_pages(companies: Iterable[CompanyDB]) -> None:
    """Open each company page in a new browser tab with a short delay."""

    for index, company in enumerate(companies, start=1):
        url = _normalise_company_link(company.link)
        webbrowser.open_new_tab(url)
        print(f'  [{index}] Opening company: {company.name} - {url}')
        time.sleep(1)


def add_company_with_validation(prospection_db: ProspectionDB, nb_open_companies_at_once: int = 8):
    """Manually confirm each batch of company pages before they are opened."""

    print('Manual company follow workflow ready.')

    while True:
        pending_companies = prospection_db.get_all_companies_not_added()
        if not pending_companies:
            print('No more companies available to open.')
            break

        print(f'Companies waiting to be followed: {len(pending_companies)}')
        user_input = input("Press 'Y' to open the next batch of company pages (any other key to stop): ")
        if user_input not in ['y', 'Y']:
            print('Stopping manual follow workflow.')
            break

        batch = pending_companies[:nb_open_companies_at_once]
        _open_company_pages(batch)
        for company in batch:
            prospection_db.updateAddedCompany(company)


def auto_add_companies_with_total_limit(
    prospection_db: ProspectionDB,
    max_nb_companies_to_add: int
) -> int:
    """Open a limited number of company pages and mark them as followed in the database."""

    companies_to_add = prospection_db.get_all_companies_not_added()[:max_nb_companies_to_add]

    print(f'Processing {len(companies_to_add)} companies...')
    processed_count = 0

    for i, company in enumerate(companies_to_add):
        url = _normalise_company_link(company.link)
        webbrowser.open_new_tab(url)
        print(f'  [{i + 1}/{len(companies_to_add)}] Opening company: {company.name} - {url}')
        prospection_db.updateAddedCompany(company)
        processed_count += 1

        if i < len(companies_to_add) - 1:
            delay = random.uniform(1.0, 3.0)
            print(f'    ⏱️  Random delay before next company: {delay:.1f}s')
            time.sleep(delay)

    return processed_count


def auto_add_companies(prospection_db: ProspectionDB, max_nb_companies_to_add: int) -> bool:
    """Legacy helper that opens a random number of company pages."""

    randomized_target = random.randint(int(max_nb_companies_to_add / 2), max_nb_companies_to_add)
    print(f'Random number of companies to add this round: {randomized_target}')

    companies_to_add = prospection_db.get_all_companies_not_added()[:randomized_target]

    print(f'Total companies not yet followed: {len(companies_to_add)}')
    _open_company_pages(companies_to_add)
    for company in companies_to_add:
        prospection_db.updateAddedCompany(company)
    return len(companies_to_add) > 0


def auto_follow_companies_with_batches(
    prospection_db: ProspectionDB,
    total_companies: int,
    companies_per_batch: int = 20,
    avg_batch_delay: int = 60
):
    """Automate opening company pages in batches with randomized delays between batches."""

    if total_companies <= 0:
        print('No companies requested. Exiting automation.')
        return

    print('🚀 Starting LinkedIn company follow automation')
    print(f'  Target companies: {total_companies}')
    print(f'  Companies per batch: {companies_per_batch}')
    print(f'  Average delay between batches: {avg_batch_delay} seconds')

    companies_processed = 0
    batch_number = 1

    while companies_processed < total_companies:
        remaining_companies = total_companies - companies_processed
        batch_companies = min(companies_per_batch, remaining_companies)

        print(f"\nBatch {batch_number}: preparing to open {batch_companies} company pages")
        processed = auto_add_companies_with_total_limit(
            prospection_db,
            batch_companies
        )
        companies_processed += processed

        if processed == 0:
            print('No more companies found in the database. Ending automation.')
            break

        if companies_processed >= total_companies:
            print('\n✅ Automation complete!')
            print(f'   Companies followed: {companies_processed}')
            break

        batch_delay_variation = max(0, avg_batch_delay + random.randint(-10, 10))
        print(f'Waiting approximately {batch_delay_variation} seconds before the next batch...')
        time.sleep(batch_delay_variation)
        batch_number += 1



def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Company Follow Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 src/main_add_linkedin_companies_and_employees.py
  python3 src/main_add_linkedin_companies_and_employees.py --total-companies 30 --companies-per-batch 10
        """
    )

    parser.add_argument(
        '-c', '--total-companies',
        type=int,
        default=50,
        help='Total number of companies to follow (default: 50)'
    )

    parser.add_argument(
        '--companies-per-batch',
        type=int,
        default=20,
        help='Number of companies to open per batch (default: 20, recommended: 5-15)'
    )

    parser.add_argument(
        '--batch-delay',
        type=int,
        default=60,
        help='Average delay between batches in seconds (default: 60, recommended: 45-120)'
    )

    parser.add_argument(
        '--manual',
        action='store_true',
        help='Use manual confirmation mode instead of automated batches.'
    )

    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='Path to the SQLite database (default: PROSPECTION_DB_PATH or prospection_data.db)'
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    db_path = args.db_path or DEFAULT_DB_PATH
    prospection_db = ProspectionDB(db_path)

    print(f'Using database at: {os.path.abspath(db_path)}')

    if args.manual:
        add_company_with_validation(prospection_db, args.companies_per_batch)
    else:
        auto_follow_companies_with_batches(
            prospection_db=prospection_db,
            total_companies=args.total_companies,
            companies_per_batch=args.companies_per_batch,
            avg_batch_delay=args.batch_delay
        )
