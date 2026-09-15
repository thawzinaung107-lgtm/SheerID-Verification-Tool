"""
Canva Education Teacher Document Generator
Generates UK Teacher documents for manual upload to canva.com/education

Supports:
- Employment Letter (UK school letterhead)
- Teacher ID Card (UK school staff ID)
- Teaching License (DfE QTS certificate)

Enhanced with:
- HTML templates rendered via Playwright (replaces PDF manipulation)
- Random noise injection to avoid template detection
- Slight blur and rotation for scan-like appearance
- Realistic handwritten signatures (Great Vibes font)

NOTE: Canva Education does NOT use SheerID for verification.
      You must upload documents manually at canva.com/education

Author: ThanhNguyxn
Based on: GitHub Issue #49 templates by cruzzzdev
HTML rewrite: HugeFrog24
"""

import sys
import json
import random
import asyncio
import base64
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from io import BytesIO

try:
    from PIL import Image, ImageFilter
except ImportError:
    print("[ERROR] Pillow required. Install: pip install Pillow")
    sys.exit(1)

# Import noise generator from parent module if available
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from doc_generator import add_simple_noise
except ImportError:

    def add_simple_noise(img, intensity=3):
        """Fallback: no-op noise function"""
        return img


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "assets" / "templates"


# =============================================================================
# DATA: UK SCHOOLS
# =============================================================================

DEFAULT_SCHOOLS = [
    # ============ UNITED KINGDOM ============
    {
        "country": "UK",
        "name": "Leeds Grammar School",
        "address": "Alwoodley Gates, Harrogate Road",
        "town": "Leeds",
        "postcode": "LS17 8GS",
        "phone": "0113 229 1552",
        "lea": "Leeds LEA",
        "authority": "Department for Education",
        "id_label": "Staff ID",
        "license_title": "Qualified Teacher Status",
        "license_body": "Department for Education",
    },
    {
        "country": "UK",
        "name": "Manchester Grammar School",
        "address": "Old Hall Lane",
        "town": "Manchester",
        "postcode": "M13 0XT",
        "phone": "0161 224 7201",
        "lea": "Manchester LEA",
        "authority": "Department for Education",
        "id_label": "Staff ID",
        "license_title": "Qualified Teacher Status",
        "license_body": "Department for Education",
    },
    {
        "country": "UK",
        "name": "King Edward's School",
        "address": "Edgbaston Park Road",
        "town": "Birmingham",
        "postcode": "B15 2UA",
        "phone": "0121 472 1672",
        "lea": "Birmingham LEA",
        "authority": "Department for Education",
        "id_label": "Staff ID",
        "license_title": "Qualified Teacher Status",
        "license_body": "Department for Education",
    },
    {
        "country": "UK",
        "name": "St Paul's School",
        "address": "Lonsdale Road",
        "town": "London",
        "postcode": "SW13 9JT",
        "phone": "020 8748 9162",
        "lea": "Richmond LEA",
        "authority": "Department for Education",
        "id_label": "Staff ID",
        "license_title": "Qualified Teacher Status",
        "license_body": "Department for Education",
    },
    {
        "country": "UK",
        "name": "Eton College",
        "address": "High Street",
        "town": "Windsor",
        "postcode": "SL4 6DW",
        "phone": "01753 370 100",
        "lea": "Windsor LEA",
        "authority": "Department for Education",
        "id_label": "Staff ID",
        "license_title": "Qualified Teacher Status",
        "license_body": "Department for Education",
    },
    # ============ INDIA ============
    {
        "country": "India",
        "name": "Delhi Public School, R.K. Puram",
        "address": "Sector XII, R.K. Puram",
        "town": "New Delhi",
        "postcode": "110022",
        "phone": "+91 11 2617 1277",
        "lea": "Directorate of Education, Delhi",
        "authority": "Central Board of Secondary Education",
        "id_label": "Teacher ID",
        "license_title": "B.Ed. Teaching License",
        "license_body": "National Council for Teacher Education",
    },
    {
        "country": "India",
        "name": "The Doon School",
        "address": "Maldevta Road",
        "town": "Dehradun",
        "postcode": "248007",
        "phone": "+91 135 252 6400",
        "lea": "Uttarakhand Board of School Education",
        "authority": "Central Board of Secondary Education",
        "id_label": "Teacher ID",
        "license_title": "B.Ed. Teaching License",
        "license_body": "National Council for Teacher Education",
    },
    {
        "country": "India",
        "name": "Cathedral and John Connon School",
        "address": "6, Purshottamdas Thakurdas Marg",
        "town": "Mumbai",
        "postcode": "400001",
        "phone": "+91 22 2262 3526",
        "lea": "Maharashtra State Board",
        "authority": "Council for the Indian School Certificate Examinations",
        "id_label": "Teacher ID",
        "license_title": "B.Ed. Teaching License",
        "license_body": "National Council for Teacher Education",
    },
    {
        "country": "India",
        "name": "The Shri Ram School",
        "address": "V-37, Moulsari Avenue",
        "town": "Gurugram",
        "postcode": "122002",
        "phone": "+91 124 475 6600",
        "lea": "Haryana Board of School Education",
        "authority": "Central Board of Secondary Education",
        "id_label": "Teacher ID",
        "license_title": "B.Ed. Teaching License",
        "license_body": "National Council for Teacher Education",
    },
    {
        "country": "India",
        "name": "Mayo College",
        "address": "Srinagar Road",
        "town": "Ajmer",
        "postcode": "305001",
        "phone": "+91 145 266 1226",
        "lea": "Rajasthan Board of Secondary Education",
        "authority": "Council for the Indian School Certificate Examinations",
        "id_label": "Teacher ID",
        "license_title": "B.Ed. Teaching License",
        "license_body": "National Council for Teacher Education",
    },
    # ============ INDONESIA ============
    {
        "country": "Indonesia",
        "name": "Sekolah Pelita Harapan",
        "address": "Jl. Jababeka Raya Blok F29",
        "town": "Cikarang",
        "postcode": "17550",
        "phone": "+62 21 8980 3633",
        "lea": "Dinas Pendidikan Jawa Barat",
        "authority": "Kementerian Pendidikan, Kebudayaan, Riset, dan Teknologi",
        "id_label": "Kartu Guru",
        "license_title": "Surat Izin Mengajar",
        "license_body": "Kementerian Pendidikan dan Kebudayaan",
    },
    {
        "country": "Indonesia",
        "name": "Jakarta Intercultural School",
        "address": "Jl. Terogong Raya 33",
        "town": "Jakarta Selatan",
        "postcode": "12430",
        "phone": "+62 21 769 2555",
        "lea": "Dinas Pendidikan DKI Jakarta",
        "authority": "Kementerian Pendidikan, Kebudayaan, Riset, dan Teknologi",
        "id_label": "Kartu Guru",
        "license_title": "Surat Izin Mengajar",
        "license_body": "Kementerian Pendidikan dan Kebudayaan",
    },
    {
        "country": "Indonesia",
        "name": "SMA Negeri 3 Jakarta",
        "address": "Jl. Setiabudi Barat No. 3",
        "town": "Jakarta Selatan",
        "postcode": "12910",
        "phone": "+62 21 525 4722",
        "lea": "Dinas Pendidikan DKI Jakarta",
        "authority": "Kementerian Pendidikan, Kebudayaan, Riset, dan Teknologi",
        "id_label": "Kartu Guru",
        "license_title": "Surat Izin Mengajar",
        "license_body": "Kementerian Pendidikan dan Kebudayaan",
    },
    {
        "country": "Indonesia",
        "name": "SMA Negeri 1 Denpasar",
        "address": "Jl. Kamboja No. 4",
        "town": "Denpasar",
        "postcode": "80234",
        "phone": "+62 361 226 995",
        "lea": "Dinas Pendidikan Bali",
        "authority": "Kementerian Pendidikan, Kebudayaan, Riset, dan Teknologi",
        "id_label": "Kartu Guru",
        "license_title": "Surat Izin Mengajar",
        "license_body": "Kementerian Pendidikan dan Kebudayaan",
    },
    # ============ CAMBODIA ============
    {
        "country": "Cambodia",
        "name": "Northbridge International School Cambodia",
        "address": "No. 885, Preah Norodom Boulevard",
        "town": "Phnom Penh",
        "postcode": "12301",
        "phone": "+855 23 991 591",
        "lea": "Ministry of Education, Youth and Sport",
        "authority": "Ministry of Education, Youth and Sport",
        "id_label": "Teacher ID",
        "license_title": "Teaching Permit",
        "license_body": "Ministry of Education, Youth and Sport",
    },
    {
        "country": "Cambodia",
        "name": "International School of Phnom Penh",
        "address": "No. 146, Norodom Boulevard",
        "town": "Phnom Penh",
        "postcode": "12301",
        "phone": "+855 23 213 103",
        "lea": "Ministry of Education, Youth and Sport",
        "authority": "Ministry of Education, Youth and Sport",
        "id_label": "Teacher ID",
        "license_title": "Teaching Permit",
        "license_body": "Ministry of Education, Youth and Sport",
    },
    {
        "country": "Cambodia",
        "name": "Lycée René Descartes",
        "address": "No. 90, Preah Sihanouk Boulevard",
        "town": "Phnom Penh",
        "postcode": "12207",
        "phone": "+855 23 216 179",
        "lea": "Agency for French Education Abroad",
        "authority": "Ministry of Education, Youth and Sport",
        "id_label": "Teacher ID",
        "license_title": "Teaching Permit",
        "license_body": "Ministry of Education, Youth and Sport",
    },
    {
        "country": "Cambodia",
        "name": "Western International School of Phnom Penh",
        "address": "No. 20, Street 598",
        "town": "Phnom Penh",
        "postcode": "12102",
        "phone": "+855 23 640 6363",
        "lea": "Ministry of Education, Youth and Sport",
        "authority": "Ministry of Education, Youth and Sport",
        "id_label": "Teacher ID",
        "license_title": "Teaching Permit",
        "license_body": "Ministry of Education, Youth and Sport",
    },
]

TEACHING_POSITIONS = [
    "Head of Drama Department",
    "Head of English Department",
    "Head of Mathematics Department",
    "Head of Science Department",
    "Head of History Department",
    "Head of Geography Department",
    "Head of Modern Languages",
    "Head of Art Department",
    "Head of Music Department",
    "Head of PE Department",
    "Deputy Head Teacher",
    "Senior Teacher",
    "Class Teacher",
    "Subject Leader - English",
    "Subject Leader - Mathematics",
    "Year Group Leader",
]

NAME_POOLS = {
    "UK": {
        "first": [
            "James", "Oliver", "Harry", "George", "Noah", "Jack", "Charlie", "Oscar",
            "William", "Henry", "Thomas", "Alfie", "Joshua", "Leo", "Archie", "Ethan",
            "Emma", "Olivia", "Amelia", "Isla", "Ava", "Mia", "Emily", "Isabella",
            "Sophia", "Grace", "Lily", "Chloe", "Ella", "Charlotte", "Sophie", "Alice",
        ],
        "last": [
            "Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans",
            "Wilson", "Thomas", "Roberts", "Johnson", "Lewis", "Walker", "Robinson",
            "Wood", "Thompson", "White", "Watson", "Jackson", "Wright", "Green",
            "Harris", "Cooper", "King",
        ],
    },
    "India": {
        "first": [
            "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Arnav", "Ayaan",
            "Krishna", "Ishaan", "Shaurya", "Atharv", "Darsh", "Kabir", "Rohan",
            "Aadhya", "Ananya", "Diya", "Saanvi", "Aaradhya", "Navya", "Myra",
            "Sara", "Ira", "Ahana", "Siya", "Pari", "Kavya", "Anvi", "Mira",
        ],
        "last": [
            "Sharma", "Kumar", "Singh", "Patel", "Gupta", "Reddy", "Nair", "Rao",
            "Iyer", "Desai", "Joshi", "Shah", "Mehta", "Agarwal", "Verma",
            "Yadav", "Malhotra", "Kapoor", "Banerjee", "Das", "Chowdhury",
        ],
    },
    "Indonesia": {
        "first": [
            "Budi", "Ahmad", "Muhammad", "Agus", "Hendra", "Rizky", "Dedi", "Andi",
            "Yusuf", "Adi", "Bayu", "Eko", "Fajar", "Hadi", "Indra", "Joko",
            "Siti", "Dewi", "Putri", "Nur", "Ayu", "Rina", "Maya", "Lestari",
            "Ani", "Yuni", "Fitri", "Wulan", "Ratna", "Sari", "Intan", "Mega",
        ],
        "last": [
            "Santoso", "Wijaya", "Sari", "Susanto", "Saputra", "Kusuma", "Setiawan",
            "Lestari", "Hidayat", "Utama", "Pratama", "Putra", "Wati", "Handayani",
            "Cahyadi", "Mahendra", "Purnama", "Suryadi", "Ramadhan", "Firmansyah",
        ],
    },
    "Cambodia": {
        "first": [
            "Sokha", "Dara", "Sopheap", "Bopha", "Chantha", "Srey", "Kunthea",
            "Rathanak", "Sovann", "Visal", "Sok", "Chhay", "Khemara", "Pisey",
            "Sophorn", "Leakhena", "Maly", "Pich", "Sambath", "Vannak", "Thida",
            "Narith", "Socheata", "Sopheap",
        ],
        "last": [
            "Sok", "Chan", "Chea", "Kim", "Lay", "Lim", "Mao", "Meas", "Ngin",
            "Ou", "Pen", "Phan", "Prak", "Ros", "Sam", "San", "Sim", "Sok",
            "Suon", "Thach", "Thai", "Touch", "Vann", "Yem",
        ],
    },
}


UK_FIRST_NAMES = NAME_POOLS["UK"]["first"]
UK_LAST_NAMES = NAME_POOLS["UK"]["last"]



class SchoolDatabase:
    """International schools database with search and random selection."""

    def __init__(self):
        self.schools = self._load()

    def _load(self) -> List[Dict]:
        json_path = DATA_DIR / "schools.json"
        if json_path.exists():
            try:
                return json.loads(json_path.read_text())
            except Exception:
                pass
        return DEFAULT_SCHOOLS

    def random(self) -> Dict:
        return random.choice(self.schools)

    def search(self, query: str) -> Optional[Dict]:
        query_lower = query.lower()
        for school in self.schools:
            if query_lower in school["name"].lower():
                return school
        return None

    def list_names(self) -> List[str]:
        return [s["name"] for s in self.schools]

    def list_by_country(self) -> Dict[str, List[Dict]]:
        grouped: Dict[str, List[Dict]] = {}
        for school in self.schools:
            grouped.setdefault(school.get("country", "Other"), []).append(school)
        return grouped


# =============================================================================
# DATA GENERATORS
# =============================================================================


def generate_name(country: str = "UK") -> Tuple[str, str]:
    pool = NAME_POOLS.get(country, NAME_POOLS["UK"])
    return random.choice(pool["first"]), random.choice(pool["last"])


def generate_dob(min_age: int = 28, max_age: int = 55, country: str = "UK") -> str:
    """Generate DOB in country-appropriate format."""
    age = random.randint(min_age, max_age)
    year = datetime.now().year - age
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    if country == "Indonesia":
        return f"{day:02d}-{month:02d}-{year}"
    return f"{day:02d}/{month:02d}/{year}"


def generate_staff_id() -> str:
    return f"STF-{random.randint(2020, 2025)}-{random.randint(100000, 999999)}"


def generate_trn() -> str:
    """Generate Teacher Reference Number."""
    return f"{random.randint(1000000, 9999999)}"


def generate_data_controller_no() -> str:
    return f"Z{random.randint(1000000, 9999999)}"


# =============================================================================
# TEMPLATE ENGINE
# =============================================================================


def load_template(name: str) -> str:
    """Load HTML template from file."""
    path = TEMPLATES_DIR / f"{name}.html"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def load_photo_base64() -> str:
    """Load a random employee photo as base64 data URL, or return placeholder."""
    photo_paths = sorted(TEMPLATES_DIR.glob("employee*.png"))
    if not photo_paths:
        # Fallback to legacy single file
        photo_paths = [TEMPLATES_DIR / "employee.png"]

    existing = [p for p in photo_paths if p.exists()]
    if not existing:
        return "PHOTO"

    photo_path = random.choice(existing)
    b64 = base64.b64encode(photo_path.read_bytes()).decode("utf-8")
    return f'<img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;border-radius:3px;">'


def load_chip_base64() -> str:
    """Load ID card chip image as base64 data URL."""
    chip_path = TEMPLATES_DIR / "chip.png"
    if chip_path.exists():
        b64 = base64.b64encode(chip_path.read_bytes()).decode("utf-8")
        return f'<img src="data:image/png;base64,{b64}">'
    return ""


def render_employment_letter(first: str, last: str, school: Dict, position: str) -> str:
    """Render country-aware employment letter template with data."""
    country = school.get("country", "UK")
    template = load_template(f"employment_letter_{country.lower()}") if (TEMPLATES_DIR / f"employment_letter_{country.lower()}.html").exists() else load_template("employment_letter")

    staff_id = generate_staff_id()
    start_date = (datetime.now() - timedelta(days=random.randint(180, 1800))).strftime(
        "%d %B %Y"
    )

    # Parse address
    addr_parts = school["address"].split(",")
    addr_line1 = addr_parts[0].strip()
    addr_line2 = f"{addr_parts[1].strip()}<br>" if len(addr_parts) > 1 else ""

    # Determine department from position
    if "Language" in position:
        department = "Modern Foreign Languages"
    else:
        department = position.replace("Head of ", "").replace(" Department", "")

    # Country-specific signature titles and labels
    signatory_titles = {
        "UK": ("Headteacher", "Disclosure and Barring Service", "United Kingdom"),
        "India": ("Principal", "Police Verification & CBSE Background Check", "India"),
        "Indonesia": ("Kepala Sekolah", "Surat Keterangan Catatan Kepolisian", "Indonesia"),
        "Cambodia": ("School Director", "Ministry of Education Background Check", "Cambodia"),
    }
    sig_title, bg_check, country_name = signatory_titles.get(country, signatory_titles["UK"])

    return template.format(
        school_name=school["name"],
        address_line1=addr_line1,
        address_line2=addr_line2,
        address_full=school["address"],
        town=school["town"],
        postcode=school["postcode"],
        phone=school["phone"],
        current_date=datetime.now().strftime("%d %B %Y"),
        year=datetime.now().year,
        staff_id=staff_id,
        full_name=f"{first} {last}",
        full_name_upper=f"{first.upper()} {last.upper()}",
        start_date=start_date,
        position=position,
        department=department,
        data_controller=generate_data_controller_no(),
        authority=school.get("authority", "Department for Education"),
        lea=school.get("lea", ""),
        sig_title=sig_title,
        bg_check=bg_check,
        country_name=country_name,
        # Random signature rotation for realistic hand-signed look
        signature_rotation=round(random.uniform(-3, 3), 1),
    )


def render_teacher_id(
    first: str, last: str, school: Dict, position: str, dob: str
) -> str:
    """Render country-aware teacher ID card template with data."""
    country = school.get("country", "UK")
    template = load_template(f"teacher_id_{country.lower()}") if (TEMPLATES_DIR / f"teacher_id_{country.lower()}.html").exists() else load_template("teacher_id")

    # Extract short position for badge
    if " - " in position:
        pos_short = position.upper().split(" - ")[-1]
    else:
        pos_short = position.upper().replace("HEAD OF ", "").replace(" DEPARTMENT", "")

    # Country-specific date formats
    date_fmt = "%d/%m/%Y" if country in {"UK", "India", "Cambodia"} else "%d-%m-%Y"

    return template.format(
        school_name_upper=school["name"].upper(),
        full_name_upper=f"{first.upper()} {last.upper()}",
        position_short=pos_short,
        dob=dob,
        # Issue date set to ~2 weeks ago to look established, not freshly minted
        issue_date=(datetime.now() - timedelta(days=random.randint(10, 20))).strftime(date_fmt),
        expiry_date=(datetime.now() + timedelta(days=3 * 365)).strftime(date_fmt),
        staff_id=generate_staff_id(),
        lea=school.get("lea", f"{school['town']} LEA"),
        country=country,
        id_label=school.get("id_label", "Staff ID"),
        authority=school.get("authority", "Department for Education"),
        photo_html=load_photo_base64(),
        chip_html=load_chip_base64(),
    )


def render_teaching_license(first: str, last: str, school: Dict) -> str:
    """Render country-aware teaching license/certificate template with data."""
    country = school.get("country", "UK")
    template = load_template(f"teaching_license_{country.lower()}") if (TEMPLATES_DIR / f"teaching_license_{country.lower()}.html").exists() else load_template("teaching_license")

    trn = generate_trn()
    award_date = (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime(
        "%d %B %Y"
    )

    license_id_prefixes = {
        "UK": "QTS",
        "India": "NCTE",
        "Indonesia": "SIM",
        "Cambodia": "TP",
    }
    prefix = license_id_prefixes.get(country, "LIC")

    return template.format(
        full_name=f"{first} {last}",
        trn=trn,
        trn_short=trn[:6],
        award_date=award_date,
        year=datetime.now().year,
        country=country,
        license_title=school.get("license_title", "Qualified Teacher Status"),
        license_body=school.get("license_body", "Department for Education"),
        license_id=f"{prefix}/{datetime.now().year}/{trn[:6]}",
    )


# =============================================================================
# RENDERING ENGINE
# =============================================================================


async def html_to_png(html: str, width: int = 595, height: int = None) -> bytes:
    """Render HTML to PNG using Playwright."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[ERROR] Playwright required. Install:")
        print("   pip install playwright")
        print("   playwright install chromium")
        sys.exit(1)

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": width, "height": height or 842}
            )

            await page.set_content(html)
            await page.wait_for_load_state("networkidle")

            # Auto-detect content height if not specified
            if height is None:
                content_height = await page.evaluate("document.body.scrollHeight")
                await page.set_viewport_size(
                    {"width": width, "height": content_height + 50}
                )

            screenshot = await page.screenshot(type="png", full_page=True)
            return screenshot
        finally:
            if browser:
                await browser.close()


def apply_anti_detection(png_bytes: bytes, max_rotation: float = 2.0) -> bytes:
    """Add noise, slight blur, and rotation to avoid template detection.

    Args:
        png_bytes: Raw PNG image bytes
        max_rotation: Maximum rotation angle in degrees (use lower values for letters)
    """
    img = Image.open(BytesIO(png_bytes))

    if img.mode != "RGB":
        img = img.convert("RGB")

    # Add subtle noise
    img = add_simple_noise(img, intensity=random.randint(2, 4))

    # Occasional slight blur
    if random.random() > 0.6:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3))

    # Random rotation to simulate scan alignment (varies by document type)
    rotation_angle = random.uniform(-max_rotation, max_rotation)
    img = img.rotate(
        rotation_angle,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        fillcolor=(255, 255, 255),
    )

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# =============================================================================
# DOCUMENT GENERATORS
# =============================================================================


async def generate_employment_letter(
    first: str, last: str, school: Dict, position: str
) -> bytes:
    """Generate employment letter as PNG."""
    html = render_employment_letter(first, last, school, position)
    png = await html_to_png(html, width=595, height=842)
    # Letters are placed carefully in scanner - minimal rotation
    return apply_anti_detection(png, max_rotation=0.75)


async def generate_teacher_id(
    first: str, last: str, school: Dict, position: str, dob: str
) -> bytes:
    """Generate teacher ID card as PNG."""
    html = render_teacher_id(first, last, school, position, dob)
    png = await html_to_png(html, width=380, height=260)
    # Small cards are harder to align - more rotation
    return apply_anti_detection(png, max_rotation=2.0)


async def generate_teaching_license(first: str, last: str, school: Dict) -> bytes:
    """Generate teaching license (QTS certificate) as PNG."""
    html = render_teaching_license(first, last, school)
    png = await html_to_png(html, width=560, height=780)
    # Certificate - moderate rotation
    return apply_anti_detection(png, max_rotation=1.0)


# =============================================================================
# CLI
# =============================================================================


async def main():
    import argparse

    # Fix Unicode output on Windows (cp1252 can't encode Vietnamese, etc.)
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            # Python < 3.7 fallback
            import io

            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf-8", errors="replace"
            )

    print()
    print("=" * 62)
    print("   Canva Education - UK Teacher Document Generator")
    print("=" * 62)
    print()
    print("   NOTE: Canva does NOT use SheerID for teacher verification.")
    print("   You must upload documents manually at: canva.com/education")
    print()

    parser = argparse.ArgumentParser(
        description="Generate UK Teacher documents for Canva Education"
    )
    parser.add_argument(
        "--doc-type",
        "-d",
        choices=["employment_letter", "teacher_id", "teaching_license", "all"],
        default="all",
        help="Document type to generate",
    )
    parser.add_argument("--name", "-n", help="Teacher name (format: 'First Last')")
    parser.add_argument("--school", "-s", help="School name (partial match)")
    parser.add_argument("--position", "-p", help="Teaching position")
    parser.add_argument(
        "--list-schools", action="store_true", help="List available schools"
    )
    args = parser.parse_args()

    schools = SchoolDatabase()

    # List schools mode
    if args.list_schools:
        print("   Available UK Schools:")
        for i, name in enumerate(schools.list_names(), 1):
            print(f"      {i}. {name}")
        return

    # Select school first so name generation can match country
    if args.school:
        school = schools.search(args.school)
        if not school:
            print(f"   [ERROR] School '{args.school}' not found. Use --list-schools")
            return
    else:
        school = schools.random()

    # Parse or generate data
    if args.name:
        parts = args.name.split()
        first, last = parts[0], parts[-1] if len(parts) > 1 else parts[0]
    else:
        first, last = generate_name(school.get("country", "UK"))

    position = args.position or random.choice(TEACHING_POSITIONS)
    dob = generate_dob(country=school.get("country", "UK"))

    print(f"   Teacher: {first} {last}")
    print(f"   School: {school['name']}")
    print(f"   Position: {position}")
    print(f"   DOB: {dob}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Determine which documents to generate
    if args.doc_type == "all":
        doc_types = ["employment_letter", "teacher_id", "teaching_license"]
    else:
        doc_types = [args.doc_type]

    # Generate documents
    for doc_type in doc_types:
        try:
            print(f"   > Generating {doc_type.replace('_', ' ').title()}...")

            if doc_type == "employment_letter":
                doc = await generate_employment_letter(first, last, school, position)
            elif doc_type == "teacher_id":
                doc = await generate_teacher_id(first, last, school, position, dob)
            else:
                doc = await generate_teaching_license(first, last, school)

            output_path = OUTPUT_DIR / f"{doc_type}_{first}_{last}.png"
            output_path.write_bytes(doc)
            print(f"     [OK] Saved: {output_path.name} ({len(doc) / 1024:.1f} KB)")

        except Exception as e:
            print(f"     [ERROR] {e}")

    print()
    print("-" * 62)
    print("   Output files saved to: ./output/")
    print()
    print("   Next steps:")
    print("   1. Go to https://canva.com/education")
    print("   2. Click 'Get Verified' or 'I'm a Teacher'")
    print("   3. Upload one of the generated documents")
    print("   4. Wait 24-48 hours for review")
    print("-" * 62)


if __name__ == "__main__":
    asyncio.run(main())
