# 🚀 LinkedIn Automation Suite

**Automate your LinkedIn prospection process with intelligent employee connections and company following.**

This Python project automates LinkedIn prospection by:
- 👥 **Connecting with employees** from target companies
- 🏢 **Following company pages** automatically  
- 📊 **Managing prospects** in a local SQLite database
- 🤖 **Smart automation** with configurable delays and batch processing

---

## 🛠️ Setup Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Prepare and Load Your Data

#### **Configure Data Sources**
Before running the parser, update the file paths in `src/main_parse_files.py`:

1. **BuiltWith Data** (lines 17-20):
   ```python
   builtwith_dir = '/Users/YOUR_USERNAME/Builtwith'  # Update this path
   ```
   
2. **Mantiks Data** (line 42):
   ```python
   dir = '/Users/YOUR_USERNAME/Mantiks'  # Update this path
   ```

#### **Required File Structure**
The parser expects specific CSV files in each directory (examples bellow):

**BuiltWith Directory** (`/Users/YOUR_USERNAME/Builtwith/`):
- `React-websites-in-France.csv`
- `React-websites-in-Germany.csv`
- `React-websites-in-the-United-Kingdom.csv`

**Mantiks Directory** (`/Users/YOUR_USERNAME/Mantiks/`):
- `Développeur React Freelance Moins De 1000 Salarié.csv`
- `Node.Js - 6 mois à partir du 23_02_2025.csv`
- `Node.JS - Freelance Entreprise De Moins De 1000 Salariés.csv`
- `Node.JS - Télétravail Entreprise De Moins De 1000 Salariés.csv`
- `React - Entreprise de 1 à 10000 salariés sur 6 mois à partir du 13_02_2025.csv`
- `React Native - All TIME.csv`
- `React Native Freelance - Entreprise De Moins De 1000 Salariés.csv`
- `React Native Télétravail - Entreprise De Moins De 1000 Salariés.csv`
- `React Télétravail CDI Entreprise De Moins De 1000 Salariés En France.csv`

#### **Expected CSV Column Structure**

**BuiltWith CSV Format:**
- `Company` - Company name
- `Linkedin` - Company LinkedIn URL

**Mantiks CSV Format** - **3 Required Column Types** (exact column names vary by file):

1. **Company Name Column** (REQUIRED):
   - Possible names: `Company name`, `Nom de l'entreprise`
   - Contains the company/organization name
   - Example: "Acme Corp", "TechStart SAS"

2. **Company LinkedIn URL Column** (REQUIRED):
   - Possible names: `Company LinkedIn`, `LinkedIn Entreprise`
   - Contains the LinkedIn company page URL
   - Example: "https://linkedin.com/company/acme-corp"

3. **Employee LinkedIn URL Column** (OPTIONAL):
   - Possible names: `LinkedIn profil`, `Profile LinkedIn`, `Company LinkedIn Employees`
   - Contains individual employee LinkedIn profile URLs
   - Example: "https://linkedin.com/in/john-doe-123456"
   - **Note**: Use empty string `''` if your CSV file doesn't have employee profiles

**⚠️ Important Notes:**
- Column names are **case-insensitive** (parser converts to lowercase)
- All three column parameters are required in `MantiksCSVParser()`, but employee column can be empty string
- CSV files should be comma-separated (`,`)
- Missing or null values in company columns will be filtered out automatically

#### **How to Configure MantiksCSVParser for Your CSV Files**

To use `MantiksCSVParser` with your own CSV files, you need to identify the correct column names and update `src/main_parse_files.py`:

**Example Configuration:**
```python
# If your CSV has these columns: "Enterprise Name", "Company URL", "Employee Profiles"
mantiks_parser = MantiksCSVParser(
    file_path='your_file.csv',
    company_name_column='Enterprise Name',      # Column with company names
    company_link_column='Company URL',          # Column with company LinkedIn URLs
    employee_link_column='Employee Profiles'   # Column with employee LinkedIn URLs
)

# If your CSV only has company data (no employee profiles)
mantiks_parser = MantiksCSVParser(
    file_path='companies_only.csv',
    company_name_column='Company Name',
    company_link_column='LinkedIn URL',
    employee_link_column=''                     # Empty string for no employee data
)
```

**Step-by-step:**
1. Open your CSV file and identify the column headers
2. Find which column contains company names → use for `company_name_column`
3. Find which column contains company LinkedIn URLs → use for `company_link_column`
4. Find which column contains employee LinkedIn URLs → use for `employee_link_column` (or `''` if none)
5. Update the configuration in `load_mantiks_files()` function

**Current Examples in `main_parse_files.py`:**
```python
# Example configurations already in the code:
parsers_info = [
    # French column names, with employee profiles
    (file1, 'Company name', 'Company LinkedIn', 'LinkedIn profil', 'Description'),
    
    # French column names, NO employee profiles (empty string)
    (file2, 'Nom de l\'entreprise', 'LinkedIn Entreprise', '', 'Description'),
    
    # Different employee column name
    (file4, 'Company name', 'Company LinkedIn', 'Company LinkedIn Employees', 'Description'),
    
    # Another employee column variation
    (file5, 'Nom de l\'entreprise', 'LinkedIn Entreprise', 'Profile LinkedIn', 'Description'),
]
```

#### **Run the Data Parser**
```bash
python src/main_parse_files.py
```

**What this does:**
- ✅ Creates/updates `prospection_data.db` SQLite database
- 📊 Processes 3 BuiltWith files + 9 Mantiks files
- 🏢 Extracts company information and LinkedIn URLs
- 👥 Extracts employee LinkedIn profiles (from Mantiks data)
- 📝 Provides detailed logging of processing progress
- 🔄 Supports incremental updates (won't duplicate existing data)

**Expected Output:**
```
Processing Builtwith file: React-websites-in-France.csv
Found 1,245 companies in React-websites-in-France.csv
Adding company to DB: Acme Corp
...
Completed processing React-websites-in-France.csv
```

### Step 3: Install Chrome Extension (Recommended)
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" 
3. Click "Load unpacked" and select the `chrome_plugin/` folder
4. The extension will automatically handle LinkedIn interactions

### Step 4: Run Automation

#### Quick Start (with defaults):
```bash
python src/main_add_linkedin_companies_and_employees.py
```
*Defaults: 0 employees, 50 companies*

#### Custom Parameters:
```bash
# Connect with 20 employees and follow 30 companies
python src/main_add_linkedin_companies_and_employees.py --total-employees 20 --total-companies 30

# Short form
python src/main_add_linkedin_companies_and_employees.py -e 10 -c 25

# Full customization
python src/main_add_linkedin_companies_and_employees.py \
    --total-employees 15 \
    --total-companies 40 \
    --employees-per-batch 5 \
    --companies-per-batch 15 \
    --batch-delay 90
```

#### Command Line Options:
| Option | Short | Description | Default |
|--------|--------|-------------|---------|
| `--total-employees` | `-e` | Total employees to connect with | 0 |
| `--total-companies` | `-c` | Total companies to follow | 50 |
| `--employees-per-batch` | | Employees per batch | 5 |
| `--companies-per-batch` | | Companies per batch | 20 |
| `--batch-delay` | | Seconds between batches | 60 |

#### Help:
```bash
python src/main_add_linkedin_companies_and_employees.py --help
```

---

## ⚙️ Configuration Options

### 🎯 **Automation Parameters**

| Parameter | Description | Default | Recommended |
|-----------|-------------|---------|-------------|
| `total_employees` | Total employees to connect | 50 | 20-100 |
| `total_companies` | Total companies to follow | 100 | 50-200 |
| `nb_employees_per_batch` | Employees per batch | 5 | 3-8 |
| `nb_companies_per_batch` | Companies per batch | 10 | 5-15 |
| `avg_batch_delay` | Seconds between batches | 60 | 45-120 |

### 🕐 **Timing Features**
- **Random delays**: 1-3 seconds between each action
- **Batch delays**: Configurable pauses between batches
- **Smart progression**: Employees processed first, then companies

---

## 🔄 How It Works

### **Automated Workflow:**
```
1. 👥 Connect with X employees (with "Se connecter" button)
   ↓ (Random 1-3s delays between each)
2. 🏢 Follow Y companies (with "Suivre" button)  
   ↓ (Random 1-3s delays between each)
3. ⏱️ Wait ~60 seconds (batch delay)
4. 🔄 Repeat until totals reached
```

### **Chrome Extension Actions:**
- **Employee profiles**: Clicks "Se connecter" → Handles invitation modal → Clicks "Envoyer sans note"
- **Company profiles**: Clicks "Suivre" button
- **Auto-close**: Closes tabs after successful actions

---

## 📊 Monitoring & Management

### Check Progress:
```bash
python src/main_inspect_db.py
```
Shows detailed statistics about your prospection progress.

### Manual Mode Options:
```python
# Manual company following with validation
add_company_with_validation(8)

# Manual employee connections with validation  
add_employee_with_validation(8)

# Legacy automation (companies only)
auto_add_companies_with_batch_delay(10, 60, 5)
```

---

## 🛡️ Safety Features

- **Rate limiting**: Configurable delays prevent LinkedIn detection
- **Batch processing**: Spreads actions over time
- **Random timing**: Mimics human behavior
- **Progress tracking**: Resume from where you left off
- **Error handling**: Graceful failure management

---

## 🗂️ File Structure

```
prospection-main/
├── src/
│   ├── main_add_linkedin_companies_and_employees.py  # 🎯 Main automation script
│   ├── main_inspect_db.py                           # 📊 Database statistics
│   ├── main_parse_files.py                          # 📥 CSV data import
│   ├── db_prospection.py                            # 🗄️ Database operations
│   └── csv_parser.py                                # 📋 CSV parsing logic
├── chrome_plugin/                                   # 🔧 Browser automation
├── prospection_data.db                              # 🗃️ SQLite database
└── requirements.txt                                 # 📦 Dependencies
```

---

## ⚠️ Important Notes

- **Use Chrome browser** for best compatibility with the extension
- **French LinkedIn interface** currently supported (easily customizable)
- **Start small**: Test with 10-20 prospects before scaling up
- **Monitor LinkedIn limits**: Respect platform guidelines
- **Backup your data**: Keep copies of your prospect databases

---

## 🎨 Customization

### Modify Chrome Extension:
Edit `chrome_plugin/content.js` to:
- Support different languages
- Change button detection logic
- Adjust timing parameters

### Database Queries:
Use `src/db_prospection.py` to:
- Filter prospects by criteria
- Export data for analysis
- Custom reporting

---

## 🚨 Troubleshooting

**Extension not working?**
- Check if it's enabled in Chrome extensions
- Verify LinkedIn page is fully loaded
- Check console for error messages

**Database issues?**
- Run `python src/main_inspect_db.py` to check data
- Re-import CSV files if needed

**Rate limiting?**
- Increase `avg_batch_delay` parameter
- Reduce batch sizes
- Add longer random delays

---

**⚡ Happy prospecting! Remember to use responsibly and respect LinkedIn's terms of service.**
