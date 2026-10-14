"""Built-in seed data for 20 evidence-based public resources."""
from __future__ import annotations

from backend.app.database import SessionLocal, engine
from backend.app.models import Article, Base


ARTICLES = [
    # ── Symptoms ─────────────────────────────────────────────────────────────
    {
        "slug": "malnutrition-warning-signs",
        "title": "Early warning signs of child malnutrition",
        "topic": "Symptoms",
        "summary": "Common signs include poor weight gain, visible wasting, swelling of both feet, repeated illness, low appetite, and tiredness.",
        "body_md": "Watch growth over time, not one number alone. Seek urgent care if the child will not eat, vomits everything, has swelling of both feet, fits, fast breathing, severe dehydration, or is very sleepy.",
        "source_name": "WHO Child Growth Standards",
        "source_url": "https://www.who.int/tools/child-growth-standards",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "sam-vs-mam-difference",
        "title": "SAM vs MAM — understanding the difference",
        "topic": "Symptoms",
        "summary": "Severe acute malnutrition (SAM) needs urgent care; moderate (MAM) needs supervised feeding. Both identified by MUAC and z-scores.",
        "body_md": "Severe acute malnutrition (SAM) is defined by severe wasting (weight-for-height z-score < -3 SD), MUAC < 11.5 cm, or bilateral nutritional oedema. SAM children need immediate therapeutic feeding. Moderate acute malnutrition (MAM) is defined by WHZ between -2 and -3 SD or MUAC between 11.5 and 12.5 cm, managed with targeted supplementary feeding and close growth monitoring.",
        "source_name": "WHO",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/malnutrition",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "muac-tape-measurement",
        "title": "MUAC tape — how to measure child mid-upper arm",
        "topic": "Symptoms",
        "summary": "Red = severe, yellow = moderate, green = normal. Simple tool any parent can use at home.",
        "body_md": "Mid-upper arm circumference (MUAC) is measured midway between the shoulder and elbow on a relaxed left arm. Red (< 11.5 cm) indicates Severe Acute Malnutrition (urgent medical referral required). Yellow (11.5–12.5 cm) indicates Moderate Acute Malnutrition. Green (> 12.5 cm) indicates normal nutritional status.",
        "source_name": "UNICEF",
        "source_url": "https://www.unicef.org/nutrition/severe-acute-malnutrition",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "hidden-hunger-micronutrients",
        "title": "Hidden hunger — micronutrient deficiency signs",
        "topic": "Symptoms",
        "summary": "Iron, zinc, vitamin A deficiency show no visible wasting but cause poor immunity, blindness, delayed development.",
        "body_md": "Hidden hunger happens when a child consumes enough energy but lacks micronutrients. Iron deficiency causes weakness and developmental delay; zinc deficiency increases susceptibility to diarrhoea and pneumonia; vitamin A deficiency causes night blindness and high infectious risk.",
        "source_name": "WHO Micronutrients",
        "source_url": "https://www.who.int/health-topics/micronutrients",
        "reviewed_on": "2026-10-14",
    },

    # ── Feeding ──────────────────────────────────────────────────────────────
    {
        "slug": "feeding-6-to-23-months",
        "title": "Feeding children from 6 to 23 months",
        "topic": "Feeding",
        "summary": "Continue breastfeeding and add thick, varied foods with enough energy, protein, and micronutrients.",
        "body_md": "Start complementary foods at 6 months while continuing breastfeeding. Use thick mashed foods, add dal, egg, curd, ragi, vegetables, fruit, and a small amount of oil or ghee. Avoid watery food as the main meal.",
        "source_name": "UNICEF Infant and Young Child Feeding",
        "source_url": "https://www.unicef.org/nutrition/infant-and-young-child-feeding",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "breastfeeding-first-6-months",
        "title": "Breastfeeding — first hour and first 6 months",
        "topic": "Feeding",
        "summary": "Start within 1 hour of birth. Breast milk only for 6 months — no water, no other food needed.",
        "body_md": "Colostrum produced in the first hours provides early antibody protection. Exclusive breastfeeding for the first 6 months covers 100% of water and nutrition requirements. Avoid pre-lacteal feeds, honey, or plain water before 6 months.",
        "source_name": "WHO",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "complementary-feeding-after-6m",
        "title": "Complementary feeding after 6 months",
        "topic": "Feeding",
        "summary": "Add thick, varied foods from 6 months onward while continuing to breastfeed up to 2 years.",
        "body_md": "At 6 months, breast milk is no longer enough on its own. Introduce mashed khichdi, cooked lentils, seasonal vegetables, and mashed fruits 2-3 times daily, gradually increasing portion size and texture thickness as teeth erupt.",
        "source_name": "UNICEF Parenting",
        "source_url": "https://www.unicef.org/parenting/food-nutrition/introducing-solid-foods-your-baby",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "iron-rich-foods-children",
        "title": "Iron-rich foods for young children",
        "topic": "Feeding",
        "summary": "Lentils, eggs, meat, dark leafy greens, and iron-fortified cereals prevent anaemia and support brain growth.",
        "body_md": "Rapid brain growth requires dietary iron. Give lentils, eggs, poultry, dark leafy greens (spinach, methi), and fortified cereals. Pair plant-based iron foods with Vitamin C (lemon, orange, amla) to maximize iron absorption.",
        "source_name": "WHO",
        "source_url": "https://www.who.int/tools/child-growth-standards",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "vitamin-a-foods-supplementation",
        "title": "Vitamin A foods and supplementation",
        "topic": "Feeding",
        "summary": "Carrots, green leafy vegetables, eggs, orange fruits. Vitamin A drops given every 6 months in India via Anganwadi.",
        "body_md": "Vitamin A protects child vision, skin, and immune health. Include carrots, sweet potatoes, papaya, mangoes, green leaves, eggs, and dairy. In India, bi-annual Vitamin A liquid doses are administered free at Anganwadi centres from 9 months to 5 years.",
        "source_name": "UNICEF",
        "source_url": "https://www.unicef.org/nutrition/vitamin-micronutrient",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "feeding-sick-children",
        "title": "Feeding sick children — do not stop food",
        "topic": "Feeding",
        "summary": "During illness keep breastfeeding. Give extra feeds after recovery. Stopping food worsens malnutrition.",
        "body_md": "Never withhold food during illness. Offer frequent small feeds and continue breastfeeding. During convalescence, give an extra meal every day for at least 2 weeks to promote catch-up growth.",
        "source_name": "WHO",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/diarrhoeal-disease",
        "reviewed_on": "2026-10-14",
    },

    # ── Schemes ──────────────────────────────────────────────────────────────
    {
        "slug": "poshan-and-anganwadi-help",
        "title": "Government nutrition support in India",
        "topic": "Schemes",
        "summary": "Anganwadi centres and POSHAN services can help with growth monitoring, supplementary food, counselling, and referrals.",
        "body_md": "Ask the nearest Anganwadi worker about growth monitoring, take-home ration, nutrition counselling, immunisation days, and referral to a health centre or Nutrition Rehabilitation Centre when needed.",
        "source_name": "POSHAN Abhiyaan",
        "source_url": "https://poshanabhiyaan.gov.in/",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "icds-anganwadi-services",
        "title": "ICDS — Integrated Child Development Services",
        "topic": "Schemes",
        "summary": "Free supplementary nutrition, growth monitoring, immunisation and health education at every Anganwadi for children 0–6 years.",
        "body_md": "The Integrated Child Development Services (ICDS) scheme provides supplementary nutrition (Take-Home Ration / hot cooked meals), growth monitoring, immunization support, and non-formal preschool education at every Anganwadi center.",
        "source_name": "Govt of India WCD",
        "source_url": "https://wcd.nic.in/schemes-listing/2405",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "nrc-rehabilitation-centres",
        "title": "NRC — Nutrition Rehabilitation Centres",
        "topic": "Schemes",
        "summary": "Govt hospitals that admit SAM children for 14 days of therapeutic feeding. Ask your local doctor or Anganwadi for referral.",
        "body_md": "Nutrition Rehabilitation Centres (NRCs) are specialized inpatient units in government hospitals that provide 14-day supervised medical and therapeutic feeding for children with Severe Acute Malnutrition with complications.",
        "source_name": "NHM India",
        "source_url": "https://nhm.gov.in/index1.php?lang=1&level=2&sublinkid=1009&lid=397",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "pm-poshan-mid-day-meal",
        "title": "PM POSHAN (Mid-Day Meal Scheme)",
        "topic": "Schemes",
        "summary": "Free nutritious meals for children in government schools. Helps prevent school-age malnutrition.",
        "body_md": "PM POSHAN provides free hot cooked meals with specified calories and protein to children in government schools, reducing classroom hunger and preventing nutritional deficiencies in school-age children.",
        "source_name": "Govt of India",
        "source_url": "https://pmposhan.education.gov.in/",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "pmmvy-maternal-scheme",
        "title": "Pradhan Mantri Matru Vandana Yojana",
        "topic": "Schemes",
        "summary": "Cash benefit of ₹5,000 for pregnant and lactating mothers for first child. Supports maternal nutrition.",
        "body_md": "PMMVY provides cash incentives transferred directly to bank accounts of pregnant women and lactating mothers for health registration, institutional delivery, and child vaccination, combating low birth weight.",
        "source_name": "WCD India",
        "source_url": "https://pmmvy.wcd.gov.in/",
        "reviewed_on": "2026-10-14",
    },

    # ── Prevention ───────────────────────────────────────────────────────────
    {
        "slug": "ors-zinc-diarrhoea",
        "title": "Diarrhoea care: ORS, zinc, and continued feeding",
        "topic": "Prevention",
        "summary": "During diarrhoea, continue feeding and breastfeeding, give ORS, and ask a health worker about zinc.",
        "body_md": "Diarrhoea can quickly worsen nutrition. Keep feeding small frequent meals, continue breastfeeding, give ORS after loose stools, and seek care for blood in stool, dehydration, fever, or poor drinking.",
        "source_name": "WHO Diarrhoeal disease guidance",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/diarrhoeal-disease",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "handwashing-hygiene-prevention",
        "title": "Handwashing and hygiene to prevent malnutrition",
        "topic": "Prevention",
        "summary": "Diarrhoea causes malnutrition. Wash hands before feeding and after toilet — soap and water, 20 seconds.",
        "body_md": "Good hygiene prevents gut infections that impair nutrient absorption. Wash hands with soap and running water before feeding children, before preparing meals, and after using toilets or cleaning diapers.",
        "source_name": "UNICEF WASH",
        "source_url": "https://www.unicef.org/wash/handwashing",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "growth-monitoring-monthly",
        "title": "Growth monitoring — weigh your child every month",
        "topic": "Prevention",
        "summary": "Regular weighing catches slow weight gain early. Visit Anganwadi monthly for free growth chart update.",
        "body_md": "Growth faltering happens before visible wasting is obvious. Weighing monthly and plotting on the Mother-Child Protection (MCP) card catches slow growth early so feeding interventions can start immediately.",
        "source_name": "POSHAN Abhiyaan",
        "source_url": "https://poshanabhiyaan.gov.in/",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "anaemia-prevention-ifa",
        "title": "Anaemia prevention in children",
        "topic": "Prevention",
        "summary": "Give iron-folic acid syrup weekly to children 6 months–5 years as advised by health worker.",
        "body_md": "Under the Anemia Mukt Bharat initiative, bi-weekly Iron and Folic Acid (IFA) syrup is given to children aged 6 to 59 months through Anganwadis to prevent anaemia, fatigue, and developmental delay.",
        "source_name": "NHM WIFS Programme",
        "source_url": "https://nhm.gov.in/index1.php?lang=1&level=2&sublinkid=1043&lid=396",
        "reviewed_on": "2026-10-14",
    },
    {
        "slug": "when-to-go-to-hospital-immediately",
        "title": "When to go to hospital immediately",
        "topic": "Prevention",
        "summary": "Danger signs: child cannot eat or drink, vomiting everything, convulsions, fast breathing, very pale. Go to NRC / district hospital same day.",
        "body_md": "Immediate danger signs requiring emergency hospital transfer: 1) Inability to breastfeed or drink, 2) Vomiting everything, 3) Convulsions, 4) Fast breathing or chest in-drawing, 5) Bilateral feet swelling (oedema), 6) Unusually lethargic or unconscious.",
        "source_name": "WHO Pocket Book",
        "source_url": "https://www.who.int/publications/i/item/9789241548526",
        "reviewed_on": "2026-10-14",
    },
]


def seed_articles() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for item in ARTICLES:
            exists = db.query(Article).filter(Article.slug == item["slug"]).first()
            if not exists:
                db.add(Article(**item))
            else:
                for k, v in item.items():
                    setattr(exists, k, v)
        db.commit()
    finally:
        db.close()
