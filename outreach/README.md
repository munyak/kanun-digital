# KaNun Digital Prospect Research & Outreach System

A production-ready system for finding, validating, and reaching out to family therapists, lawyers, and mediators as potential referral partners or clients for KaNun Digital's family digital privacy and security services.

## Problem This Solves

Previous prospect research efforts yielded 5 therapy practice leads, all of which turned out to be inactive or unreachable—wasting outreach effort. **The root cause: no validation step.** This system validates that prospects are active before adding them to any outreach queue.

## System Components

### 1. **prospect_engine.py** — Core Data Models & Validation

**Classes:**
- `Prospect`: Data model for a prospect record (name, contact info, specialties, validation score, outreach status, history)
- `ProspectDatabase`: Loads/saves prospect data (JSON), exports to CSV, prevents duplicate contacts
- `EmailGenerator`: Generates personalized cold outreach emails for therapists, lawyers, and mediators (A/B testable)
- `ValidationScorer`: Scores prospects 1–5 on validation confidence

**Prospect Data Structure:**
```json
{
  "email: Dr. Sarah Thompson": {
    "name": "Dr. Sarah Thompson",
    "title": "LMFT",
    "practice_name": "Family First Therapy",
    "email": "sarah@familyfirst.com",
    "phone": "555-123-4567",
    "website": "https://familyfirst.com",
    "directory_url": "https://psychologytoday.com/us/therapists/sarah-thompson",
    "specialties": ["divorce", "child therapy"],
    "state": "CA",
    "city": "Los Angeles",
    "validation_score": 4,
    "validation_notes": "Website live; email + phone verified; content recent",
    "outreach_status": "pending",
    "date_added": "2026-04-15T12:34:56.789012",
    "outreach_history": [
      {
        "event": "email_sent",
        "template": "therapist_initial_variant1",
        "timestamp": "2026-04-16T09:00:00"
      }
    ]
  }
}
```

### 2. **run_research.py** — Automated Prospect Search & Validation

Command-line tool that searches multiple directories, validates each prospect, and adds validated results to the database.

**Supported Sources:**
- Psychology Today therapist directory (LMFT, LCSW, psychologists)
- Avvo lawyer directory (family law attorneys)
- Google search patterns (requires manual curation or Google Custom Search API)

**Usage:**

```bash
# Search for 20 therapists in Los Angeles, CA
python run_research.py --type therapist --state CA --city "Los Angeles" --count 20

# Search for 15 family law attorneys in New York
python run_research.py --type lawyer --state NY --count 15

# Search for family mediators (directory TBD)
python run_research.py --type mediator --state TX --city Austin

# Custom database path
python run_research.py --type therapist --state CA --count 10 \
  --db /path/to/prospects.json
```

**What It Does:**

1. **Discovers** candidates from directory sources (Psychology Today, Avvo, etc.)
2. **Validates** each candidate:
   - Pings website to confirm it's live (200 OK, not a parking page)
   - Extracts contact info (email, phone) using regex
   - Scores validation confidence 1–5
3. **Deduplicates** — doesn't re-add prospects already in database
4. **Exports** results to `prospects.json` (machine-readable) and `prospects.csv` (for manual review/CRM import)

**Output Example:**
```
============================================================
RESEARCH COMPLETE
============================================================
Found: 47 candidates
Validated & added: 23 new prospects
Total in database: 87
By status: {'pending': 74, 'contacted': 13, 'responded': 0, 'converted': 0}
By validation score: {'1': 2, '2': 14, '3': 31, '4': 35, '5': 5}

Saved to: /path/to/prospects.json
CSV export: /path/to/prospects.csv
============================================================
```

### 3. **email_templates.py** — Personalized Outreach Sequences

Generates 3-email sequences (initial + 2 follow-ups) customized per prospect type.

**Classes:**
- `EmailSequence`: Builds and manages a multi-touch sequence for one prospect
- `SequenceManager`: Manages sequences across multiple prospects
- Helper functions for subject line A/B testing

**Sequence Structure (for all prospect types):**
- **Day 1**: Initial outreach (with 2 subject line variants for A/B testing)
- **Day 5**: Follow-up 1 (friendly reminder)
- **Day 12**: Follow-up 2 / "Breakup email" (final attempt, sets expectation)

**Email Tone:**
- **Therapists**: Position KaNun as a resource handling the "tech safety" part so they focus on emotional/relational work. Mention Bren C., LMFT, as a peer referral.
- **Lawyers**: Position KaNun as a forensic-grade digital safety expert for custody cases. Emphasize digital evidence preservation, co-parenting app setup, device audits.
- **Mediators**: Position KaNun as a value-add for mediations—helps families navigate device/privacy issues.

**Usage:**
```python
from prospect_engine import Prospect
from email_templates import EmailSequence

prospect = Prospect(
    name="Dr. Sarah Thompson",
    title="LMFT",
    email="sarah@familyfirst.com",
    ...
)

# Generate full 3-email sequence
sequence = EmailSequence(prospect, "therapist")

# Get initial email
initial = sequence.get_email_for_phase(EmailSequencePhase.INITIAL)
print(initial['subject'])
print(initial['body'])

# Or get all emails
for email in sequence.get_all_emails():
    print(f"Day {email['day']}: {email['subject']}")
```

**CLI (for review/testing):**
```bash
python email_templates.py
# Prints all sequences and subject line variations for review
```

## Validation Scoring (1–5)

Each prospect receives a validation confidence score:

| Score | Meaning | Typical Profile |
|-------|---------|---|
| **5** | Highly confident they're active | Website live (200), email + phone verified, content recent, listed in 2+ directories |
| **4** | Very likely active | Website live, 1 contact method verified, content recent |
| **3** | Probably active | Website accessible, some contact method found, content age uncertain |
| **2** | Possibly active | Website redirects or status unclear, limited contact info |
| **1** | Questionable | Contact info missing or website unreachable |

**Default threshold for outreach: score ≥ 2** (configurable in code)

**Validation checks:**
- Website status: HTTP 200 (live), 301/302 (redirects), or unreachable
- Contact info: Email and/or phone extracted from website
- Directory sources: Number of professional directories confirming they're active
- Content recency: Recent updates suggest active practice

## Database Files

### prospects.json
Machine-readable JSON database, keyed by `"email: Name"`.

**Use cases:**
- Programmatic prospect lookup
- Merging multiple research runs
- Tracking outreach history

**Example:**
```json
{
  "sarah@familyfirst.com: Dr. Sarah Thompson": {
    "name": "Dr. Sarah Thompson",
    "validation_score": 4,
    "outreach_status": "pending",
    ...
  }
}
```

### prospects.csv
Human-readable CSV for manual review, CRM import, spreadsheet analysis.

**Columns:**
- name, title, practice_name
- email, phone, website
- specialties (semicolon-separated)
- state, city
- validation_score, validation_notes
- outreach_status, date_added

**Sorted by:** validation_score (descending), then date_added

**Use cases:**
- Import into Salesforce, HubSpot, or other CRM
- Manual review before outreach
- Analytics (which states/specialties have best prospects)

## Outreach Workflow

### Step 1: Research
```bash
python run_research.py --type therapist --state CA --count 30
```
Finds and validates prospects, saves to `prospects.json` and `prospects.csv`.

### Step 2: Review
Open `prospects.csv` in Excel or Google Sheets.
- Check validation notes
- Filter by score ≥ 3 (or your threshold)
- Identify prospects to skip (competitors, "not accepting clients", etc.)
- Optionally edit outreach_status to "skip" for non-prospects

### Step 3: Generate Outreach Emails
```python
from prospect_engine import ProspectDatabase, EmailGenerator
from email_templates import EmailSequence

db = ProspectDatabase('prospects.json')
pending = db.get_pending_prospects(limit=10)

for prospect in pending:
    seq = EmailSequence(prospect, "therapist")
    initial_email = seq.get_email_for_phase(EmailSequencePhase.INITIAL)
    
    print(f"To: {prospect.email}")
    print(f"Subject: {initial_email['subject']}")
    print(initial_email['body'])
    print("---")
```

### Step 4: Track Outreach
After sending an email, mark the prospect as contacted:
```python
db.mark_contacted(prospect, email_template_id='therapist_initial_variant1')
db.save()
```

This prevents accidental duplicate emails and maintains outreach history.

### Step 5: Schedule Follow-ups
Day 5 and Day 12 emails are pre-generated and ready. Use your email tool's scheduler or set a reminder:
```python
next_phase, send_date = sequence.get_next_email_date(prospect.date_added)
print(f"Send {next_phase.value} on {send_date}")
```

## Key Assumptions & Limitations

### Strengths
- **Multiple validation checks**: Website status + contact info extraction prevents wasted outreach
- **Deduplication**: Database prevents emailing the same prospect twice
- **Structured data**: JSON + CSV exports work with any CRM
- **Personalization**: Emails reference prospect specialties and practice focus
- **A/B testing**: Multiple subject line variants for initial emails
- **Rate limiting**: Respects server load with delays between requests

### Limitations
- **Web scraping complexity**: Directory websites use JavaScript, paywalls, and anti-bot measures. Scraping may require:
  - Selenium or Playwright for JS-rendered sites
  - Headless browser for captchas
  - API access (Psychology Today has no public API; Avvo is harder to scrape)
  - **Recommendation**: Hand-curate top directories + use Psychology Today search API if available
- **Contact info extraction**: Regex-based email/phone extraction misses:
  - Contact forms (no visible email)
  - Contact info behind paywalls
  - **Workaround**: Manually review low-validation prospects and add contact info
- **Google search**: Direct Google scraping is rate-limited and blocked. **Recommendation**: Use Google Custom Search API or manual search
- **No phone number verification**: Phone numbers are extracted but not validated
- **Mediators**: No dedicated directory exists. **Recommendation**: Use Psychology Today search + manual curation

## Getting Started

### Installation
```bash
cd /path/to/outreach
pip install -r requirements.txt
```

### Quick Start (Manual Testing)

1. **Test the email generator:**
   ```bash
   python prospect_engine.py
   ```
   Prints sample emails for therapists and lawyers.

2. **Test the email sequences:**
   ```bash
   python email_templates.py
   ```
   Prints all 3-email sequences and subject line variations.

3. **Run a small research job:**
   ```bash
   python run_research.py --type therapist --state CA --city "Los Angeles" --count 5
   ```
   Finds 5 therapists in LA, validates them, saves results.

4. **Review results:**
   ```bash
   cat prospects.csv
   ```

### Production Workflow

1. **Decide your target market** (states, cities, prospect types)
2. **Run research** for each target:
   ```bash
   python run_research.py --type therapist --state CA --count 30
   python run_research.py --type lawyer --state CA --count 20
   ```
3. **Review & filter** in `prospects.csv`
4. **Generate and send** initial emails (batch or manually)
5. **Track responses** and mark status as "responded" or "converted"
6. **Schedule follow-ups** for days 5 and 12
7. **Iterate**: Add more prospects weekly

## Future Improvements

- [ ] Email sending integration (Gmail API, SendGrid, etc.)
- [ ] Automated follow-up scheduling (APScheduler, Celery)
- [ ] LinkedIn profile scraping for additional validation
- [ ] Phone number validation (TwilioAPI)
- [ ] CRM integration (Salesforce, HubSpot APIs)
- [ ] Response tracking (open rates, click tracking via pixel emails)
- [ ] Unsubscribe list management
- [ ] Multivariate subject line testing dashboard
- [ ] Conversion rate tracking by state/city/specialty
- [ ] Mediator directory integration (when data source identified)

## Code Quality

- **Docstrings**: All functions and classes documented with purpose, args, returns
- **Type hints**: Full type annotations for clarity
- **Error handling**: Graceful handling of network timeouts, 404s, parsing failures
- **Logging**: Clear console output for debugging
- **Modular design**: Each concern separated (discovery, validation, email, database)

## Support

For questions or bugs:
1. Check `validation_notes` on prospects with low scores
2. Review `outreach_history` to see what's been tried
3. Manually inspect a prospect's website if validation failed unexpectedly
