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

### Step 2: Load Your Data
Parse your CSV files from Mantiks and BuiltWith:
```bash
python src/main_parse_files.py
```
This creates a local SQLite database (`prospection_data.db`) with all your prospects.

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
