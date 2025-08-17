import sys
import os
import logging
# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.csv_parser import BuiltwithCSVParser, MantiksCSVParser
from src.parser_visitors import SQLLiteSaveVisitor
from src.db_prospection import ProspectionDB

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_builtwith_files():
    # requires unzipped files
    builtwith_dir = '/Users/xxx/Builtwith'
    bfile1 = builtwith_dir + '/' + 'React-websites-in-France.csv'
    bfile2 = builtwith_dir + '/' + 'React-websites-in-Germany.csv'
    bfile3 = builtwith_dir + '/' + 'React-websites-in-the-United-Kingdom.csv'

    # sysoutVisitor is only useful for debug
    #sysout_visitor = SysoutVisitor()
    sqlite_visitor = SQLLiteSaveVisitor('prospection_data.db', False)
    bfiles = [bfile1, bfile2, bfile3]
    for bfile in bfiles:
        logging.info(f"Processing Builtwith file: {os.path.basename(bfile)}")
        parsed_file = BuiltwithCSVParser(bfile, 'Company', 'Linkedin', '')
        
        # Log companies being added
        companies = parsed_file.get_companies()
        logging.info(f"Found {len(companies)} companies in {os.path.basename(bfile)}")
        for company in companies:
            if company and company.name:
                logging.info(f"Adding company to DB: {company.name}")
        
        sqlite_visitor.visit(parsed_file)
        logging.info(f"Completed processing {os.path.basename(bfile)}")


def load_mantiks_files():
    dir = '/Users/xxx/Mantiks'
    file1 = dir + '/' + 'Développeur React Freelance Moins De 1000 Salarié.csv'
    file2 = dir + '/' + 'Node.Js - 6 mois à partir du 23_02_2025.csv'
    file3 = dir + '/' + 'Node.JS - Freelance Entreprise De Moins De 1000 Salariés.csv'
    file4 = dir + '/' + 'Node.JS - Télétravail Entreprise De Moins De 1000 Salariés.csv'
    file5 = dir + '/' + 'React - Entreprise de 1 à 10000 salariés sur 6 mois à partir du 13_02_2025.csv'
    file6 = dir + '/' + 'React Native - All TIME.csv'
    file7 = dir + '/' + 'React Native Freelance - Entreprise De Moins De 1000 Salariés.csv'
    file8 = dir + '/' + 'React Native Télétravail - Entreprise De Moins De 1000 Salariés.csv'
    file9 = dir + '/' + 'React Télétravail CDI Entreprise De Moins De 1000 Salariés En France.csv'


    sqlite_visitor = SQLLiteSaveVisitor('prospection_data.db', False)
    
    # Create parsers and process them with logging
    parsers_info = [
        (file1, 'Company name', 'Company LinkedIn', 'LinkedIn profil', 'Développeur React Freelance'),
        (file2, 'Nom de l\'entreprise', 'LinkedIn Entreprise', '', 'Node.Js - 6 mois'),
        (file3, 'Company name', 'Company LinkedIn', 'LinkedIn profil', 'Node.JS - Freelance'),
        (file4, 'Company name', 'Company LinkedIn', 'Company LinkedIn Employees', 'Node.JS - Télétravail'),
        (file5, 'Nom de l\'entreprise', 'LinkedIn Entreprise', 'Profile LinkedIn', 'React - Entreprise'),
        (file6, 'Nom de l\'entreprise', 'LinkedIn Entreprise', '', 'React Native - All TIME'),
        (file7, 'Company name', 'Company LinkedIn', 'LinkedIn profil', 'React Native Freelance'),
        (file8, 'Company name', 'Company LinkedIn', 'LinkedIn profil', 'React Native Télétravail'),
        (file9, 'Company name', 'Company LinkedIn', 'LinkedIn profil', 'React Télétravail CDI')
    ]
    
    for file_path, company_name_col, company_link_col, employee_link_col, description in parsers_info:
        logging.info(f"Processing Mantiks file: {description}")
        mantiks_parser = MantiksCSVParser(file_path, company_name_col, company_link_col, employee_link_col)
        
        # Log companies being added
        companies = mantiks_parser.get_companies()
        logging.info(f"Found {len(companies)} companies in {description}")
        for company in companies:
            if company and company.name:
                logging.info(f"Adding company to DB: {company.name}")
        
        sqlite_visitor.visit(mantiks_parser)
        logging.info(f"Completed processing {description}")

if __name__ == '__main__':
    db = ProspectionDB('prospection_data.db') # it will create a "prospection_data.db" in this current folder
    db.init_db(drop_existing=False)
    load_builtwith_files()
    load_mantiks_files()


