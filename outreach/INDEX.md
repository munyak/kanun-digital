# KaNun Digital Prospect Research System — Complete Index

Production-ready Python system for discovering, validating, and outreaching to family therapists, lawyers, and mediators.

## System Overview

```
DISCOVERY → VALIDATION → DATABASE → EMAIL GENERATION → OUTREACH TRACKING
```

1. **DISCOVERY**: Search Psychology Today, Avvo, and other directories
2. **VALIDATION**: Verify websites, extract contact info, score confidence (1-5)
3. **DATABASE**: Store prospects in JSON, export to CSV
4. **EMAIL GENERATION**: Create personalized 3-email sequences per prospect
5. **OUTREACH TRACKING**: Log interactions, prevent duplicates, schedule follow-ups

---

## Files & Modules

### Core Modules

| File | Purpose | Key Classes/Functions |
|------|---------|---|
| **prospect_engine.py** (18 KB) | Data models, database management, validation scoring | `Prospect`, `ProspectDatabase`, `EmailGenerator`, `ValidationScorer` |
| **run_research.py** (17 KB) | Automated prospect discovery from directories | `ProspectSearcher.search_psychology_today()`, `.search_avvo_lawyers()` |
| **email_templates.py** (11 KB) | Multi-touch email sequence builder | `EmailSequence`, `SequenceManager`, subject line variations |
| **outreach_manager.py** (11 KB) | Batch operations: generate emails, mark sent, schedule follow-ups | `OutreachManager` CLI commands |

### Configuration & Testing

| File | Purpose |
|------|---------|
| **config.py** (8 KB) | Centralized settings: directories, validation rules, targets |
| **test_system.py** (18 KB) | Full test suite (37 tests, validates all components) |
| **requirements.txt** | Python dependencies: `requests`, `beautifulsoup4` |

### Documentation

| File | Audience | Content |
|------|----------|---------|
| **README.md** (13 KB) | Full system documentation | Architecture, validation scoring, workflow, limitations |
| **QUICKSTART.md** (6 KB) | First-time users | 5-minute setup and usage walkthrough |
| **INDEX.md** | This file | System overview and file index |

### Sample Data

| File | Purpose |
|------|---------|
| **sample_prospects.json** | 6 example prospect records (shows data structure) |

---

## Quick Reference: Command Line Usage

### Research & Discovery

```bash
# Search for 20 therapists in Los Angeles
python run_research.py --type therapist --state CA --city "Los Angeles" --count 20

# Search for 15 family law attorneys in New York
python run_research.py --type lawyer --state NY --count 15

# Search for 10 family mediators in Texas
python run_research.py --type mediator --state TX --count 10
```

### Email & Outreach Management

```bash
# Generate 5 initial outreach emails
python outreach_manager.py --action generate --limit 5

# Mark an email as sent
python outreach_manager.py --action mark-sent --email prospect@email.com

# Get prospects due for 5-day follow-up
python outreach_manager.py --action followup-schedule --days 5

# Print database statistics
python outreach_manager.py --action stats

# Audit low-scoring prospects
python outreach_manager.py --action audit

# Export to CSV
python outreach_manager.py --action export --output my_prospects.csv
```

### Testing & Validation

```bash
# Run full test suite
python test_system.py

# Test without network operations
python test_system.py --quick

# Show email templates and sequences
python email_templates.py

# Show sample generated emails
python prospect_engine.py
```

---

## Data Structures

### Prospect Record

```python
Prospect(
    name="Dr. Sarah Thompson",
    title="LMFT",
    practice_name="Family First Therapy",
    email="sarah@familyfirst.com",
    phone="555-123-4567",
    website="https://familyfirst.com",
    directory_url="https://psychologytoday.com/us/therapists/sarah-thompson",
    specialties=["divorce", "family therapy", "children"],
    state="CA",
    city="Los Angeles",
    validation_score=4,  # 1-5 scale
    validation_notes="Website live; email + phone verified; content recent",
    outreach_status="pending",  # pending, contacted, responded, converted
    date_added="2026-04-15T10:30:00",
    outreach_history=[
        {
            "event": "email_sent",
            "template": "therapist_initial_variant1",
            "timestamp": "2026-04-16T09:00:00"
        }
    ]
)
```

### Email Sequence Format

Each prospect gets a 3-email sequence:
- **Day 1**: Initial outreach (variant 1 or 2 for A/B testing)
- **Day 5**: Follow-up reminder
- **Day 12**: Final/"breakup" email

Subject lines are customized per prospect type (therapist, lawyer, mediator).

### Database Files

**prospects.json** (machine-readable):
- Key: `"email: Name"`
- Value: Full prospect record
- Used for: Programmatic access, deduplication, outreach tracking

**prospects.csv** (human-readable):
- Columns: name, title, practice_name, email, phone, website, specialties, state, city, validation_score, validation_notes, outreach_status, date_added
- Sorted: validation_score (descending), then date_added
- Used for: Manual review, CRM import, spreadsheet analysis

---

## Validation Scoring (1-5 Scale)

| Score | Confidence | Typical Criteria |
|-------|-----------|---|
| **5** | Very High | Website live (200), email + phone verified, recent content, 2+ directories |
| **4** | High | Website live, 1 contact method verified, recent content |
| **3** | Moderate | Website accessible, some contact info, content age uncertain |
| **2** | Low | Website redirects/unclear, limited contact info |
| **1** | Very Low | Contact info missing or website unreachable |

**Default minimum for outreach: score ≥ 2** (configurable in `config.py`)

---

## Email Personalization

### For Therapists
- **Position**: KaNun handles the "tech safety" part; therapist focuses on emotional/relational work
- **Value prop**: Families dealing with divorce/custody/tech addiction need digital audits and parental control setup
- **Social proof**: "Bren C., LMFT, refers families to us"
- **CTA**: "Would a 15-min call make sense?"

### For Lawyers
- **Position**: Forensic-grade digital safety expert for family law practice
- **Value prop**: Help clients with digital evidence preservation, co-parenting tech, device security during custody disputes
- **Expertise**: 21-year enterprise security veteran
- **CTA**: "Would a 15-min call make sense to explore if this is useful?"

### For Mediators
- **Position**: Value-add for mediation practices
- **Value prop**: Helps families navigate device/privacy issues during mediation
- **Outcome**: Smoother mediations, more confident families
- **CTA**: "Could we talk for 15 minutes?"

---

## Workflow: Weekly Outreach Cycle

### Monday: Research
```bash
python run_research.py --type therapist --state CA --city "Los Angeles" --count 20
python run_research.py --type lawyer --state CA --count 15
```
Produces: `prospects.json` + `prospects.csv`

### Tuesday: Review
Open `prospects.csv` in Excel/Sheets:
- Filter by validation_score ≥ 3
- Manually review specialties & focus
- Mark any to skip in `outreach_status` column
- Save

### Wednesday: Generate & Send
```bash
python outreach_manager.py --action generate --limit 10
```
Copy/paste emails into your email client (or integrate with Gmail API).

### Thursday–Friday: Track
```bash
python outreach_manager.py --action mark-sent --email prospect1@email.com
python outreach_manager.py --action mark-sent --email prospect2@email.com
```

### Next Week (Day 5 & 12)
```bash
python outreach_manager.py --action followup-schedule --days 5
python outreach_manager.py --action followup-schedule --days 12
```

---

## Key Configuration Settings

Edit `config.py` to customize:

| Setting | Default | Purpose |
|---------|---------|---------|
| `PSYCHOLOGY_TODAY_ENABLED` | True | Search Psychology Today directory |
| `AVVO_ENABLED` | True | Search Avvo lawyer directory |
| `MIN_VALIDATION_SCORE` | 2 | Minimum score to add to outreach |
| `REQUEST_DELAY` | 1.5 sec | Rate limiting between requests |
| `TARGET_STATES` | CA, NY, TX, FL, IL | States to focus on |
| `USE_AB_TESTING` | True | Enable subject line A/B variants |
| `DEFAULT_SUBJECT_VARIANT` | 1 | Which subject variant to use (1 or 2) |

---

## Testing & Quality Assurance

Run tests to validate the entire system:

```bash
# All tests
python test_system.py
# Expected: 37 passed, 0 failed

# Quick tests (skip network)
python test_system.py --quick

# Individual module tests
python prospect_engine.py       # Sample emails
python email_templates.py       # Sequences & subject lines
```

---

## Known Limitations

1. **Web Scraping Challenges**
   - Psychology Today uses JavaScript rendering → Selenium/Playwright may be needed
   - Avvo has paywalls and anti-bot measures
   - **Workaround**: Use APIs where available or hand-curate top results

2. **Contact Info Extraction**
   - Regex-based extraction misses contact forms (no visible email)
   - **Workaround**: Manually add contact info for valuable prospects with score ≥ 3

3. **No Built-in Email Sending**
   - System generates emails but doesn't send them
   - **Next step**: Integrate Gmail API, SendGrid, or Mailgun

4. **No Mediator Directory**
   - Psychology Today search can find mediators, but results are mixed
   - **Recommendation**: Use Google search + manual curation

5. **No Phone Validation**
   - Extracted phone numbers aren't verified
   - **Note**: Email is preferred contact method

---

## Future Enhancements

- [ ] Email sending API integration (Gmail, SendGrid)
- [ ] Automated follow-up scheduling (APScheduler)
- [ ] LinkedIn profile validation
- [ ] Phone number validation (Twilio)
- [ ] CRM sync (Salesforce, HubSpot, Pipedrive)
- [ ] Response tracking (open rates, click tracking)
- [ ] Unsubscribe list management
- [ ] Multivariate testing dashboard
- [ ] State bar scraping (attorneys)
- [ ] Mediator directory integration

---

## Project Statistics

| Metric | Value |
|--------|-------|
| **Total Lines of Code** | ~2,000 |
| **Modules** | 4 (prospect_engine, run_research, email_templates, outreach_manager) |
| **Test Coverage** | 37 automated tests |
| **Documentation** | 3 guides (README, QUICKSTART, INDEX) + inline docstrings |
| **Dependencies** | 2 (requests, beautifulsoup4) |
| **Python Version** | 3.7+ |

---

## Getting Started Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run tests: `python test_system.py`
- [ ] Try email generation: `python prospect_engine.py`
- [ ] See sample data: `cat sample_prospects.json`
- [ ] Run small research job: `python run_research.py --type therapist --state CA --city "Los Angeles" --count 5`
- [ ] Review results: `cat prospects.csv`
- [ ] Generate outreach emails: `python outreach_manager.py --action generate --limit 3`
- [ ] Mark one as sent: `python outreach_manager.py --action mark-sent --email <email>`
- [ ] Check stats: `python outreach_manager.py --action stats`
- [ ] Read full docs: `README.md`

---

## Support & Troubleshooting

**"No prospects found"**
→ Check if directories are reachable; try larger city or broader state search

**"Validation score too low"**
→ Website may be behind firewall; check validation_notes; manually verify and update

**"Duplicate contact issue"**
→ Always mark emails sent: `--action mark-sent`; check prospects.json for duplicate keys

**Email template syntax error**
→ Ensure all Prospect records have required fields: name, title, practice_name, email or phone

---

## File Locations

All files located in:
```
/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach/
```

Output files:
- `prospects.json` — Main prospect database
- `prospects.csv` — Human-readable export
- `research.log` — Scraping logs (if enabled)

---

## Contact & Questions

For system improvements, bug reports, or feature requests, refer to README.md for detailed documentation on each component.

---

**Last Updated**: April 15, 2026
**Version**: 1.0.0
**Status**: Production-Ready
