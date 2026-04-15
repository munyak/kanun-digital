#!/usr/bin/env python3
"""
KaNun Digital Prospect Research Script

Searches for therapists, lawyers, and mediators across multiple directories,
validates their contact info and website status, and saves to prospects database.

Usage:
    python run_research.py --type therapist --state CA --city "Los Angeles" --count 20
    python run_research.py --type lawyer --state NY --count 15
    python run_research.py --type mediator --state TX --city Austin
"""

import argparse
import time
import re
import sys
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, quote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

from prospect_engine import Prospect, ProspectDatabase, ValidationScorer


# Configuration
REQUESTS_TIMEOUT = 5
RATE_LIMIT_DELAY = 1.5  # seconds between requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class ProspectSearcher:
    """
    Searches multiple directories for prospects (therapists, lawyers, mediators).
    Validates contact info and website status before adding to database.
    """

    def __init__(self, db: ProspectDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.found_count = 0
        self.validated_count = 0

    def _safe_request(self, url: str, method: str = 'GET') -> Optional[requests.Response]:
        """
        Make a request with rate limiting and error handling.
        Returns None on failure.
        """
        try:
            time.sleep(RATE_LIMIT_DELAY)
            resp = self.session.request(method, url, timeout=REQUESTS_TIMEOUT)
            return resp if resp.status_code < 400 else None
        except (requests.RequestException, requests.Timeout) as e:
            print(f"  [WARN] Request failed: {e}")
            return None

    def _validate_website(self, url: Optional[str]) -> Tuple[Optional[str], str]:
        """
        Check if website is live. Returns (status_code, message).
        Status codes: '200_OK', '301_302', '404', 'timeout', 'invalid'
        """
        if not url:
            return None, "No URL provided"

        # Basic URL validation
        if not url.startswith('http'):
            url = 'https://' + url

        try:
            resp = self._safe_request(url, method='HEAD')
            if resp is None:
                # Try GET if HEAD fails
                resp = self._safe_request(url, method='GET')
                if resp is None:
                    return None, "Unreachable"

            if resp.status_code == 200:
                return '200_OK', "Live"
            elif resp.status_code in [301, 302]:
                return '301_302', "Redirects"
            else:
                return str(resp.status_code), f"Status {resp.status_code}"

        except Exception as e:
            return None, str(e)[:50]

    def _extract_contact_info(
        self, html: str, url: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract email and phone from HTML content.
        Returns (email, phone).
        """
        email = None
        phone = None

        # Email regex (basic)
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', html)
        if email_match:
            email = email_match.group(1)
            # Exclude no-reply and other typical invalid addresses
            if 'no-reply' not in email.lower() and 'noreply' not in email.lower():
                email = email
            else:
                email = None

        # Phone regex: (123) 456-7890, 123-456-7890, 1234567890, etc.
        phone_match = re.search(
            r'(\+?1?\s*)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}',
            html
        )
        if phone_match:
            phone = phone_match.group(0).strip()

        return email, phone

    def search_psychology_today(
        self, state: str, city: Optional[str] = None, limit: int = 10
    ) -> List[Prospect]:
        """
        Search Psychology Today therapist directory.
        Uses the search API endpoint.
        """
        print(f"\n[*] Searching Psychology Today for therapists in {state}...")
        prospects = []

        # Psychology Today search API (may require rate limiting)
        # Format: https://www.psychologytoday.com/us/therapists/[location]
        location = quote(city if city else state)
        base_url = f"https://www.psychologytoday.com/us/therapists/{location}"

        resp = self._safe_request(base_url)
        if not resp:
            print(f"  [!] Could not reach Psychology Today for {location}")
            return prospects

        try:
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Psychology Today uses dynamic loading; try to find therapist profiles
            # Look for profile links/cards
            profile_links = soup.find_all('a', class_=re.compile('TherapistProfile'))

            if not profile_links:
                # Alternative: look for any links with therapist names
                profile_links = soup.find_all(
                    'a', href=re.compile(r'/profile/|/therapists/')
                )[:limit]

            for link in profile_links[:limit]:
                name = link.get_text(strip=True)
                if not name or len(name) < 2:
                    continue

                profile_url = urljoin(base_url, link.get('href', ''))

                # Fetch profile page to get details
                profile_resp = self._safe_request(profile_url)
                if not profile_resp:
                    continue

                profile_soup = BeautifulSoup(profile_resp.text, 'html.parser')

                # Extract details from profile
                title_elem = profile_soup.find(text=re.compile(r'LMFT|LCSW|PsyD|PhD|LPC'))
                title = title_elem if title_elem else "Therapist"

                # Get specialties
                specialties_text = profile_soup.find(
                    text=re.compile(r'Specialties|Issues')
                )
                specialties = []
                if specialties_text:
                    # Try to extract from nearby content
                    specialties = [
                        s.strip() for s in
                        re.findall(r'\b(divorce|family|child|custody|addiction)\b',
                                   profile_resp.text, re.IGNORECASE)
                    ]

                email, phone = self._extract_contact_info(profile_resp.text, profile_url)

                # Create prospect
                prospect = Prospect(
                    name=name,
                    title=str(title),
                    practice_name=name,  # Use name as practice if not found
                    email=email,
                    phone=phone,
                    website=profile_url,
                    directory_url=profile_url,
                    specialties=list(set(specialties)) if specialties else ["family therapy"],
                    state=state,
                    city=city or state,
                )

                # Validate
                website_status, _ = self._validate_website(profile_url)
                score, notes = ValidationScorer.score_prospect(
                    website_status=website_status,
                    has_email=bool(email),
                    has_phone=bool(phone),
                    content_recency='recent' if profile_resp else 'unknown',
                    directory_sources=1,
                )

                prospect.validation_score = score
                prospect.validation_notes = notes

                if score >= 2:  # Only include if minimally valid
                    prospects.append(prospect)
                    self.found_count += 1
                    print(f"  [+] {name} ({score}/5) - {email or phone or 'No contact'}")
                else:
                    print(f"  [-] {name} - validation score too low ({score}/5)")

        except Exception as e:
            print(f"  [!] Error parsing Psychology Today: {e}")

        return prospects[:limit]

    def search_avvo_lawyers(
        self, state: str, practice_area: str = "family-law", limit: int = 10
    ) -> List[Prospect]:
        """
        Search Avvo lawyer directory for family law attorneys.
        Avvo URL pattern: https://www.avvo.com/legal-guides/[practice-area]/[state]
        """
        print(f"\n[*] Searching Avvo for family law attorneys in {state}...")
        prospects = []

        base_url = f"https://www.avvo.com/legal-guides/{practice_area}/{state.lower()}"

        resp = self._safe_request(base_url)
        if not resp:
            print(f"  [!] Could not reach Avvo for {state}")
            return prospects

        try:
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Avvo lists lawyers with profile links
            lawyer_links = soup.find_all('a', class_=re.compile('LawyerLink|lawyer-name'))

            if not lawyer_links:
                # Broader fallback
                lawyer_links = soup.find_all(
                    'a', href=re.compile(r'/attorney/')
                )[:limit * 2]

            for link in lawyer_links[:limit]:
                name = link.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                profile_url = urljoin("https://www.avvo.com", link.get('href', ''))

                # Fetch lawyer profile
                profile_resp = self._safe_request(profile_url)
                if not profile_resp:
                    continue

                profile_soup = BeautifulSoup(profile_resp.text, 'html.parser')

                # Extract title/credentials
                title = "JD"  # Default

                # Get practice info
                practice_name_elem = profile_soup.find(
                    text=re.compile(r'Law Office|Practice|Firm')
                )
                practice_name = practice_name_elem or name

                email, phone = self._extract_contact_info(profile_resp.text, profile_url)

                # Specialties
                specialties = []
                if profile_resp.text:
                    specialties = [
                        s.strip() for s in
                        re.findall(
                            r'\b(custody|divorce|family|child support|mediation|litigation)\b',
                            profile_resp.text, re.IGNORECASE
                        )
                    ]

                prospect = Prospect(
                    name=name,
                    title=title,
                    practice_name=str(practice_name),
                    email=email,
                    phone=phone,
                    website=profile_url,
                    directory_url=profile_url,
                    specialties=list(set(specialties)) if specialties else ["family law"],
                    state=state,
                    city="",
                )

                # Validate
                website_status, _ = self._validate_website(profile_url)
                score, notes = ValidationScorer.score_prospect(
                    website_status=website_status,
                    has_email=bool(email),
                    has_phone=bool(phone),
                    content_recency='recent',
                    directory_sources=1,
                )

                prospect.validation_score = score
                prospect.validation_notes = notes

                if score >= 2:
                    prospects.append(prospect)
                    self.found_count += 1
                    print(f"  [+] {name} ({score}/5) - {email or phone or 'No contact'}")
                else:
                    print(f"  [-] {name} - validation score too low ({score}/5)")

        except Exception as e:
            print(f"  [!] Error parsing Avvo: {e}")

        return prospects[:limit]

    def search_google_therapists(
        self, state: str, city: Optional[str] = None, limit: int = 10
    ) -> List[Prospect]:
        """
        Google search for therapists matching criteria.
        Searches: "LMFT family therapist [city] site:psychologytoday.com"
        """
        location = f"{city}, {state}" if city else state
        print(f"\n[*] Google search for therapists in {location}...")
        prospects = []

        # Note: Direct Google scraping is difficult due to robots.txt and captchas.
        # This is a placeholder for API-based or manual search.
        # In production, use Google Custom Search API or hand-curate results.

        search_terms = [
            f"LMFT family therapist {location} site:psychologytoday.com",
            f"LCSW family therapy {location} site:psychologytoday.com",
            f"child therapist {location} site:psychologytoday.com",
        ]

        # For now, we'll skip Google search to avoid rate limiting.
        # Recommend: use Google Custom Search API or manual search + paste URLs
        print(f"  [!] Google search requires API key. Skipping.")

        return prospects

    def validate_prospect(self, prospect: Prospect) -> Prospect:
        """
        Re-validate a prospect and update score.
        """
        if prospect.website:
            website_status, _ = self._validate_website(prospect.website)
            score, notes = ValidationScorer.score_prospect(
                website_status=website_status,
                has_email=bool(prospect.email),
                has_phone=bool(prospect.phone),
                content_recency='recent' if website_status else 'unknown',
                directory_sources=len([prospect.directory_url]) if prospect.directory_url else 1,
                notes=prospect.validation_notes,
            )
            prospect.validation_score = score
            prospect.validation_notes = notes

        return prospect

    def run(
        self, prospect_type: str, state: str, city: Optional[str] = None,
        count: int = 10
    ) -> Tuple[int, int]:
        """
        Run research for a given prospect type.
        Returns (found, validated).
        """
        results = []

        if prospect_type.lower() == "therapist":
            results.extend(
                self.search_psychology_today(state, city=city, limit=count)
            )

        elif prospect_type.lower() == "lawyer":
            results.extend(
                self.search_avvo_lawyers(state, limit=count)
            )

        elif prospect_type.lower() == "mediator":
            # Mediators: use therapist search with "mediator" keyword
            # (they often overlap on Psychology Today)
            print(f"\n[*] Searching for family mediators in {state}...")
            print(f"  [!] Mediator-specific directories not yet implemented.")
            print(f"      Recommend: Google search + manual curation.")

        # Validate and add to database
        for prospect in results:
            prospect = self.validate_prospect(prospect)

            is_new = self.db.add_or_update(prospect)
            if is_new:
                self.validated_count += 1

        self.db.save()

        return self.found_count, self.validated_count


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="KaNun Digital Prospect Research Tool"
    )
    parser.add_argument(
        '--type',
        required=True,
        choices=['therapist', 'lawyer', 'mediator'],
        help="Prospect type to search for"
    )
    parser.add_argument(
        '--state',
        required=True,
        help="State abbreviation or name (e.g., CA, NY)"
    )
    parser.add_argument(
        '--city',
        default=None,
        help="City to search in (optional)"
    )
    parser.add_argument(
        '--count',
        type=int,
        default=20,
        help="Maximum prospects to find (default: 20)"
    )
    parser.add_argument(
        '--db',
        default='/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach/prospects.json',
        help="Path to prospect database (JSON)"
    )

    args = parser.parse_args()

    # Initialize database
    db = ProspectDatabase(args.db)

    # Run search
    searcher = ProspectSearcher(db)
    found, validated = searcher.run(
        prospect_type=args.type,
        state=args.state,
        city=args.city,
        count=args.count
    )

    # Print summary
    stats = db.get_stats()
    print("\n" + "=" * 60)
    print("RESEARCH COMPLETE")
    print("=" * 60)
    print(f"Found: {found} candidates")
    print(f"Validated & added: {validated} new prospects")
    print(f"Total in database: {stats['total']}")
    print(f"By status: {stats['by_status']}")
    print(f"By validation score: {stats['by_validation_score']}")
    print(f"\nSaved to: {args.db}")
    print(f"CSV export: {db.csv_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
