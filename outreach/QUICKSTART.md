# KaNun Digital Prospect System — Quick Start Guide

Get up and running in 5 minutes.

## Installation

```bash
cd /sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach
pip install -r requirements.txt
```

## 1. Test the System (2 min)

### Generate sample emails (no research needed)
```bash
python prospect_engine.py
```
Prints sample personalized emails for therapists and lawyers.

### See the full email sequences
```bash
python email_templates.py
```
Prints all 3-email sequences (initial + 2 follow-ups) and A/B test subject lines.

## 2. Run a Small Research Job (2 min)

### Find 5 therapists in Los Angeles
```bash
python run_research.py --type therapist --state CA --city "Los Angeles" --count 5
```

**Output:**
```
============================================================
RESEARCH COMPLETE
============================================================
Found: 5 candidates
Validated & added: 3 new prospects
Total in database: 3
By status: {'pending': 3}
By validation score: {'3': 2, '4': 1}

Saved to: prospects.json
CSV export: prospects.csv
============================================================
```

## 3. Review Results (1 min)

### See what you found
```bash
cat prospects.csv
```

| name | title | practice_name | email | validation_score |
|------|-------|---------------|-------|-----------------|
| Dr. Sarah Thompson | LMFT | Family First Therapy | sarah@ff.com | 4 |
| Dr. John Smith | LCSW | Wellness Center | john@wellness.com | 3 |

## 4. Generate Outreach Emails (1 min)

### Generate initial emails for your new prospects
```bash
python outreach_manager.py --action generate --limit 3
```

**Output:**
```
======================================================================
OUTREACH BATCH: 3 emails ready to send
======================================================================

[1] TO: sarah@ff.com
    NAME: Dr. Sarah Thompson
    TYPE: therapist
    SUBJECT: Quick resource for your families: digital safety

Hi Sarah,

I noticed your work specializing in divorce, and thought you might find this useful.

Many families you work with struggle with the "tech side" of their issues...

[Would continue for all 3 prospects]
```

Copy and paste into your email client, or integrate with email API.

## 5. Track Your Outreach (30 sec)

### Mark an email as sent
```bash
python outreach_manager.py --action mark-sent --email sarah@ff.com
```

This prevents duplicate contacts and tracks outreach history.

## 6. See Overall Stats

```bash
python outreach_manager.py --action stats
```

**Output:**
```
======================================================================
PROSPECT DATABASE STATISTICS
======================================================================

Total prospects: 3

By outreach status:
  pending          2
  contacted        1

By validation score:
  Score 1:   0
  Score 2:   0
  Score 3:   1 █
  Score 4:   2 ██
  Score 5:   0

Pending outreach (top 10 by validation score):
  [1] Dr. Sarah Thompson        (4/5) - sarah@ff.com
  [2] Dr. John Smith            (3/5) - john@wellness.com
```

## 7. Schedule Follow-ups (Day 5 & 12)

Your initial email was sent on Day 1. Here's when to follow up:

### Day 5 follow-ups
```bash
python outreach_manager.py --action followup-schedule --days 5
```

### Day 12 follow-ups (breakup email)
```bash
python outreach_manager.py --action followup-schedule --days 12
```

---

## Production Workflow

Repeat weekly:

1. **Research new prospects**
   ```bash
   python run_research.py --type therapist --state CA --city "Los Angeles" --count 20
   python run_research.py --type lawyer --state CA --count 15
   ```

2. **Review `prospects.csv`** in Excel/Sheets
   - Check validation notes
   - Mark any to skip in `outreach_status` column
   - Save

3. **Generate batch emails**
   ```bash
   python outreach_manager.py --action generate --limit 10
   ```

4. **Send** (your email client or API)

5. **Mark as sent** in the database
   ```bash
   python outreach_manager.py --action mark-sent --email prospect@email.com
   ```

6. **Track responses** — update `outreach_status` in `prospects.json` to "responded" or "converted"

7. **Schedule follow-ups** on days 5 and 12

8. **Check stats anytime**
   ```bash
   python outreach_manager.py --action stats
   ```

---

## File Locations

- **Prospect data**: `prospects.json` (machine-readable), `prospects.csv` (for review)
- **Core system**: `prospect_engine.py` (data + validation), `email_templates.py` (sequences), `run_research.py` (search)
- **CLI tools**: `outreach_manager.py` (batch operations)
- **Docs**: `README.md` (full docs), `QUICKSTART.md` (this file)

---

## Next Steps

- **Production email sending**: Integrate `email_templates.EmailSequence` with Gmail API, SendGrid, or your email provider
- **Automated follow-ups**: Use APScheduler or Celery to schedule day-5 and day-12 emails automatically
- **CRM integration**: Export `prospects.csv` to Salesforce, HubSpot, or Pipedrive
- **Better directories**: Add LinkedIn scraping, state bar lookups, specialized mediator directories
- **Response tracking**: Add email open tracking, click tracking, reply detection

---

## Troubleshooting

### "No prospects found"
- Check directory availability (Psychology Today may block scraping)
- Try a larger city or state
- Manually review a prospect's website if validation seems wrong

### "validation_score too low (1/5)"
- Website may be unreachable (firewall, robots.txt)
- Contact info may be behind a contact form (not visible HTML)
- Manually add contact info to `prospects.json` if you verify it's valid

### "Duplicate contacts issue"
- Always mark emails as sent: `python outreach_manager.py --action mark-sent`
- Check `prospects.json` for duplicate entries (key is `"email: name"`)

---

## Questions?

Refer to `README.md` for full documentation on validation scoring, database structure, email personalization, and limitations.
