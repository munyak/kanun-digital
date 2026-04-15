"""
KaNun Digital Prospect Research Engine

Manages discovery, validation, and outreach tracking for therapy practice prospects,
family law attorneys, and family mediators.

Core features:
- Load/save prospect database (JSON)
- Validate prospect contact info and website status
- Generate personalized outreach emails
- Track outreach history to prevent duplicate contacts
"""

import json
import csv
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field


@dataclass
class Prospect:
    """Represents a validated prospect for KaNun Digital outreach."""

    name: str
    title: str  # LMFT, JD, etc.
    practice_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    directory_url: Optional[str] = None
    specialties: List[str] = field(default_factory=list)
    state: str = ""
    city: str = ""
    validation_score: int = 0  # 1-5, higher is better
    validation_notes: str = ""
    outreach_status: str = "pending"  # pending, contacted, responded, converted
    date_added: str = ""
    outreach_history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary, formatting outreach_history safely."""
        d = asdict(self)
        d['date_added'] = d['date_added'] or datetime.now().isoformat()
        return d

    def validate_basic_fields(self) -> Tuple[bool, str]:
        """
        Check if prospect has minimum required fields for outreach.
        Returns (is_valid, reason).
        """
        if not self.name:
            return False, "Missing name"
        if not (self.email or self.phone):
            return False, "Missing both email and phone"
        if self.validation_score < 2:
            return False, f"Validation score too low: {self.validation_score}"
        return True, "OK"


class ProspectDatabase:
    """
    Manages loading, saving, and querying the prospect database.

    Stores prospects in JSON for easy merging and deduplication.
    Exports to CSV for CRM import and manual review.
    """

    def __init__(self, db_path: str):
        """Initialize database at the given JSON file path."""
        self.db_path = db_path
        self.prospects: Dict[str, Prospect] = {}
        self.csv_path = db_path.replace('.json', '.csv')
        self.load()

    def load(self) -> None:
        """Load prospects from JSON file. Creates empty DB if file doesn't exist."""
        if not os.path.exists(self.db_path):
            self.prospects = {}
            return

        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                # Normalize: if it's a list, convert to dict keyed by email+name
                if isinstance(data, list):
                    self.prospects = {
                        f"{p.get('email', p.get('phone', p.get('name')))}: "
                        f"{p.get('name')}": Prospect(**p)
                        for p in data
                    }
                else:
                    self.prospects = {
                        k: Prospect(**v) for k, v in data.items()
                    }
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Could not load {self.db_path}: {e}. Starting fresh.")
            self.prospects = {}

    def save(self) -> None:
        """Save all prospects to JSON and CSV."""
        # JSON: keyed dictionary
        with open(self.db_path, 'w') as f:
            data = {
                f"{p.email or p.phone}: {p.name}": p.to_dict()
                for p in self.prospects.values()
            }
            json.dump(data, f, indent=2, default=str)

        # CSV: for import/review
        if self.prospects:
            with open(self.csv_path, 'w', newline='') as f:
                fieldnames = [
                    'name', 'title', 'practice_name', 'email', 'phone',
                    'website', 'specialties', 'state', 'city',
                    'validation_score', 'validation_notes', 'outreach_status',
                    'date_added'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for p in sorted(
                    self.prospects.values(),
                    key=lambda x: (-x.validation_score, x.date_added)
                ):
                    row = asdict(p)
                    row['specialties'] = '; '.join(row['specialties'])
                    row = {k: row.get(k, '') for k in fieldnames}
                    writer.writerow(row)

    def add_or_update(self, prospect: Prospect) -> bool:
        """
        Add or update a prospect. Returns True if new, False if updated.
        Uses email+name as unique key.
        """
        key = f"{prospect.email or prospect.phone}: {prospect.name}"
        is_new = key not in self.prospects

        if not is_new:
            # Merge: keep existing outreach history if updating
            existing = self.prospects[key]
            if not prospect.outreach_history:
                prospect.outreach_history = existing.outreach_history
            if not prospect.date_added:
                prospect.date_added = existing.date_added
            if prospect.outreach_status == "pending":
                prospect.outreach_status = existing.outreach_status

        if not prospect.date_added:
            prospect.date_added = datetime.now().isoformat()

        self.prospects[key] = prospect
        return is_new

    def get_pending_prospects(self, limit: Optional[int] = None) -> List[Prospect]:
        """Return prospects with 'pending' outreach status, sorted by validation score."""
        pending = [
            p for p in self.prospects.values()
            if p.outreach_status == "pending"
        ]
        pending.sort(key=lambda x: -x.validation_score)
        return pending[:limit] if limit else pending

    def mark_contacted(self, prospect: Prospect, email_template_id: str) -> None:
        """Mark a prospect as contacted and log the event."""
        if prospect.outreach_status == "pending":
            prospect.outreach_status = "contacted"

        prospect.outreach_history.append({
            'event': 'email_sent',
            'template': email_template_id,
            'timestamp': datetime.now().isoformat(),
        })

    def get_stats(self) -> Dict:
        """Return database statistics."""
        statuses = {}
        scores = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}

        for p in self.prospects.values():
            status = p.outreach_status
            statuses[status] = statuses.get(status, 0) + 1
            scores[str(p.validation_score)] += 1

        return {
            'total': len(self.prospects),
            'by_status': statuses,
            'by_validation_score': scores,
        }


class EmailGenerator:
    """
    Generates personalized outreach emails for different prospect types.
    Supports A/B testing with subject line variations.
    """

    # Company context
    COMPANY = "KaNun Digital"
    FOUNDER = "Bren C."
    FOUNDER_CRED = "21-year enterprise security veteran"
    COMPANY_FOCUS = "family digital privacy and security"

    @staticmethod
    def therapist_initial(prospect: Prospect, variant: int = 1) -> Tuple[str, str]:
        """
        Generate initial outreach email for a therapist.

        Args:
            prospect: The prospect record
            variant: Subject line variant (1 or 2 for A/B testing)

        Returns:
            Tuple of (subject, body)
        """
        # A/B test subject lines
        subjects = {
            1: f"Quick resource for your families: digital safety",
            2: f"Thought of you: expert on the 'tech part' of family issues",
        }
        subject = subjects.get(variant, subjects[1])

        # Extract specialty for personalization
        specialty_mention = ""
        if prospect.specialties:
            spec = prospect.specialties[0].lower()
            if 'divorce' in spec or 'custody' in spec:
                specialty_mention = f" working with families through {spec}"
            elif 'child' in spec or 'adolescent' in spec:
                specialty_mention = f" specializing in {spec}"
            else:
                specialty_mention = f" focused on {spec}"

        body = f"""Hi {prospect.name.split()[0]},

I noticed your work{specialty_mention}, and thought you might find this useful.

Many families you work with struggle with the "tech side" of their issues — device monitoring during custody disputes, setting up parental controls that actually work, recovering from tech addiction. We help with exactly that.

I'm {EmailGenerator.FOUNDER}, a {EmailGenerator.FOUNDER_CRED}. We handle the digital security and privacy audits so you can focus on the emotional and relational work. I've got a peer, {EmailGenerator.FOUNDER}, an LMFT, who refers families to us and says it takes a huge weight off her plate.

Would a 15-min call make sense to see if there's a fit? Happy to chat on your schedule.

Best,
{EmailGenerator.FOUNDER}
{EmailGenerator.COMPANY}"""

        return subject, body

    @staticmethod
    def therapist_followup1(prospect: Prospect) -> Tuple[str, str]:
        """5-day follow-up for therapist."""
        subject = f"Re: digital safety resource for your families"

        name_first = prospect.name.split()[0]
        body = f"""Hi {name_first},

Following up on my note from last week — wanted to make sure it didn't slip through.

The reason I'm reaching out is simple: families dealing with custody or tech issues often have digital security gaps that impact their kids. We see it all the time. You handle the relationship piece; we handle the tech piece.

Would you have 15 minutes next week for a quick call?

Thanks,
{EmailGenerator.FOUNDER}"""

        return subject, body

    @staticmethod
    def therapist_followup2(prospect: Prospect) -> Tuple[str, str]:
        """12-day follow-up (breakup email) for therapist."""
        subject = f"Last note: {EmailGenerator.COMPANY} + therapists"

        name_first = prospect.name.split()[0]
        body = f"""Hi {name_first},

This is my last note — just wanted to be direct.

We work best with therapists who are actively looking for ways to improve outcomes for families dealing with divorce, custody, or tech issues. If that's you, let's talk. If not, no worries.

Either way, my door is open if you ever want to explore this.

Best,
{EmailGenerator.FOUNDER}"""

        return subject, body

    @staticmethod
    def lawyer_initial(prospect: Prospect, variant: int = 1) -> Tuple[str, str]:
        """
        Generate initial outreach email for a family law attorney.

        Args:
            prospect: The prospect record
            variant: Subject line variant (1 or 2)

        Returns:
            Tuple of (subject, body)
        """
        subjects = {
            1: "Expert resource for your custody/divorce cases: digital evidence & device security",
            2: "Forensic-grade digital safety advisor for your family law clients",
        }
        subject = subjects.get(variant, subjects[1])

        body = f"""Hi {prospect.name.split()[0]},

I help family law attorneys advise their clients on digital evidence, co-parenting tech, and device security during custody disputes.

Here's what comes up constantly:
- Preserving digital evidence properly (so it's admissible)
- Setting up secure co-parenting communication tools
- Auditing devices for hidden monitoring or security gaps
- Advising on child device setup post-custody handoff

I'm {EmailGenerator.FOUNDER}, a {EmailGenerator.FOUNDER_CRED}. We've worked with a few attorneys in your state who now refer clients for the "tech due diligence" part of their cases — lets you focus on the legal strategy.

Would a 15-minute call work to explore if this is useful for your practice?

Best,
{EmailGenerator.FOUNDER}
{EmailGenerator.COMPANY}"""

        return subject, body

    @staticmethod
    def lawyer_followup1(prospect: Prospect) -> Tuple[str, str]:
        """5-day follow-up for attorney."""
        subject = "Re: digital evidence & device security resource"

        name_first = prospect.name.split()[0]
        body = f"""Hi {name_first},

Following up on my note from last week.

The thing is: most family law attorneys don't have an expert on the digital side. We fill that gap. Your clients get better advice. You close faster. Everyone wins.

Would you have 15 minutes to talk?

Thanks,
{EmailGenerator.FOUNDER}"""

        return subject, body

    @staticmethod
    def lawyer_followup2(prospect: Prospect) -> Tuple[str, str]:
        """12-day follow-up (breakup) for attorney."""
        subject = "Last message: {EmailGenerator.COMPANY} for family law practices"

        name_first = prospect.name.split()[0]
        body = f"""Hi {name_first},

Final note from me.

If you're interested in having a forensic-grade digital security expert on your team (for referral or collaboration), let's talk. If not, all good.

Door's open.

{EmailGenerator.FOUNDER}"""

        return subject, body

    @staticmethod
    def mediator_initial(prospect: Prospect, variant: int = 1) -> Tuple[str, str]:
        """Initial outreach for family mediators."""
        subjects = {
            1: "Digital safety resource for families in mediation",
            2: "Help your families navigate device & privacy issues during mediation",
        }
        subject = subjects.get(variant, subjects[1])

        body = f"""Hi {prospect.name.split()[0]},

Many families you mediate have digital safety gaps — shared devices, custody app setup, tech concerns.

We handle the digital side of family transitions. Handles device audits, co-parenting tech setup, digital privacy. Takes a load off you and gives families clarity.

I'm {EmailGenerator.FOUNDER}, {EmailGenerator.FOUNDER_CRED}, and we work with mediators to provide this as a value-add.

Could we talk for 15 minutes?

Best,
{EmailGenerator.FOUNDER}
{EmailGenerator.COMPANY}"""

        return subject, body


class ValidationScorer:
    """
    Scores prospects on validation confidence (1-5).

    Considers: website status, contact info, recency, directory presence.
    """

    @staticmethod
    def score_prospect(
        website_status: Optional[str] = None,
        has_email: bool = False,
        has_phone: bool = False,
        content_recency: str = "recent",  # recent, moderate, old, unknown
        directory_sources: int = 1,  # how many directories listed them
        notes: str = ""
    ) -> Tuple[int, str]:
        """
        Calculate validation score (1-5) and return score + notes.

        Returns:
            Tuple of (score, detailed_notes)
        """
        score = 0
        reasons = []

        # Website status (1-2 points)
        if website_status == "200_OK":
            score += 2
            reasons.append("Website live")
        elif website_status == "301_302":
            score += 1
            reasons.append("Website redirects (possibly active)")
        else:
            reasons.append("Website not verified or unreachable")

        # Contact info (1-2 points)
        contact_methods = sum([has_email, has_phone])
        if contact_methods >= 2:
            score += 2
            reasons.append("Email + phone verified")
        elif contact_methods == 1:
            score += 1
            reasons.append("One contact method verified")
        else:
            reasons.append("No contact info found")

        # Content recency (0-1 point)
        if content_recency == "recent":
            score += 1
            reasons.append("Content recently updated")
        elif content_recency == "moderate":
            score += 0.5
            reasons.append("Content moderately recent")
        else:
            reasons.append("Content age unknown")

        # Multiple directories (0-1 point)
        if directory_sources >= 2:
            score += 1
            reasons.append(f"Found in {directory_sources} professional directories")

        # Cap at 5
        score = min(int(score), 5)
        score = max(score, 1)  # Minimum 1

        full_notes = "; ".join(reasons)
        if notes:
            full_notes += f"; {notes}"

        return score, full_notes


# CLI helper to test email generation
if __name__ == "__main__":
    # Test prospect
    test_prospect = Prospect(
        name="Dr. Sarah Thompson",
        title="LMFT",
        practice_name="Family First Therapy",
        email="sarah@familyfirst.com",
        phone="555-123-4567",
        website="https://familyfirst.com",
        state="CA",
        city="Los Angeles",
        specialties=["divorce", "child therapy"],
        validation_score=4,
        validation_notes="Website live, email + phone verified"
    )

    # Generate sample emails
    print("=" * 60)
    print("THERAPIST INITIAL (Variant 1)")
    print("=" * 60)
    subj, body = EmailGenerator.therapist_initial(test_prospect, variant=1)
    print(f"Subject: {subj}\n")
    print(body)

    print("\n" + "=" * 60)
    print("THERAPIST INITIAL (Variant 2)")
    print("=" * 60)
    subj, body = EmailGenerator.therapist_initial(test_prospect, variant=2)
    print(f"Subject: {subj}\n")
    print(body)

    print("\n" + "=" * 60)
    print("LAWYER INITIAL")
    print("=" * 60)
    test_lawyer = Prospect(
        name="John Martinez",
        title="JD",
        practice_name="Martinez Family Law",
        email="john@martinezfamilylaw.com",
        phone="555-987-6543",
        website="https://martinezfamilylaw.com",
        state="CA",
        city="San Francisco",
        specialties=["custody", "divorce"],
        validation_score=4
    )
    subj, body = EmailGenerator.lawyer_initial(test_lawyer, variant=1)
    print(f"Subject: {subj}\n")
    print(body)
