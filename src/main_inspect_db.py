import sys
import os
from datetime import datetime
# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_prospection import ProspectionDB

prospection_db_name = 'prospection_data.db'

def print_separator(title: str = "", width: int = 60):
    """Print a formatted separator with optional title"""
    if title:
        print(f"\n{'=' * width}")
        print(f" {title} ".center(width))
        print(f"{'=' * width}")
    else:
        print("-" * width)

def print_stats_table(stats: dict, entity_type: str):
    """Print statistics in a formatted table"""
    print(f"\n{entity_type.upper()} STATISTICS:")
    print(f"{'Metric':<20} {'Count':<10} {'Percentage':<12}")
    print("-" * 42)
    print(f"{'Total':<20} {stats['total']:<10} {'100.0%':<12}")
    print(f"{'Added':<20} {stats['added']:<10} {stats['percentage_added']:<11.1f}%")
    print(f"{'Remaining':<20} {stats['remaining']:<10} {100 - stats['percentage_added']:<11.1f}%")

def display_comprehensive_stats():
    """Display comprehensive statistics about the prospection database"""
    db = ProspectionDB(prospection_db_name)
    
    print_separator("PROSPECTION DATABASE STATISTICS")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get and display company statistics
    company_stats = db.get_companies_stats()
    print_stats_table(company_stats, "company")
    
    # Get and display employee statistics
    employee_stats = db.get_employees_stats()
    print_stats_table(employee_stats, "employee")
    
    # Overall progress summary
    print_separator("OVERALL PROGRESS SUMMARY")
    total_entities = company_stats['total'] + employee_stats['total']
    total_added = company_stats['added'] + employee_stats['added']
    total_remaining = company_stats['remaining'] + employee_stats['remaining']
    overall_percentage = (total_added / total_entities * 100) if total_entities > 0 else 0
    
    print(f"Total Entities: {total_entities}")
    print(f"Total Added: {total_added}")
    print(f"Total Remaining: {total_remaining}")
    print(f"Overall Progress: {overall_percentage:.1f}%")
    
    # Progress bar
    bar_width = 40
    filled_width = int(bar_width * overall_percentage / 100)
    bar = "█" * filled_width + "░" * (bar_width - filled_width)
    print(f"Progress: [{bar}] {overall_percentage:.1f}%")

def display_sample_data(nb_companies: int = 5, nb_employees: int = 5):
    """Display sample data from companies and employees not yet added"""
    db = ProspectionDB(prospection_db_name)
    
    print_separator("SAMPLE DATA - COMPANIES NOT ADDED")
    companies = db.get_all_companies_not_added()[:nb_companies]
    if companies:
        for i, company in enumerate(companies, 1):
            print(f"{i:2d}. {company.name[:50]:<50} | {company.link}")
    else:
        print("No companies remaining to add.")
    
    print_separator("SAMPLE DATA - EMPLOYEES NOT ADDED")
    employees = db.get_all_employees_not_added()[:nb_employees]
    if employees:
        for i, employee in enumerate(employees, 1):
            company_name = employee.company.name[:30] if employee.company.name else "Unknown"
            print(f"{i:2d}. Employee: {employee.link}")
            print(f"    Company: {company_name} | {employee.company.link}")
    else:
        print("No employees remaining to add.")

def display_recently_added(nb_companies: int = 5, nb_employees: int = 5):
    """Display recently added companies and employees"""
    db = ProspectionDB(prospection_db_name)
    
    print_separator("RECENTLY ADDED - COMPANIES")
    added_companies = db.get_all_companies_added()[-nb_companies:] if db.get_all_companies_added() else []
    if added_companies:
        for i, company in enumerate(added_companies, 1):
            print(f"{i:2d}. {company.name[:50]:<50} | {company.link}")
    else:
        print("No companies have been added yet.")
    
    print_separator("RECENTLY ADDED - EMPLOYEES")
    added_employees = db.get_all_employees_added()[-nb_employees:] if db.get_all_employees_added() else []
    if added_employees:
        for i, employee in enumerate(added_employees, 1):
            company_name = employee.company.name[:30] if employee.company.name else "Unknown"
            print(f"{i:2d}. Employee: {employee.link}")
            print(f"    Company: {company_name} | {employee.company.link}")
    else:
        print("No employees have been added yet.")

def update_companies_already_added(nb_companies: int):
    """Update specified number of companies as added (for testing purposes)"""
    db = ProspectionDB(prospection_db_name)
    companies = db.get_all_companies_not_added()[:nb_companies]
    
    print(f"\nMarking {len(companies)} companies as added:")
    for company in companies:
        print(f"  - {company.name}: {company.link}")
        # Uncomment the line below to actually update the database
        # db.updateAddedCompany(company)
    
    print(f"\nTo actually update the database, uncomment the updateAddedCompany line in the code.")

def main():
    """Main function to display all statistics and information"""
    display_comprehensive_stats()
    print_separator()
    display_sample_data()
    print_separator()
    display_recently_added()
    print_separator()

if __name__ == '__main__':
    main()

