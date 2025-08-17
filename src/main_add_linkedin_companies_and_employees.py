import sys
import os
import argparse
# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_prospection import ProspectionDB
import time
import webbrowser

# more than this number can lead to not loaded pages
def add_company_with_validation(nb_open_companies_at_once: int = 8):
    prospection_db = ProspectionDB('prospection_data.db')
    all_companies = prospection_db.get_all_companies_not_added()
    print('Total nb companies not added : ' + str(len(all_companies)))

    counter = 0
    companies_to_open = []

    def update_companies_status():
        for c in companies_to_open:
            prospection_db.updateAddedCompany(c)

    while(True):
        update_companies_status()

        if counter >= len(all_companies):
            print('No more companies to open')
            break

        user_input = input("Press 'Y' to continue...")
        if user_input in ['y', 'Y']:
            # open new companies in browser
            companies_to_open = all_companies[counter:counter + nb_open_companies_at_once]
            for company in companies_to_open:
                link =  company.link if company.link.startswith('http') else 'http://' + company.link
                webbrowser.open(link)
                print('Opening company : ' + company.name + " - " + company.link)
                time.sleep(1)
            counter += nb_open_companies_at_once
        else:
            break

def add_employee_with_validation(nb_open_employees_at_once: int = 8):
    prospection_db = ProspectionDB('prospection_data.db')
    all_employees = prospection_db.get_all_employees_not_added()
    print('Total nb employees not added : ' + str(len(all_employees)))

    counter = 0
    employees_to_open = []

    def update_employees_status():
        for e in employees_to_open:
            prospection_db.updateAddedEmployee(e)

    while(True):
        update_employees_status()

        if counter >= len(all_employees):
            print('No more employees to open')
            break

        user_input = input("Press 'Y' to continue...")
        if user_input in ['y', 'Y']:
            # open new employees in browser
            employees_to_open = all_employees[counter:counter + nb_open_employees_at_once]
            for employee in employees_to_open:
                link = employee.link if employee.link.startswith('http') else 'http://' + employee.link
                webbrowser.open(link)
                print('Opening employee : ' + str(employee.link) + " - Company: " + employee.company.name)
                time.sleep(1)
            counter += nb_open_employees_at_once
        else:
            break

def auto_add_employees_and_companies_with_batch_delay(
    total_employees: int, 
    total_companies: int, 
    nb_employees_per_batch: int = 20, 
    nb_companies_per_batch: int = 30, 
    avg_batch_delay: int = 60
):
    """
    Enhanced automation with total limits and random delays
    
    Args:
        total_employees: Total number of employees to connect (across all batches)
        total_companies: Total number of companies to follow (across all batches)
        nb_employees_per_batch: Number of employees per batch
        nb_companies_per_batch: Number of companies per batch
        avg_batch_delay: Average delay between batches in seconds
    """
    import random
    
    employees_processed = 0
    companies_processed = 0
    
    print(f"🚀 Starting automation:")
    print(f"   Target: {total_employees} employees, {total_companies} companies")
    print(f"   Batch size: {nb_employees_per_batch} employees, {nb_companies_per_batch} companies")
    print(f"   Batch delay: ~{avg_batch_delay} seconds")
    
    while employees_processed < total_employees or companies_processed < total_companies:
        batch_start_time = time.time()
        
        # Process employees first (if any remaining)
        if employees_processed < total_employees:
            remaining_employees = total_employees - employees_processed
            batch_employees = min(nb_employees_per_batch, remaining_employees)
            
            if batch_employees > 0:
                print(f"\n👥 Processing {batch_employees} employees (Progress: {employees_processed}/{total_employees})")
                processed = auto_add_employees_with_total_limit(batch_employees)
                employees_processed += processed
        
        # Process companies (if any remaining)
        if companies_processed < total_companies:
            remaining_companies = total_companies - companies_processed
            batch_companies = min(nb_companies_per_batch, remaining_companies)
            
            if batch_companies > 0:
                print(f"\n🏢 Processing {batch_companies} companies (Progress: {companies_processed}/{total_companies})")
                processed = auto_add_companies_with_total_limit(batch_companies)
                companies_processed += processed
        
        # Check if we're done
        if employees_processed >= total_employees and companies_processed >= total_companies:
            print(f"\n✅ Automation complete!")
            print(f"   Employees connected: {employees_processed}")
            print(f"   Companies followed: {companies_processed}")
            break
        
        # Batch delay only if there's more work to do
        if employees_processed < total_employees or companies_processed < total_companies:
            batch_delay_variation = avg_batch_delay + random.randint(-10, 10)
            print(f"\n⏱️  Batch delay: {batch_delay_variation} seconds")
            time.sleep(batch_delay_variation)

def auto_add_companies_with_batch_delay(nb_companies: int, avg_batch_delay: int, max_iter=6):
    import random
    can_add_companies = True
    current_iter = 0
    while(can_add_companies and current_iter < max_iter):
        can_add_companies = auto_add_companies(nb_companies)
        current_iter += 1
        if can_add_companies:
            batch_delay_variation = avg_batch_delay + random.randint(-10, 10)
            print("Batch delay variation : " + str(batch_delay_variation))
            time.sleep(batch_delay_variation)

# uses plugin to open browser and update status in DB
def auto_add_employees_with_total_limit(max_nb_employees_to_add: int) -> int:
    """
    Add employees with random delays between each action
    Returns the actual number of employees processed
    """
    import random
    prospection_db = ProspectionDB('prospection_data.db')
    
    employees_to_add = prospection_db.get_all_employees_not_added()[:max_nb_employees_to_add]

    print(f'Processing {len(employees_to_add)} employees...')
    processed_count = 0
    
    for i, employee in enumerate(employees_to_add):
        link = employee.link if employee.link.startswith('http') else 'http://' + employee.link
        webbrowser.open(link)
        print(f'  [{i+1}/{len(employees_to_add)}] Opening employee: {employee.link} - Company: {employee.company.name}')
        prospection_db.updateAddedEmployee(employee)
        processed_count += 1
        
        # Random delay between 1-3 seconds for each employee
        if i < len(employees_to_add) - 1:  # Don't delay after the last one
            delay = random.uniform(1.0, 3.0)
            print(f'    ⏱️  Random delay: {delay:.1f}s')
            time.sleep(delay)
    
    return processed_count

# uses plugin to open browser and update status in DB (legacy function)
def auto_add_employees(max_nb_employees_to_add: int) -> bool:
    import random
    prospection_db = ProspectionDB('prospection_data.db')
    max_nb_employees_to_add = random.randint(int(max_nb_employees_to_add / 2), max_nb_employees_to_add)
    print('Random number of employees to connect : ' + str(max_nb_employees_to_add))

    employees_to_add = prospection_db.get_all_employees_not_added()[:max_nb_employees_to_add]

    print('Total nb employees not added : ' + str(len(employees_to_add)))
    for employee in employees_to_add:
        link = employee.link if employee.link.startswith('http') else 'http://' + employee.link
        webbrowser.open(link)
        print('Opening employee : ' + str(employee.link) + " - Company: " + employee.company.name)
        prospection_db.updateAddedEmployee(employee)
        time.sleep(1)
    return len(employees_to_add) > 0

# uses plugin to open browser and update status in DB
def auto_add_companies_with_total_limit(max_nb_companies_to_add: int) -> int:
    """
    Add companies with random delays between each action
    Returns the actual number of companies processed
    """
    import random
    prospection_db = ProspectionDB('prospection_data.db')
    
    companies_to_add = prospection_db.get_all_companies_not_added()[:max_nb_companies_to_add]

    print(f'Processing {len(companies_to_add)} companies...')
    processed_count = 0
    
    for i, company in enumerate(companies_to_add):
        link = company.link if company.link.startswith('http') else 'http://' + company.link
        webbrowser.open(link)
        print(f'  [{i+1}/{len(companies_to_add)}] Opening company: {company.name} - {company.link}')
        prospection_db.updateAddedCompany(company)
        processed_count += 1
        
        # Random delay between 1-3 seconds for each company
        if i < len(companies_to_add) - 1:  # Don't delay after the last one
            delay = random.uniform(1.0, 3.0)
            print(f'    ⏱️  Random delay: {delay:.1f}s')
            time.sleep(delay)
    
    return processed_count

# uses plugin to open browser and update status in DB (legacy function)
def auto_add_companies(max_nb_companies_to_add: int) -> bool:
    import random
    prospection_db = ProspectionDB('prospection_data.db')
    max_nb_companies_to_add = random.randint(int(max_nb_companies_to_add / 2), max_nb_companies_to_add)
    print('Random number of companies to add : ' + str(max_nb_companies_to_add))

    companies_to_add = prospection_db.get_all_companies_not_added()[:max_nb_companies_to_add]

    print('Total nb companies not added : ' + str(len(companies_to_add)))
    for company in companies_to_add:
        link =  company.link if company.link.startswith('http') else 'http://' + company.link
        webbrowser.open(link)
        print('Opening company : ' + str(company.name) + " - " + company.link)
        prospection_db.updateAddedCompany(company)
        time.sleep(1)
    return len(companies_to_add) > 0

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="LinkedIn Automation Suite - Automate employee connections and company follows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 src/main_add_linkedin_companies_and_employees.py
  python3 src/main_add_linkedin_companies_and_employees.py --total-employees 10 --total-companies 25
  python3 src/main_add_linkedin_companies_and_employees.py -e 5 -c 15
        """
    )
    
    parser.add_argument(
        '-e', '--total-employees',
        type=int,
        default=0,
        help='Total number of employees to connect with (default: 0)'
    )
    
    parser.add_argument(
        '-c', '--total-companies',
        type=int,
        default=50,
        help='Total number of companies to follow (default: 50)'
    )
    
    parser.add_argument(
        '--employees-per-batch',
        type=int,
        default=5,
        help='Number of employees per batch (default: 5, recommended: 3-8)'
    )
    
    parser.add_argument(
        '--companies-per-batch',
        type=int,
        default=20,
        help='Number of companies per batch (default: 20, recommended: 5-15)'
    )
    
    parser.add_argument(
        '--batch-delay',
        type=int,
        default=60,
        help='Average delay between batches in seconds (default: 60, recommended: 45-120)'
    )
    
    return parser.parse_args()

if __name__ == '__main__':
    print("🚀 LinkedIn Automation Suite")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Enhanced automation with total limits and random delays
    auto_add_employees_and_companies_with_batch_delay(
        total_employees=args.total_employees,
        total_companies=args.total_companies,
        nb_employees_per_batch=args.employees_per_batch,
        nb_companies_per_batch=args.companies_per_batch,
        avg_batch_delay=args.batch_delay
    )
    
    # Alternative automation options (commented out):
    
    # Legacy company-only automation
    #auto_add_companies_with_batch_delay(10, 60, 5)
    
    # Manual validation modes
    #add_company_with_validation(8)
    #add_employee_with_validation(8)
    
    # Individual function calls for testing
    #auto_add_employees_with_total_limit(5)
    #auto_add_companies_with_total_limit(10)