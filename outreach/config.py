"""
KaNun Digital Configuration

Centralized settings for the prospect research and outreach system.
Modify these values to customize behavior.
"""

# ============================================================================
# DIRECTORY SEARCH SETTINGS
# ============================================================================

# Psychology Today search settings
PSYCHOLOGY_TODAY_BASE_URL = "https://www.psychologytoday.com/us/therapists"
PSYCHOLOGY_TODAY_ENABLED = True

# Avvo search settings
AVVO_BASE_URL = "https://www.avvo.com"
AVVO_ENABLED = True

# Google Custom Search (requires API key)
# Get one free at: https://programmablesearchengine.google.com/
GOOGLE_SEARCH_ENABLED = False  # Set to True if you have an API key
GOOGLE_API_KEY = ""  # Your API key here
GOOGLE_SEARCH_ENGINE_ID = ""  # Your search engine ID here

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================

# Minimum validation score to add prospect to outreach queue
MIN_VALIDATION_SCORE = 2  # 1-5 scale

# Website validation
VALIDATE_WEBSITE = True
WEBSITE_TIMEOUT_SECONDS = 5
WEBSITE_ACCEPTABLE_STATUS_CODES = [200, 301, 302]

# Contact info validation
REQUIRE_EMAIL = False  # If False, phone is acceptable
REQUIRE_PHONE = False  # If False, email is acceptable
BOTH_REQUIRED = False  # If True, need both email and phone

# ============================================================================
# SEARCH & RATE LIMITING
# ============================================================================

# Delay between requests (seconds) to avoid rate limiting
REQUEST_DELAY = 1.5

# HTTP request timeout
REQUEST_TIMEOUT = 5

# User-Agent string (some sites check this)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Maximum pages to scrape per search
MAX_PAGES_PER_SEARCH = 5

# ============================================================================
# EMAIL SETTINGS
# ============================================================================

# Email sender (will be overridden when actually sending)
EMAIL_FROM_NAME = "Bren C."
EMAIL_FROM_EMAIL = "bren@kanun.digital"

# Email sequences
INITIAL_EMAIL_DAY = 1
FOLLOWUP_1_EMAIL_DAY = 5
FOLLOWUP_2_EMAIL_DAY = 12

# Subject line variants for A/B testing
USE_AB_TESTING = True
DEFAULT_SUBJECT_VARIANT = 1  # 1 or 2

# Email signature company name
COMPANY_NAME = "KaNun Digital"

# ============================================================================
# TARGET MARKETS (Customize for your outreach)
# ============================================================================

# States/cities to focus on (can expand or customize)
TARGET_STATES = [
    "CA",  # California
    "NY",  # New York
    "TX",  # Texas
    "FL",  # Florida
    "IL",  # Illinois
]

TARGET_CITIES_BY_STATE = {
    "CA": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
    "NY": ["New York City", "Buffalo", "Rochester", "Syracuse"],
    "TX": ["Austin", "Dallas", "Houston", "San Antonio"],
    "FL": ["Miami", "Tampa", "Orlando", "Jacksonville"],
    "IL": ["Chicago", "Rockford", "Springfield"],
}

# Therapist specialties to prioritize (for filtering search results)
THERAPIST_SPECIALTIES = [
    "divorce",
    "family therapy",
    "child therapy",
    "custody",
    "co-parenting",
    "family conflict",
    "children",
    "adolescent",
]

# Lawyer practice areas to prioritize
LAWYER_SPECIALTIES = [
    "family law",
    "divorce",
    "custody",
    "child support",
    "mediation",
    "co-parenting",
]

# Mediator specialties
MEDIATOR_SPECIALTIES = [
    "family mediation",
    "divorce mediation",
    "co-parenting",
    "custody mediation",
]

# ============================================================================
# DATABASE SETTINGS
# ============================================================================

# Default database paths
PROSPECTS_JSON_PATH = "/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach/prospects.json"
PROSPECTS_CSV_PATH = "/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach/prospects.csv"

# Backup database after each save
CREATE_BACKUPS = True
BACKUP_DIR = "/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach/backups"

# ============================================================================
# LOGGING & OUTPUT
# ============================================================================

# Print verbose output during research
VERBOSE = True

# Log all scraping attempts to file
LOG_SCRAPING = True
LOG_FILE = "/sessions/jolly-admiring-knuth/mnt/outputs/kanun-digital-v4/outreach/research.log"

# ============================================================================
# OUTREACH SETTINGS
# ============================================================================

# Default contact mode (email vs phone)
PREFERRED_CONTACT_METHOD = "email"  # "email" or "phone"

# Prevent duplicate outreach by email
DEDUP_BY_EMAIL = True
DEDUP_BY_PHONE = True
DEDUP_BY_NAME = False  # Names can be duplicates, so don't use this alone

# Auto-mark prospects as "skip" if they match certain patterns
AUTO_SKIP_PATTERNS = [
    "currently not accepting",
    "not available",
    "retired",
    "no longer practicing",
    "closed",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_target_locations():
    """Return list of (state, city) tuples for research."""
    locations = []
    for state in TARGET_STATES:
        cities = TARGET_CITIES_BY_STATE.get(state, [state])
        for city in cities:
            locations.append((state, city))
    return locations


def validate_config():
    """Check for configuration issues."""
    issues = []

    if not PSYCHOLOGY_TODAY_ENABLED and not AVVO_ENABLED:
        issues.append("No search directories enabled!")

    if GOOGLE_SEARCH_ENABLED and not GOOGLE_API_KEY:
        issues.append("Google search enabled but no API key provided")

    if REQUIRE_EMAIL and REQUIRE_PHONE and not BOTH_REQUIRED:
        issues.append("Conflicting email/phone requirements")

    return issues


if __name__ == "__main__":
    # Test configuration
    print("KaNun Digital Configuration")
    print("=" * 60)

    issues = validate_config()
    if issues:
        print("[!] Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[+] Configuration valid")

    print(f"\n[+] Enabled directories:")
    print(f"    Psychology Today: {PSYCHOLOGY_TODAY_ENABLED}")
    print(f"    Avvo: {AVVO_ENABLED}")
    print(f"    Google: {GOOGLE_SEARCH_ENABLED}")

    print(f"\n[+] Validation thresholds:")
    print(f"    Minimum score: {MIN_VALIDATION_SCORE}/5")
    print(f"    Require email: {REQUIRE_EMAIL}")
    print(f"    Require phone: {REQUIRE_PHONE}")

    print(f"\n[+] Target markets: {len(get_target_locations())} locations")
    for state, city in get_target_locations()[:5]:
        print(f"    {city}, {state}")
    if len(get_target_locations()) > 5:
        print(f"    ... and {len(get_target_locations()) - 5} more")

    print(f"\n[+] Email settings:")
    print(f"    From: {EMAIL_FROM_NAME} <{EMAIL_FROM_EMAIL}>")
    print(f"    Company: {COMPANY_NAME}")
    print(f"    A/B testing: {USE_AB_TESTING}")

    print("\n[+] Database paths:")
    print(f"    JSON: {PROSPECTS_JSON_PATH}")
    print(f"    CSV: {PROSPECTS_CSV_PATH}")
