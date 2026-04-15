#!/usr/bin/env python3
"""
KaNun Digital Outreach Manager

Manages batch outreach: generate emails, schedule follow-ups, track responses.

Usage:
    python outreach_manager.py --action generate --type therapist --limit 5
    python outreach_manager.py --action mark-sent --email sarah@familyfirst.com
    python outreach_manager.py --action followup-schedule --days 5
    python outreach_manager.py --action stats
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import List, Optional

from prospect_engine import ProspectDatabase, Prospect, EmailGenerator
from email_templates import EmailSequence, EmailSequencePhase


class OutreachManager:
    """Manages bulk outreach operations."""

    def __init__(self, db_path: str):
        self.db = ProspectDatabase(db_path)

    def generate_batch_emails(
        self, prospect_type: str, limit: int = 5, variant: int = 1
    ) -> List[dict]:
        """
        Generate initial emails for pending prospects.

        Returns list of email dicts with recipient and full email text.
        """
        pending = self.db.get_pending_prospects(limit=limit)
        emails = []

        for prospect in pending:
            if not prospect.email and not prospect.phone:
                print(f"[!] {prospect.name}: No contact info. Skipping.")
                continue

            # Determine prospect type if not provided
            if not prospect_type:
                # Infer from title
                if 'LMFT' in prospect.title or 'LCSW' in prospect.title or 'PhD' in prospect.title:
                    inferred_type = 'therapist'
                elif 'JD' in prospect.title or 'Esq' in prospect.title:
                    inferred_type = 'lawyer'
                else:
                    inferred_type = 'therapist'  # Default
            else:
                inferred_type = prospect_type

            # Generate sequence
            sequence = EmailSequence(prospect, inferred_type)
            initial = sequence.get_email_for_phase(EmailSequencePhase.INITIAL)

            emails.append({
                'to_email': prospect.email,
                'to_phone': prospect.phone,
                'recipient_name': prospect.name,
                'subject': initial['subject'],
                'body': initial['body'],
                'prospect_type': inferred_type,
                'variant': initial.get('variant', 1),
                'template_id': f"{inferred_type}_initial_variant{initial.get('variant', 1)}",
            })

        return emails

    def print_batch_emails(self, emails: List[dict]) -> None:
        """Pretty-print a batch of emails for review."""
        print(f"\n{'=' * 70}")
        print(f"OUTREACH BATCH: {len(emails)} emails ready to send")
        print(f"{'=' * 70}\n")

        for i, email in enumerate(emails, 1):
            print(f"[{i}] TO: {email['to_email'] or email['to_phone']}")
            print(f"    NAME: {email['recipient_name']}")
            print(f"    TYPE: {email['prospect_type']}")
            print(f"    SUBJECT: {email['subject']}")
            print(f"\n{email['body']}")
            print(f"\n{'-' * 70}\n")

    def mark_sent(self, recipient_email: str, template_id: str) -> bool:
        """
        Mark a prospect as contacted.

        Returns True if found and updated, False otherwise.
        """
        for prospect in self.db.prospects.values():
            if prospect.email == recipient_email or prospect.phone == recipient_email:
                self.db.mark_contacted(prospect, template_id)
                self.db.save()
                print(f"[+] Marked {prospect.name} as contacted ({template_id})")
                return True
        return False

    def get_followup_due(self, days_offset: int = 5) -> List[Prospect]:
        """
        Get prospects due for follow-up at a given offset.

        E.g., days_offset=5 returns prospects whose initial email was sent
        5+ days ago and haven't received followup 1 yet.
        """
        target_date = datetime.now() - timedelta(days=days_offset)
        due = []

        for prospect in self.db.prospects.values():
            if prospect.outreach_status != "contacted":
                continue

            # Check if most recent email_sent was > days_offset days ago
            if prospect.outreach_history:
                last_email = prospect.outreach_history[-1]
                if last_email.get('event') == 'email_sent':
                    sent_date = datetime.fromisoformat(last_email['timestamp'])
                    if sent_date <= target_date:
                        due.append(prospect)

        return due

    def generate_followup_sequence(self, prospect: Prospect, day: int = 5) -> Optional[dict]:
        """
        Generate a follow-up email for a prospect.

        day: 5 for followup 1, 12 for followup 2
        """
        # Infer type from title
        if 'LMFT' in prospect.title or 'LCSW' in prospect.title or 'PhD' in prospect.title:
            prospect_type = 'therapist'
        elif 'JD' in prospect.title or 'Esq' in prospect.title:
            prospect_type = 'lawyer'
        else:
            prospect_type = 'therapist'

        sequence = EmailSequence(prospect, prospect_type)

        if day == 5:
            phase = EmailSequencePhase.FOLLOWUP_1
        elif day == 12:
            phase = EmailSequencePhase.FOLLOWUP_2
        else:
            return None

        email = sequence.get_email_for_phase(phase)

        return {
            'to_email': prospect.email,
            'to_phone': prospect.phone,
            'recipient_name': prospect.name,
            'subject': email['subject'],
            'body': email['body'],
            'prospect_type': prospect_type,
            'day': day,
            'template_id': f"{prospect_type}_followup_{day}",
        }

    def print_stats(self) -> None:
        """Print database statistics."""
        stats = self.db.get_stats()
        pending = self.db.get_pending_prospects()

        print(f"\n{'=' * 70}")
        print("PROSPECT DATABASE STATISTICS")
        print(f"{'=' * 70}\n")

        print(f"Total prospects: {stats['total']}")
        print(f"\nBy outreach status:")
        for status, count in sorted(stats['by_status'].items()):
            print(f"  {status:15} {count:3}")

        print(f"\nBy validation score:")
        for score in ['1', '2', '3', '4', '5']:
            count = stats['by_validation_score'].get(score, 0)
            bar = '█' * count
            print(f"  Score {score}: {count:3} {bar}")

        print(f"\nPending outreach (top 10 by validation score):")
        for i, p in enumerate(pending[:10], 1):
            print(f"  [{i}] {p.name:30} ({p.validation_score}/5) - {p.email or p.phone or 'No contact'}")

        if len(pending) > 10:
            print(f"  ... and {len(pending) - 10} more pending")

    def export_for_crm(self, output_path: Optional[str] = None) -> None:
        """
        Export prospects to CSV for CRM import.
        (This is already done by ProspectDatabase.save(), but provided for clarity.)
        """
        if output_path:
            self.db.csv_path = output_path
        self.db.save()
        print(f"[+] Exported {len(self.db.prospects)} prospects to {self.db.csv_path}")

    def audit_validation_failures(self, threshold: int = 2) -> None:
        """
        Print prospects with low validation scores to understand why.
        """
        low_scoring = [
            p for p in self.db.prospects.values()
            if p.validation_score < threshold
        ]

        if not low_scoring:
            print(f"[+] No prospects with score < {threshold}")
            return

        print(f"\n{'=' * 70}")
        print(f"VALIDATION AUDIT: {len(low_scoring)} prospects with score < {threshold}")
        print(f"{'=' * 70}\n")

        for p in sorted(low_scoring, key=lambda x: x.validation_score):
            print(f"{p.name}")
            print(f"  Score: {p.validation_score}/5")
            print(f"  Notes: {p.validation_notes}")
            print(f"  Email: {p.email or 'Missing'}")
            print(f"  Phone: {p.phone or 'Missing'}")
            print(f"  Website: {p.website or 'Missing'}")
            print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="KaNun Digital Outreach Manager"
    )
    parser.add_argument(
        '--action',
        required=True,
        choices=['generate', 'mark-sent', 'followup-schedule', 'stats', 'audit', 'export'],
        help="Action to perform"
    )
    parser.add_argument(
        '--db',
        default='/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach/prospects.json',
        help="Path to prospect database"
    )
    parser.add_argument(
        '--type',
        choices=['therapist', 'lawyer', 'mediator'],
        help="Prospect type (for generate action)"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help="Limit number of emails (for generate action)"
    )
    parser.add_argument(
        '--email',
        help="Email address to mark as sent (for mark-sent action)"
    )
    parser.add_argument(
        '--template-id',
        default='initial',
        help="Template ID for tracking (for mark-sent action)"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=5,
        help="Days offset for followup schedule (5 or 12)"
    )
    parser.add_argument(
        '--output',
        help="Output path for export"
    )

    args = parser.parse_args()

    manager = OutreachManager(args.db)

    if args.action == 'generate':
        emails = manager.generate_batch_emails(args.type, limit=args.limit)
        manager.print_batch_emails(emails)
        print(f"\n[*] Copy and paste these emails into your email client, or integrate with email API.")
        print(f"    After sending, use: python outreach_manager.py --action mark-sent --email <email>")

    elif args.action == 'mark-sent':
        if not args.email:
            print("[!] --email required for mark-sent")
            return
        manager.mark_sent(args.email, args.template_id)

    elif args.action == 'followup-schedule':
        due = manager.get_followup_due(days_offset=args.days)
        print(f"\n[*] {len(due)} prospects due for {args.days}-day follow-up:")
        for p in due[:10]:
            email_dict = manager.generate_followup_sequence(p, day=args.days)
            if email_dict:
                print(f"\n  TO: {email_dict['to_email']}")
                print(f"  SUBJECT: {email_dict['subject']}")

    elif args.action == 'stats':
        manager.print_stats()

    elif args.action == 'audit':
        manager.audit_validation_failures(threshold=2)

    elif args.action == 'export':
        manager.export_for_crm(output_path=args.output)


if __name__ == "__main__":
    main()
