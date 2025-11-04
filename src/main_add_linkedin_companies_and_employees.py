import sys
import os
import argparse
import time
import random
import webbrowser

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_prospection import ProspectionDB


def add_company_with_validation(nb_open_companies_at_once: int = 8):
    """Manually confirm each batch of company pages before they are opened."""
    prospection_db = ProspectionDB('prospection_data.db')
    all_companies = prospection_db.get_all_companies_not_added()
    print(f'Total companies waiting to be followed: {len(all_companies)}')

    counter = 0
    companies_to_open = []

    def update_companies_status():
        for company in companies_to_open:
            prospection_db.updateAddedCompany(company)

    while True:
        update_companies_status()

        if counter >= len(all_companies):
            print('No more companies available to open.')
            break

        user_input = input("Press 'Y' to open the next batch of company pages (any other key to stop): ")
        if user_input in ['y', 'Y']:
            companies_to_open = all_companies[counter:counter + nb_open_companies_at_once]
            for company in companies_to_open:
                link = company.link if company.link.startswith('http') else 'http://' + company.link
                webbrowser.open(link)
                print(f'Opening company: {company.name} - {company.link}')
                time.sleep(1)
            counter += nb_open_companies_at_once
        else:
            print('Stopping manual follow workflow.')
            break


def auto_add_companies_with_total_limit(max_nb_companies_to_add: int) -> int:
    """Open a limited number of company pages and mark them as followed in the database."""
    prospection_db = ProspectionDB('prospection_data.db')

    companies_to_add = prospection_db.get_all_companies_not_added()[:max_nb_companies_to_add]

    print(f'Processing {len(companies_to_add)} companies...')
    processed_count = 0

    for i, company in enumerate(companies_to_add):
        link = company.link if company.link.startswith('http') else 'http://' + company.link
        webbrowser.open(link)
        print(f'  [{i + 1}/{len(companies_to_add)}] Opening company: {company.name} - {company.link}')
        prospection_db.updateAddedCompany(company)
        processed_count += 1

        if i < len(companies_to_add) - 1:
            delay = random.uniform(1.0, 3.0)
            print(f'    ⏱️  Random delay before next company: {delay:.1f}s')
            time.sleep(delay)

    return processed_count


def auto_add_companies(max_nb_companies_to_add: int) -> bool:
    """Legacy helper that opens a random number of company pages."""
    prospection_db = ProspectionDB('prospection_data.db')
    randomized_target = random.randint(int(max_nb_companies_to_add / 2), max_nb_companies_to_add)
    print(f'Random number of companies to add this round: {randomized_target}')

    companies_to_add = prospection_db.get_all_companies_not_added()[:randomized_target]

    print(f'Total companies not yet followed: {len(companies_to_add)}')
    for company in companies_to_add:
        link = company.link if company.link.startswith('http') else 'http://' + company.link
        webbrowser.open(link)
        print(f'Opening company: {company.name} - {company.link}')
        prospection_db.updateAddedCompany(company)
        time.sleep(1)
    return len(companies_to_add) > 0


def auto_follow_companies_with_batches(
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
        processed = auto_add_companies_with_total_limit(batch_companies)
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

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    if args.manual:
        add_company_with_validation(args.companies_per_batch)
    else:
        auto_follow_companies_with_batches(
            total_companies=args.total_companies,
            companies_per_batch=args.companies_per_batch,
            avg_batch_delay=args.batch_delay
        )
