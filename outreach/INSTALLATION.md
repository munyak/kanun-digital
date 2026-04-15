# Installation & Setup Guide

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- ~50 MB disk space for dependencies and database

## Step 1: Install Dependencies

```bash
cd /sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach
pip install -r requirements.txt
```

**What gets installed:**
- `requests` (2.31+) — HTTP requests with proper timeout/retry handling
- `beautifulsoup4` (4.12+) — HTML parsing for web scraping

**Install time:** ~30 seconds

## Step 2: Verify Installation

```bash
python test_system.py
```

**Expected output:**
```
Passed:  37
Failed:  0
======================================================================
[+] All tests passed! System is ready for use.
```

## Step 3: Try a Small Research Job

```bash
python run_research.py --type therapist --state CA --city "Los Angeles" --count 5
```

**Expected output:**
```
============================================================
RESEARCH COMPLETE
============================================================
Found: X candidates
Validated & added: Y new prospects
Total in database: Z
...
```

## Step 4: Generate Sample Emails

```bash
python prospect_engine.py
```

Prints 2 sample personalized emails (therapist + lawyer).

```bash
python email_templates.py
```

Prints all 3-email sequences and A/B test subject lines.

## Step 5: Review Sample Data

```bash
cat prospects.csv
```

Shows format of output CSV (columns: name, email, validation_score, etc.)

## Troubleshooting Installation

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install --upgrade requests beautifulsoup4
```

### "Connection timeout during test"
Normal if network is slow. Run `python test_system.py --quick` to skip network tests.

### "Permission denied" on Python files
```bash
chmod +x *.py
```

### "prospects.json not found"
Normal on first run. It will be created after first research job:
```bash
python run_research.py --type therapist --state CA --count 1
```

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows, macOS, Linux |
| Python | 3.7+ |
| Disk | ~50 MB (code + dependencies) |
| RAM | 100 MB (for typical operations) |
| Network | Internet required for web scraping |
| Rate Limiting | Built-in 1.5-sec delays between requests |

## Next Steps

1. **Quick start**: Read `QUICKSTART.md` (5 minutes)
2. **Full documentation**: Read `README.md` (detailed workflow and features)
3. **System overview**: Read `INDEX.md` (architecture and file index)
4. **Configuration**: Customize `config.py` for your target markets
5. **First research run**: `python run_research.py --type therapist --state CA --count 20`

## Optional Enhancements

### Gmail API Integration (for automatic email sending)
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Advanced Web Scraping (JavaScript rendering)
```bash
pip install selenium playwright
python -m playwright install
```

### Database Backup Automation
Already implemented in `config.py` (`CREATE_BACKUPS = True`)

### Email Scheduling (APScheduler)
```bash
pip install apscheduler
```

## System Locations

```
/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach/
├── prospect_engine.py          # Core data models
├── run_research.py             # Automated discovery
├── email_templates.py          # Email sequences
├── outreach_manager.py         # Batch operations
├── config.py                   # Configuration
├── test_system.py              # Test suite
├── requirements.txt            # Dependencies
├── sample_prospects.json       # Example data
├── README.md                   # Full documentation
├── QUICKSTART.md               # 5-minute setup
├── INDEX.md                    # System overview
├── INSTALLATION.md             # This file
└── prospects.json              # [Created after first run]
    prospects.csv               # [Created after first run]
```

## Getting Help

- **Installation issues**: Check OS-specific Python setup
- **Missing dependencies**: Run `pip install -r requirements.txt` again
- **Research not finding prospects**: Check if directories are accessible; try larger city
- **Email generation errors**: Ensure all Prospect fields are populated correctly
- **Test failures**: Run `python test_system.py` to diagnose

## Quick Commands Reference

```bash
# Installation
pip install -r requirements.txt
python test_system.py

# Research
python run_research.py --type therapist --state CA --count 20

# Email management
python outreach_manager.py --action generate --limit 10
python outreach_manager.py --action mark-sent --email prospect@email.com
python outreach_manager.py --action stats

# Documentation
less README.md
less QUICKSTART.md
less INDEX.md
```

---

**Installation complete!** Proceed to `QUICKSTART.md` for your first research run.
