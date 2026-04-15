"""
KaNun Digital Email Templates & Sequencing

Generates personalized outreach sequences for different prospect types.
Supports A/B testing and multi-touch follow-up campaigns.
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from enum import Enum

from prospect_engine import Prospect, EmailGenerator


class EmailSequencePhase(Enum):
    """Phases in the outreach sequence."""
    INITIAL = "initial"  # Day 1
    FOLLOWUP_1 = "followup_1"  # Day 5
    FOLLOWUP_2 = "followup_2"  # Day 12 (breakup)


class EmailSequence:
    """Manages a multi-touch email sequence for a prospect."""

    def __init__(self, prospect: Prospect, prospect_type: str):
        """
        Initialize a sequence for a prospect.

        Args:
            prospect: The prospect to email
            prospect_type: 'therapist', 'lawyer', or 'mediator'
        """
        self.prospect = prospect
        self.prospect_type = prospect_type.lower()
        self.emails: List[Dict] = []
        self._build_sequence()

    def _build_sequence(self) -> None:
        """Build the complete sequence for this prospect type."""
        if self.prospect_type == "therapist":
            self._build_therapist_sequence()
        elif self.prospect_type == "lawyer":
            self._build_lawyer_sequence()
        elif self.prospect_type == "mediator":
            self._build_mediator_sequence()
        else:
            raise ValueError(f"Unknown prospect type: {self.prospect_type}")

    def _build_therapist_sequence(self) -> None:
        """Build 3-email sequence for therapists."""
        # Day 1: Initial
        subj, body = EmailGenerator.therapist_initial(self.prospect, variant=1)
        self.emails.append({
            'phase': EmailSequencePhase.INITIAL,
            'day': 1,
            'subject': subj,
            'body': body,
            'variant': 1,
        })

        # Day 5: Follow-up 1
        subj, body = EmailGenerator.therapist_followup1(self.prospect)
        self.emails.append({
            'phase': EmailSequencePhase.FOLLOWUP_1,
            'day': 5,
            'subject': subj,
            'body': body,
            'variant': None,
        })

        # Day 12: Follow-up 2 (breakup)
        subj, body = EmailGenerator.therapist_followup2(self.prospect)
        self.emails.append({
            'phase': EmailSequencePhase.FOLLOWUP_2,
            'day': 12,
            'subject': subj,
            'body': body,
            'variant': None,
        })

    def _build_lawyer_sequence(self) -> None:
        """Build 3-email sequence for lawyers."""
        # Day 1: Initial
        subj, body = EmailGenerator.lawyer_initial(self.prospect, variant=1)
        self.emails.append({
            'phase': EmailSequencePhase.INITIAL,
            'day': 1,
            'subject': subj,
            'body': body,
            'variant': 1,
        })

        # Day 5: Follow-up 1
        subj, body = EmailGenerator.lawyer_followup1(self.prospect)
        self.emails.append({
            'phase': EmailSequencePhase.FOLLOWUP_1,
            'day': 5,
            'subject': subj,
            'body': body,
            'variant': None,
        })

        # Day 12: Follow-up 2 (breakup)
        subj, body = EmailGenerator.lawyer_followup2(self.prospect)
        self.emails.append({
            'phase': EmailSequencePhase.FOLLOWUP_2,
            'day': 12,
            'subject': subj,
            'body': body,
            'variant': None,
        })

    def _build_mediator_sequence(self) -> None:
        """Build 3-email sequence for mediators."""
        # Similar to therapist; mediators = therapists + legal
        # Day 1: Initial
        subj, body = EmailGenerator.mediator_initial(self.prospect, variant=1)
        self.emails.append({
            'phase': EmailSequencePhase.INITIAL,
            'day': 1,
            'subject': subj,
            'body': body,
            'variant': 1,
        })

        # Day 5: Follow-up 1
        name_first = self.prospect.name.split()[0]
        subj = "Re: digital safety resource for mediation"
        body = f"""Hi {name_first},

Following up on my note from last week.

Many families going through mediation have blind spots on the digital side — devices, privacy, co-parenting apps. We help navigate those. Takes a load off you.

Would 15 minutes make sense?

Thanks,
Bren
KaNun Digital"""

        self.emails.append({
            'phase': EmailSequencePhase.FOLLOWUP_1,
            'day': 5,
            'subject': subj,
            'body': body,
            'variant': None,
        })

        # Day 12: Follow-up 2 (breakup)
        subj = "Last note: KaNun Digital for mediators"
        body = f"""Hi {name_first},

Final note from me.

If you're interested in adding digital safety expertise to your mediation practice, let's talk. If not, all good.

Door's open.

Bren"""

        self.emails.append({
            'phase': EmailSequencePhase.FOLLOWUP_2,
            'day': 12,
            'subject': subj,
            'body': body,
            'variant': None,
        })

    def get_email_for_phase(self, phase: EmailSequencePhase) -> Dict:
        """Get the email dict for a specific phase."""
        for email in self.emails:
            if email['phase'] == phase:
                return email
        raise ValueError(f"No email for phase {phase}")

    def get_all_emails(self) -> List[Dict]:
        """Return the complete sequence."""
        return self.emails

    def get_next_email_date(self, last_contact_date: datetime) -> Tuple[EmailSequencePhase, datetime]:
        """
        Given the last contact date, return the next phase and when to send.

        Returns:
            Tuple of (EmailSequencePhase, datetime)
        """
        for email in self.emails:
            send_date = last_contact_date + timedelta(days=email['day'])
            if send_date > datetime.now():
                return (email['phase'], send_date)

        # All emails sent
        return (None, None)


class SequenceManager:
    """Manages outreach sequences across multiple prospects."""

    def __init__(self):
        self.sequences: Dict[str, EmailSequence] = {}

    def create_sequence(
        self, prospect: Prospect, prospect_type: str
    ) -> EmailSequence:
        """Create and store a sequence for a prospect."""
        key = f"{prospect.email or prospect.phone}: {prospect.name}"
        sequence = EmailSequence(prospect, prospect_type)
        self.sequences[key] = sequence
        return sequence

    def get_sequence(self, prospect: Prospect) -> EmailSequence:
        """Retrieve an existing sequence."""
        key = f"{prospect.email or prospect.phone}: {prospect.name}"
        return self.sequences.get(key)

    def get_pending_sends(self) -> List[Tuple[Prospect, EmailSequence, Dict]]:
        """
        Return list of (prospect, sequence, email_to_send) tuples
        for emails due to be sent today.

        This would be called by an email scheduler.
        """
        pending = []
        # Implementation would check dates against prospect.outreach_history
        # and return emails ready to send
        return pending


# Template helpers for manual review / A/B testing

THERAPIST_SUBJECT_LINES = [
    "Quick resource for your families: digital safety",
    "Thought of you: expert on the 'tech part' of family issues",
    "Digital safety = better family outcomes",
    "Therapists: free digital safety consultation for your practice",
]

LAWYER_SUBJECT_LINES = [
    "Expert resource for your custody/divorce cases: digital evidence & device security",
    "Forensic-grade digital safety advisor for your family law clients",
    "Help your clients navigate the digital side of custody disputes",
    "Family law + digital security = better outcomes",
]

MEDIATOR_SUBJECT_LINES = [
    "Digital safety resource for families in mediation",
    "Help your families navigate device & privacy issues during mediation",
    "Mediators: value-add service for digital safety",
    "Digital clarity = smoother mediations",
]


def get_subject_line_variations(prospect_type: str) -> List[str]:
    """Return subject line variations for A/B testing."""
    prospect_type = prospect_type.lower()
    if prospect_type == "therapist":
        return THERAPIST_SUBJECT_LINES
    elif prospect_type == "lawyer":
        return LAWYER_SUBJECT_LINES
    elif prospect_type == "mediator":
        return MEDIATOR_SUBJECT_LINES
    else:
        return []


# CLI: Generate sequences and print for review
if __name__ == "__main__":
    # Test with sample prospects
    test_therapist = Prospect(
        name="Dr. Sarah Thompson",
        title="LMFT",
        practice_name="Family First Therapy",
        email="sarah@familyfirst.com",
        phone="555-123-4567",
        state="CA",
        city="Los Angeles",
        specialties=["divorce", "family therapy"],
        validation_score=4,
    )

    test_lawyer = Prospect(
        name="John Martinez",
        title="JD",
        practice_name="Martinez Family Law",
        email="john@martinezfamilylaw.com",
        phone="555-987-6543",
        state="CA",
        city="San Francisco",
        specialties=["custody", "divorce"],
        validation_score=4,
    )

    # Generate therapist sequence
    print("=" * 70)
    print("THERAPIST EMAIL SEQUENCE")
    print("=" * 70)
    therapist_seq = EmailSequence(test_therapist, "therapist")
    for email in therapist_seq.get_all_emails():
        print(f"\nDay {email['day']}: {email['phase'].value}")
        print(f"Subject: {email['subject']}")
        print(f"Body:\n{email['body']}")
        print("-" * 70)

    # Generate lawyer sequence
    print("\n" + "=" * 70)
    print("LAWYER EMAIL SEQUENCE")
    print("=" * 70)
    lawyer_seq = EmailSequence(test_lawyer, "lawyer")
    for email in lawyer_seq.get_all_emails():
        print(f"\nDay {email['day']}: {email['phase'].value}")
        print(f"Subject: {email['subject']}")
        print(f"Body:\n{email['body']}")
        print("-" * 70)

    # Subject line variations
    print("\n" + "=" * 70)
    print("SUBJECT LINE VARIATIONS FOR A/B TESTING")
    print("=" * 70)
    print("\nTherapist:")
    for subj in get_subject_line_variations("therapist"):
        print(f"  - {subj}")
    print("\nLawyer:")
    for subj in get_subject_line_variations("lawyer"):
        print(f"  - {subj}")
    print("\nMediator:")
    for subj in get_subject_line_variations("mediator"):
        print(f"  - {subj}")
