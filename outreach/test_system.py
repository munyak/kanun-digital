#!/usr/bin/env python3
"""
KaNun Digital System Test Suite

Validates all components of the prospect research and outreach system.
Run this to ensure everything is working before production use.

Usage:
    python test_system.py
    python test_system.py --quick     # Skip network tests
"""

import sys
import os
import json
import argparse
from datetime import datetime

# Import core modules
from prospect_engine import Prospect, ProspectDatabase, EmailGenerator, ValidationScorer
from email_templates import EmailSequence, EmailSequencePhase, SequenceManager
from outreach_manager import OutreachManager


class SystemTest:
    """Test suite for KaNun prospect system."""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def log(self, level, message):
        """Print log message."""
        if level == "PASS":
            print(f"  [+] {message}")
            self.passed += 1
        elif level == "FAIL":
            print(f"  [!] {message}")
            self.failed += 1
        elif level == "WARN":
            print(f"  [*] {message}")
            self.warnings += 1
        elif level == "INFO":
            print(f"  [i] {message}")

    def test_prospect_creation(self):
        """Test: Create and validate prospect objects."""
        print("\n[TEST] Prospect Creation & Validation")
        print("-" * 60)

        try:
            prospect = Prospect(
                name="Dr. Sarah Thompson",
                title="LMFT",
                practice_name="Family First",
                email="sarah@test.com",
                phone="555-1234",
                state="CA",
                city="LA",
                validation_score=4,
            )
            self.log("PASS", "Prospect object created")

            # Test validation
            is_valid, reason = prospect.validate_basic_fields()
            if is_valid:
                self.log("PASS", "Prospect validation passed")
            else:
                self.log("FAIL", f"Prospect validation failed: {reason}")

            # Test conversion to dict
            prospect_dict = prospect.to_dict()
            if isinstance(prospect_dict, dict) and prospect_dict['name'] == "Dr. Sarah Thompson":
                self.log("PASS", "Prospect to_dict() works")
            else:
                self.log("FAIL", "Prospect to_dict() failed")

        except Exception as e:
            self.log("FAIL", f"Exception during prospect creation: {e}")

    def test_database_operations(self):
        """Test: Database CRUD operations."""
        print("\n[TEST] Database Operations")
        print("-" * 60)

        try:
            # Create test database in memory
            test_db_path = "/tmp/test_prospects.json"

            # Clean up if exists
            if os.path.exists(test_db_path):
                os.remove(test_db_path)

            db = ProspectDatabase(test_db_path)
            self.log("PASS", "Database initialization")

            # Add prospects
            p1 = Prospect(
                name="Dr. Alice",
                title="LMFT",
                practice_name="Practice A",
                email="alice@test.com",
                phone="555-1111",
                state="CA",
                city="LA",
                validation_score=4,
            )

            p2 = Prospect(
                name="John Smith, JD",
                title="JD",
                practice_name="Law Firm B",
                email="john@test.com",
                phone="555-2222",
                state="CA",
                city="SF",
                validation_score=3,
            )

            is_new_1 = db.add_or_update(p1)
            is_new_2 = db.add_or_update(p2)

            if is_new_1 and is_new_2:
                self.log("PASS", "Add new prospects")
            else:
                self.log("FAIL", "Add new prospects didn't return True")

            # Check deduplication
            is_new_3 = db.add_or_update(p1)  # Add duplicate
            if not is_new_3:
                self.log("PASS", "Deduplication works")
            else:
                self.log("WARN", "Deduplication may not be working correctly")

            # Get pending prospects
            pending = db.get_pending_prospects()
            if len(pending) == 2:
                self.log("PASS", f"Get pending prospects ({len(pending)} found)")
            else:
                self.log("FAIL", f"Expected 2 pending, got {len(pending)}")

            # Mark one as contacted
            db.mark_contacted(p1, "therapist_initial")
            p1_updated = [p for p in db.prospects.values() if p.name == "Dr. Alice"][0]
            if p1_updated.outreach_status == "contacted":
                self.log("PASS", "Mark contacted works")
            else:
                self.log("FAIL", "Mark contacted didn't update status")

            # Save and reload
            db.save()
            if os.path.exists(test_db_path):
                self.log("PASS", "Database saved to JSON")
            else:
                self.log("FAIL", "Database JSON not created")

            if os.path.exists(test_db_path.replace('.json', '.csv')):
                self.log("PASS", "Database exported to CSV")
            else:
                self.log("FAIL", "Database CSV not created")

            # Reload and verify
            db2 = ProspectDatabase(test_db_path)
            if len(db2.prospects) == 2:
                self.log("PASS", "Database reload preserves data")
            else:
                self.log("FAIL", f"Database reload failed: {len(db2.prospects)} != 2")

            # Get stats
            stats = db.get_stats()
            if stats['total'] == 2:
                self.log("PASS", "Database stats work")
            else:
                self.log("FAIL", f"Stats total incorrect: {stats['total']}")

            # Cleanup
            os.remove(test_db_path)
            os.remove(test_db_path.replace('.json', '.csv'))

        except Exception as e:
            self.log("FAIL", f"Exception during database operations: {e}")

    def test_email_generation(self):
        """Test: Email generation for different prospect types."""
        print("\n[TEST] Email Generation")
        print("-" * 60)

        try:
            therapist = Prospect(
                name="Dr. Sarah Thompson",
                title="LMFT",
                practice_name="Family First",
                email="sarah@test.com",
                specialties=["divorce", "family therapy"],
                state="CA",
                city="LA",
            )

            lawyer = Prospect(
                name="John Smith",
                title="JD",
                practice_name="Family Law Partners",
                email="john@test.com",
                specialties=["custody", "divorce"],
                state="CA",
                city="SF",
            )

            # Test therapist emails
            subj, body = EmailGenerator.therapist_initial(therapist, variant=1)
            if subj and body and len(body) > 50:
                self.log("PASS", "Therapist initial email generated")
            else:
                self.log("FAIL", "Therapist initial email malformed")

            subj2, body2 = EmailGenerator.therapist_followup1(therapist)
            if subj2 and body2 and len(body2) > 30:
                self.log("PASS", "Therapist followup1 email generated")
            else:
                self.log("FAIL", "Therapist followup1 email malformed")

            subj3, body3 = EmailGenerator.therapist_followup2(therapist)
            if subj3 and body3 and len(body3) > 30:
                self.log("PASS", "Therapist followup2 email generated")
            else:
                self.log("FAIL", "Therapist followup2 email malformed")

            # Test lawyer emails
            subj_l, body_l = EmailGenerator.lawyer_initial(lawyer, variant=1)
            if subj_l and body_l and len(body_l) > 50:
                self.log("PASS", "Lawyer initial email generated")
            else:
                self.log("FAIL", "Lawyer initial email malformed")

            subj_l2, body_l2 = EmailGenerator.lawyer_followup1(lawyer)
            if subj_l2 and body_l2 and len(body_l2) > 30:
                self.log("PASS", "Lawyer followup1 email generated")
            else:
                self.log("FAIL", "Lawyer followup1 email malformed")

            # Test personalization
            if therapist.name.split()[0] in body:
                self.log("PASS", "Emails are personalized with prospect name")
            else:
                self.log("WARN", "Email personalization may not be working")

        except Exception as e:
            self.log("FAIL", f"Exception during email generation: {e}")

    def test_email_sequences(self):
        """Test: Email sequence building."""
        print("\n[TEST] Email Sequences")
        print("-" * 60)

        try:
            therapist = Prospect(
                name="Dr. Sarah Thompson",
                title="LMFT",
                practice_name="Family First Therapy",
                email="sarah@test.com",
                state="CA",
                city="LA",
            )

            # Build therapist sequence
            seq = EmailSequence(therapist, "therapist")
            emails = seq.get_all_emails()

            if len(emails) == 3:
                self.log("PASS", "Therapist sequence has 3 emails")
            else:
                self.log("FAIL", f"Therapist sequence has {len(emails)} emails, expected 3")

            # Check phases
            phases = [e['phase'] for e in emails]
            if (EmailSequencePhase.INITIAL in phases and
                EmailSequencePhase.FOLLOWUP_1 in phases and
                EmailSequencePhase.FOLLOWUP_2 in phases):
                self.log("PASS", "All sequence phases present")
            else:
                self.log("FAIL", "Missing sequence phases")

            # Check days
            days = [e['day'] for e in emails]
            if days == [1, 5, 12]:
                self.log("PASS", "Email days are correct (1, 5, 12)")
            else:
                self.log("FAIL", f"Email days incorrect: {days}")

            # Test lawyer sequence
            lawyer = Prospect(
                name="John Smith",
                title="JD",
                practice_name="Smith Law Firm",
                email="john@test.com",
                state="CA",
                city="SF",
            )

            seq_l = EmailSequence(lawyer, "lawyer")
            emails_l = seq_l.get_all_emails()

            if len(emails_l) == 3:
                self.log("PASS", "Lawyer sequence has 3 emails")
            else:
                self.log("FAIL", f"Lawyer sequence has {len(emails_l)} emails")

        except Exception as e:
            self.log("FAIL", f"Exception during sequence testing: {e}")

    def test_validation_scorer(self):
        """Test: Validation scoring logic."""
        print("\n[TEST] Validation Scoring")
        print("-" * 60)

        try:
            # Test high score
            score, notes = ValidationScorer.score_prospect(
                website_status="200_OK",
                has_email=True,
                has_phone=True,
                content_recency="recent",
                directory_sources=2,
            )

            if score >= 4:
                self.log("PASS", f"High validation score calculated ({score}/5)")
            else:
                self.log("WARN", f"Expected high score, got {score}")

            # Test low score
            score2, notes2 = ValidationScorer.score_prospect(
                website_status=None,
                has_email=False,
                has_phone=False,
                content_recency="unknown",
                directory_sources=1,
            )

            if score2 <= 2:
                self.log("PASS", f"Low validation score calculated ({score2}/5)")
            else:
                self.log("WARN", f"Expected low score, got {score2}")

            # Test medium score
            score3, notes3 = ValidationScorer.score_prospect(
                website_status="200_OK",
                has_email=True,
                has_phone=False,
                content_recency="moderate",
                directory_sources=1,
            )

            if 2 <= score3 <= 4:
                self.log("PASS", f"Medium validation score calculated ({score3}/5)")
            else:
                self.log("WARN", f"Unexpected medium score: {score3}")

            # Check notes are populated
            if notes and isinstance(notes, str):
                self.log("PASS", "Validation notes generated")
            else:
                self.log("FAIL", "Validation notes not properly generated")

        except Exception as e:
            self.log("FAIL", f"Exception during validation scoring: {e}")

    def test_outreach_manager(self):
        """Test: Outreach manager operations."""
        print("\n[TEST] Outreach Manager")
        print("-" * 60)

        try:
            # Create test database
            test_db_path = "/tmp/test_outreach.json"
            if os.path.exists(test_db_path):
                os.remove(test_db_path)

            db = ProspectDatabase(test_db_path)

            # Add test prospects
            for i in range(3):
                p = Prospect(
                    name=f"Test Prospect {i}",
                    title="LMFT",
                    practice_name=f"Practice {i}",
                    email=f"prospect{i}@test.com",
                    phone=f"555-000{i}",
                    state="CA",
                    city="LA",
                    validation_score=3 + i,
                )
                db.add_or_update(p)

            db.save()

            # Initialize manager
            manager = OutreachManager(test_db_path)

            # Test stats
            manager.print_stats()
            self.log("PASS", "Outreach manager stats displayed")

            # Test batch email generation
            emails = manager.generate_batch_emails("therapist", limit=2)
            if len(emails) > 0:
                self.log("PASS", f"Generated batch emails ({len(emails)})")
            else:
                self.log("FAIL", "No batch emails generated")

            # Test mark sent
            if emails:
                first_email = emails[0]
                success = manager.mark_sent(
                    first_email['to_email'],
                    template_id="test_template"
                )
                if success:
                    self.log("PASS", "Mark sent operation successful")
                else:
                    self.log("FAIL", "Mark sent operation failed")

            # Cleanup
            os.remove(test_db_path)
            os.remove(test_db_path.replace('.json', '.csv'))

        except Exception as e:
            self.log("FAIL", f"Exception during outreach manager test: {e}")

    def test_file_structure(self):
        """Test: Required files exist and have correct structure."""
        print("\n[TEST] File Structure")
        print("-" * 60)

        base_dir = "/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach"

        required_files = [
            ("prospect_engine.py", "Prospect data model and validation"),
            ("run_research.py", "Automated research and discovery"),
            ("email_templates.py", "Email sequence generation"),
            ("outreach_manager.py", "Batch outreach operations"),
            ("requirements.txt", "Python dependencies"),
            ("config.py", "Configuration settings"),
            ("README.md", "Full documentation"),
            ("QUICKSTART.md", "Quick start guide"),
        ]

        for filename, description in required_files:
            filepath = os.path.join(base_dir, filename)
            if os.path.exists(filepath):
                # Check file size
                size = os.path.getsize(filepath)
                if size > 100:
                    self.log("PASS", f"{filename} ({size} bytes)")
                else:
                    self.log("WARN", f"{filename} exists but is very small ({size} bytes)")
            else:
                self.log("FAIL", f"{filename} missing")

        # Check sample data
        sample_path = os.path.join(base_dir, "sample_prospects.json")
        if os.path.exists(sample_path):
            try:
                with open(sample_path) as f:
                    data = json.load(f)
                    if len(data) > 0:
                        self.log("PASS", f"sample_prospects.json ({len(data)} sample records)")
                    else:
                        self.log("WARN", "sample_prospects.json is empty")
            except json.JSONDecodeError:
                self.log("FAIL", "sample_prospects.json is not valid JSON")
        else:
            self.log("WARN", "sample_prospects.json not found")

    def run_all_tests(self, skip_network=False):
        """Run all tests."""
        print("\n" + "=" * 70)
        print("KaNun Digital System Test Suite")
        print("=" * 70)

        self.test_file_structure()
        self.test_prospect_creation()
        self.test_database_operations()
        self.test_email_generation()
        self.test_email_sequences()
        self.test_validation_scorer()
        self.test_outreach_manager()

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Passed:  {self.passed}")
        print(f"Failed:  {self.failed}")
        print(f"Warnings: {self.warnings}")
        print("=" * 70)

        if self.failed == 0:
            print("[+] All tests passed! System is ready for use.")
            return True
        else:
            print(f"[!] {self.failed} test(s) failed. Review output above.")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="KaNun Digital System Test Suite"
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help="Skip network-dependent tests"
    )

    args = parser.parse_args()

    tester = SystemTest()
    success = tester.run_all_tests(skip_network=args.quick)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
