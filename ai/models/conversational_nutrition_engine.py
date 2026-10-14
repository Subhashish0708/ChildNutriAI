"""
=============================================================================
Conversational Pediatric Nutrition Decision-Support Engine - ChildNutri AI
=============================================================================
Algorithm: Deterministic Rule-Based Conversational Nutrition Decision-Support
Clinical Framework: WHO 2023 Complementary Feeding Guidelines + UNICEF IYCF + CMAM

Key Principles:
  1. ASK -> UNDERSTAND -> ANALYZE -> ASK MISSING INFORMATION -> PERSONALIZE -> EXPLAIN -> RECOMMEND -> MONITOR
  2. Ask only missing information (never re-ask known child profile/assessment data)
  3. Structured 24-Hour Food Recall mapped to WHO 8 Food Groups
  4. MDD Scorecard: strictly distinguishes "Not assessed yet" from zero (NEVER displays 0/8 when unassessed)
  5. Age-Aware Feeding: <6m exclusive breastfeeding on demand, 6-23m complementary feeding, 24-59m family diet
  6. Non-causal explanation language ("may contribute" / "may be associated with", never "caused by")
  7. Strict Clinical Safety Override for SAM/Edema/High-Risk (non-prescriptive, no autonomous RUTF/drug dosing)
  8. Every recommendation states "WHY" based on the child's actual assessment and gaps
  9. Pantry-constrained recipes & nutritionally equivalent meal substitutions
 10. 10-Part Human-Like Structured Explanation (Section 28)
=============================================================================
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Set
from datetime import date, datetime

# ---------------------------------------------------------------------------
# WHO 8 Food Groups (UNICEF / WHO IYCF Indicator)
# ---------------------------------------------------------------------------
WHO_8_FOOD_GROUPS = [
    {"id": 1, "code": "breastmilk", "name": "Breast milk", "desc": "Continued on demand up to 2 years or beyond"},
    {"id": 2, "code": "grains", "name": "Grains, roots, tubers and plantains", "desc": "Rice, wheat, ragi, suji, poha, potato, sweet potato"},
    {"id": 3, "code": "pulses", "name": "Pulses, nuts and seeds", "desc": "Yellow moong, masoor dal, chana, sattu, besan, groundnut/peanut paste"},
    {"id": 4, "code": "dairy", "name": "Dairy products", "desc": "Curd/yogurt, pasteurized milk, fresh paneer, chaas"},
    {"id": 5, "code": "flesh", "name": "Flesh foods", "desc": "Finely minced chicken, fish, tender meat"},
    {"id": 6, "code": "eggs", "name": "Eggs", "desc": "Hard-boiled mashed egg yolk, whole boiled egg"},
    {"id": 7, "code": "vita", "name": "Vitamin-A-rich fruits and vegetables", "desc": "Carrot, pumpkin, papaya, mango, dark leafy greens/spinach, methi"},
    {"id": 8, "code": "other", "name": "Other fruits and vegetables", "desc": "Banana, apple, chikoo, guava, green beans, bottle gourd, tomato"},
]

# ---------------------------------------------------------------------------
# Vocabulary mapping for 24-Hour Food Recall parsing to WHO Food Groups
# ---------------------------------------------------------------------------
FOOD_VOCABULARY_MAP: Dict[int, List[str]] = {
    1: [
        "breast milk", "breastmilk", "breastfeed", "breastfeeding", "nursing",
        "mother's milk", "fed at breast", "exclusive breastfeeding"
    ],
    2: [
        "rice", "chawal", "bhat", "wheat", "gehun", "atta", "roti", "chapati",
        "phulka", "paratha", "poha", "flattened rice", "aval", "ragi",
        "finger millet", "nachni", "suji", "sooji", "semolina", "rawa",
        "potato", "aloo", "sweet potato", "shakarkandi", "khichdi", "idli",
        "dosa", "oats", "oatmeal", "cereal", "porridge", "bread", "upma",
        "tapioca", "yam", "plantain", "raw banana", "maize", "corn"
    ],
    3: [
        "dal", "daal", "lentil", "moong", "yellow moong", "masoor", "red lentil",
        "toor", "arhar", "urad", "chana", "bengal gram", "chickpea", "sattu",
        "besan", "gram flour", "peanut", "groundnut", "moongfali", "nuts",
        "seeds", "sesame", "til", "beans", "rajma", "kidney beans", "soya",
        "soybean", "sprouts", "lentils"
    ],
    4: [
        "milk", "doodh", "cow milk", "curd", "dahi", "yogurt", "paneer",
        "cottage cheese", "cheese", "dairy", "chaas", "buttermilk", "lassi",
        "chenna", "kheer"
    ],
    5: [
        "chicken", "murgh", "meat", "mutton", "gosht", "fish", "machhli",
        "flesh", "prawn", "liver", "kaleji", "poultry", "seafood"
    ],
    6: [
        "egg", "eggs", "anda", "boiled egg", "egg yolk", "omelette",
        "scrambled egg", "poached egg"
    ],
    7: [
        "carrot", "gajar", "pumpkin", "kaddu", "sitaphal", "papaya", "papita",
        "mango", "aam", "spinach", "palak", "dark leafy greens", "greens",
        "saag", "methi", "fenugreek leaves", "drumstick leaves", "moringa",
        "sweet potato (orange)", "apricot", "cantaloupe", "ripe papaya"
    ],
    8: [
        "banana", "kela", "apple", "seb", "chikoo", "sapota", "guava", "amrood",
        "green beans", "french beans", "beans", "bottle gourd", "lauki",
        "doodhi", "ghiya", "tomato", "tamatar", "pear", "nashpati", "orange",
        "santra", "watermelon", "tarbooz", "pomegranate", "anar", "cucumber",
        "kheera", "ridge gourd", "turai", "cauliflower", "gobi", "cabbage",
        "patta gobi", "peas", "matar", "fruit", "vegetables", "veggies"
    ],
}

# Permitted basic staples for pantry cooking
PERMITTED_BASIC_PREP = {
    "water", "clean drinking water", "boiled water", "cooking oil", "vegetable oil",
    "mustard oil", "ghee", "clarified butter", "cumin", "jeera", "turmeric",
    "haldi", "salt", "pinch of salt"
}

# ---------------------------------------------------------------------------
# Comprehensive Food Database with Nutrient Tags, Textures, and Age Appropriateness
# ---------------------------------------------------------------------------
MASTER_FOOD_CATALOG: List[Dict[str, Any]] = [
    # BREAKFAST
    {
        "id": "b_poha_egg",
        "slot": "breakfast",
        "title": "Soft Vegetable Poha with Boiled Egg",
        "desc": "Steamed flattened rice cooked soft with turmeric, finely grated carrots, and mashed boiled egg yolk.",
        "groups": [2, 6, 7],
        "required_ingredients": ["poha", "egg", "carrot"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "egg_vegetarian",
        "texture": "Soft moist mash / Finger food",
        "age_min_months": 6,
        "allergens": ["egg"],
        "prep_steps": [
            "Rinse poha thoroughly in clean drinking water until softened.",
            "Lightly sauté grated carrots in 1/2 tsp vegetable oil or ghee with cumin and turmeric.",
            "Add softened poha with 2 tablespoons water and cook on low heat for 2 minutes until tender.",
            "Boil one egg until hard (10 mins). Peel and mash yolk (or whole egg for >9 months) with a fork.",
            "Mix together and serve at comfortable temperature."
        ],
        "choking_warning": "Ensure carrots are grated very fine or boiled soft. Mash egg thoroughly without large chunks."
    },
    {
        "id": "b_ragi_porridge",
        "slot": "breakfast",
        "title": "Ragi (Finger Millet) Porridge with Milk",
        "desc": "Traditional calcium-rich ragi flour cooked tender with boiled milk, mashed ripe banana, and ghee.",
        "groups": [2, 4, 8],
        "required_ingredients": ["ragi", "milk", "banana"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Smooth semi-thick porridge",
        "age_min_months": 6,
        "allergens": ["dairy"],
        "prep_steps": [
            "Dissolve 2 tablespoons ragi flour in 1/2 cup clean drinking water without lumps.",
            "Cook over medium heat, stirring continuously until the mixture thickens and turns glossy (4-5 mins).",
            "Add 1/4 cup boiled warm milk and 1/2 teaspoon ghee.",
            "Stir in 2 tablespoons thoroughly mashed ripe banana for gentle natural sweetness."
        ],
        "choking_warning": "Cook thoroughly to avoid raw starch discomfort. Porridge should be thick enough to stay on a spoon."
    },
    {
        "id": "b_idli_dal",
        "slot": "breakfast",
        "title": "Steamed Idli with Moong Dal Stew",
        "desc": "Fermented steamed rice-lentil cake thoroughly crumbled and soaked in warm yellow moong dal stew.",
        "groups": [2, 3],
        "required_ingredients": ["rice", "dal"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Soft soaked mash",
        "age_min_months": 6,
        "allergens": [],
        "prep_steps": [
            "Cook yellow moong dal until completely soft and tender with a pinch of turmeric and cumin.",
            "Steam soft idli (made from fermented rice and dal batter).",
            "Crumble half to one idli into a shallow feeding bowl.",
            "Pour warm dal stew over the crumbled idli, allow it to soak for 2 minutes, and mash with clean fork."
        ],
        "choking_warning": "Ensure idli is completely soaked and mashed soft; avoid dry crumbly pieces."
    },
    {
        "id": "b_suji_upma",
        "slot": "breakfast",
        "title": "Soft Semolina (Suji) Vegetable Porridge",
        "desc": "Roasted semolina cooked soft with finely grated carrots and vegetable oil or ghee for morning energy.",
        "groups": [2, 7],
        "required_ingredients": ["suji", "carrot"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Soft moist grain porridge",
        "age_min_months": 7,
        "allergens": ["gluten"],
        "prep_steps": [
            "Dry-roast 2 tablespoons semolina (suji) in a pan until warm (do not brown).",
            "Heat 1/2 tsp oil/ghee, lightly sauté finely grated carrot with a pinch of cumin.",
            "Add 3/4 cup clean water and bring to a gentle boil.",
            "Gradually pour in roasted suji while stirring continuously to prevent lumps.",
            "Simmer covered on low heat for 3-4 minutes until thick, soft, and moist."
        ],
        "choking_warning": "Avoid adding whole mustard seeds, hard nuts, or whole curry leaves for infants."
    },
    {
        "id": "b_roti_paneer",
        "slot": "breakfast",
        "title": "Soft Whole Wheat Roti with Fresh Paneer",
        "desc": "Whole wheat chapati soaked soft in warm boiled milk or thin dal and blended with fresh crumbled paneer.",
        "groups": [2, 4],
        "required_ingredients": ["wheat", "paneer", "milk"],
        "cost_band": "₹₹",
        "budget_tier": "standard",
        "diet": "vegetarian",
        "texture": "Soft soaked shreds / Chewy mash",
        "age_min_months": 9,
        "allergens": ["gluten", "dairy"],
        "prep_steps": [
            "Tear soft whole-wheat chapati into tiny, bite-sized pieces into a warm bowl.",
            "Pour 1/3 cup warm boiled milk or light dal stew over the roti pieces.",
            "Allow to soak for 3-4 minutes until completely soft and sponge-like.",
            "Mix in 1-2 tablespoons freshly crumbled cottage cheese (paneer) for protein and calcium."
        ],
        "choking_warning": "Never give dry, hard, or rubbery roti edges. Ensure roti is thoroughly softened."
    },

    # LUNCH
    {
        "id": "l_dal_khichdi",
        "slot": "lunch",
        "title": "Yellow Moong Dal Khichdi with Carrots & Spinach",
        "desc": "Balanced grain-legume combination of soft rice and yellow moong dal cooked with tender carrots and spinach.",
        "groups": [2, 3, 7],
        "required_ingredients": ["rice", "dal", "carrot", "spinach"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Thick moist porridge / Soft mash",
        "age_min_months": 6,
        "allergens": [],
        "prep_steps": [
            "Wash 2 tablespoons white rice and 2 tablespoons split yellow moong dal thoroughly.",
            "Add finely chopped spinach and grated carrot with 1 cup clean water, pinch of turmeric and cumin.",
            "Pressure-cook for 3-4 whistles until very soft and easily mashable.",
            "Mash with the back of a spoon, add 1/2 teaspoon ghee or vegetable oil to increase energy density."
        ],
        "choking_warning": "Ensure spinach leaves are finely shredded and carrot is cooked completely tender."
    },
    {
        "id": "l_curd_rice",
        "slot": "lunch",
        "title": "Soft Rice with Fresh Curd & Boiled Potato",
        "desc": "Cooked white rice mashed soft with fresh unsweetened curd and boiled potato for gentle digestion and energy.",
        "groups": [2, 4],
        "required_ingredients": ["rice", "curd", "potato"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Cool soft mash",
        "age_min_months": 7,
        "allergens": ["dairy"],
        "prep_steps": [
            "Cook white rice soft (slightly overcooked with extra water).",
            "Mash warm cooked rice with boiled peeled potato using a clean fork.",
            "Let cool to room temperature, then mix with 3 tablespoons fresh unsweetened curd.",
            "Add a pinch of roasted cumin powder for taste and digestion."
        ],
        "choking_warning": "Use soft well-cooked rice; do not give cold curd straight from the refrigerator."
    },
    {
        "id": "l_chana_rice",
        "slot": "lunch",
        "title": "Mashed Bengal Gram (Chana) with Rice & Pumpkin",
        "desc": "Bengal gram cooked soft, mashed with rice and sweet pumpkin for plant protein, iron, and vitamin A.",
        "groups": [2, 3, 7],
        "required_ingredients": ["chana", "rice", "pumpkin"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Coarse soft mash",
        "age_min_months": 9,
        "allergens": [],
        "prep_steps": [
            "Soak split Bengal gram (chana dal) for 2 hours and pressure cook until completely tender.",
            "Steam peeled pumpkin cubes until fork-tender.",
            "Combine cooked chana dal, soft rice, and steamed pumpkin in a feeding bowl.",
            "Mash together with 1/2 tsp cooking oil or ghee and a pinch of roasted cumin."
        ],
        "choking_warning": "Never offer whole unmashed chickpeas/chana to children under 3 years due to severe choking hazard."
    },
    {
        "id": "l_chicken_khichdi",
        "slot": "lunch",
        "title": "Soft Minced Chicken & Rice Khichdi with Carrots",
        "desc": "Finely minced tender chicken simmered soft with rice, yellow dal, and carrots for bioavailable iron and zinc.",
        "groups": [2, 3, 5, 7],
        "required_ingredients": ["chicken", "rice", "dal", "carrot"],
        "cost_band": "₹₹",
        "budget_tier": "standard",
        "diet": "non_vegetarian",
        "texture": "Soft savoury porridge",
        "age_min_months": 9,
        "allergens": [],
        "prep_steps": [
            "Finely mince boneless fresh chicken breast or thigh (check carefully for bone fragments).",
            "Simmer minced chicken with soaked rice, moong dal, grated carrot, cumin, and turmeric in 1.5 cups water.",
            "Cook until chicken is tender and shreddable and grains are soft.",
            "Mash to a soft, lump-free consistency before feeding."
        ],
        "choking_warning": "Inspect meticulously to guarantee zero bone splinters. Mince finely; avoid rubbery chunks."
    },
    {
        "id": "l_fish_rice",
        "slot": "lunch",
        "title": "Flaked Fish Stew with Mashed Rice & Gourd",
        "desc": "Fresh deboned white fish gently simmered with bottle gourd and mashed rice for bioavailable protein and omega fatty acids.",
        "groups": [2, 5, 8],
        "required_ingredients": ["fish", "rice", "bottle gourd"],
        "cost_band": "₹₹",
        "budget_tier": "standard",
        "diet": "non_vegetarian",
        "texture": "Gentle moist mash",
        "age_min_months": 9,
        "allergens": ["fish"],
        "prep_steps": [
            "Steam or gently poach fresh fish fillet with turmeric and cumin until fully cooked.",
            "Carefully flake with clean fingers, feeling twice for any tiny bones or spines.",
            "Combine with peeled soft-cooked bottle gourd and mashed warm rice.",
            "Mix with a spoonful of warm broth."
        ],
        "choking_warning": "CRITICAL: Multiple finger-checks for fish bones. Offer small bites with supervision."
    },

    # SNACK
    {
        "id": "s_banana_curd",
        "slot": "snack",
        "title": "Ripe Banana Mash with Fresh Curd",
        "desc": "Naturally sweet ripe banana mashed smoothly with fresh curd for dietary potassium, calcium, and probiotics.",
        "groups": [4, 8],
        "required_ingredients": ["banana", "curd"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Smooth spoonable puree",
        "age_min_months": 6,
        "allergens": ["dairy"],
        "prep_steps": [
            "Peel half a fully ripe yellow banana with brown sugar spots.",
            "Mash thoroughly with a clean fork until silky smooth with no hard lumps.",
            "Fold in 2-3 tablespoons fresh unsweetened curd/dahi at room temperature.",
            "Serve immediately to prevent oxidation/discoloration."
        ],
        "choking_warning": "Ensure banana is ripe and mashed; never offer whole banana chunks or rounds to infants."
    },
    {
        "id": "s_papaya_puree",
        "slot": "snack",
        "title": "Mashed Fresh Papaya",
        "desc": "Fresh ripe papaya peeled, seeded, and fork-mashed for provitamin A carotenoids and gentle digestive fiber.",
        "groups": [7],
        "required_ingredients": ["papaya"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Silky fruit mash",
        "age_min_months": 6,
        "allergens": [],
        "prep_steps": [
            "Select sweet, fully ripe papaya with vibrant orange flesh.",
            "Peel skin and scrape away all black seeds and inner membrane.",
            "Cut a thick slice and mash thoroughly with a clean fork or spoon.",
            "Feed with a small infant spoon."
        ],
        "choking_warning": "Remove 100% of seeds. Mash until completely smooth without slippery whole cubes."
    },
    {
        "id": "s_boiled_egg_snack",
        "slot": "snack",
        "title": "Mashed Boiled Egg Yolk with Warm Milk",
        "desc": "Hard-boiled egg yolk mashed tender with a spoonful of warm boiled milk for choline, iron, and fats.",
        "groups": [6, 4],
        "required_ingredients": ["egg", "milk"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "egg_vegetarian",
        "texture": "Soft crumbly moist mash",
        "age_min_months": 7,
        "allergens": ["egg", "dairy"],
        "prep_steps": [
            "Boil fresh egg for 10-12 minutes in clean water until solid.",
            "Cool, peel shell, and separate the yellow yolk.",
            "Place yolk in a clean bowl and mash thoroughly with a fork.",
            "Add 1 tablespoon warm boiled milk or thin broth to make it moist and easy to swallow."
        ],
        "choking_warning": "Egg yolk can be powdery/dry; always moisten with milk or broth to prevent choking."
    },
    {
        "id": "s_sattu_drink",
        "slot": "snack",
        "title": "Roasted Bengal Gram (Sattu) Warm Drink",
        "desc": "Roasted gram flour whisked smooth with warm boiled milk or clean water and a drop of ghee for quick plant protein.",
        "groups": [3, 4],
        "required_ingredients": ["sattu", "milk"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Smooth cup-feeding liquid / Warm beverage",
        "age_min_months": 8,
        "allergens": ["dairy"],
        "prep_steps": [
            "Whisk 1 tablespoon roasted sattu (roasted chana powder) into 1/2 cup warm boiled milk or clean water.",
            "Stir briskly to ensure complete dissolution without sediment.",
            "Add 1/4 teaspoon ghee for sustained calories.",
            "Offer via open cup or small feeding spoon."
        ],
        "choking_warning": "Feed sitting upright. Do not offer through narrow feeding bottles which may clog."
    },

    # DINNER
    {
        "id": "d_masoor_rice",
        "slot": "dinner",
        "title": "Red Lentil (Masoor Dal) with Soft Rice & Spinach",
        "desc": "Quick-cooking red lentils and soft rice simmered tender with spinach and a teaspoon of healthy cooking oil.",
        "groups": [2, 3, 7],
        "required_ingredients": ["rice", "dal", "spinach"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Gentle warm mash",
        "age_min_months": 7,
        "allergens": [],
        "prep_steps": [
            "Wash red masoor dal and rice together.",
            "Simmer with finely shredded spinach, cumin, and turmeric in 1 cup water until tender (15 mins).",
            "Mash to a soft comforting consistency with the back of a spoon.",
            "Add 1/2 teaspoon ghee or oil for evening satiety."
        ],
        "choking_warning": "Ensure greens are thoroughly cooked and shredded; remove fibrous stems."
    },
    {
        "id": "d_roti_dal",
        "slot": "dinner",
        "title": "Soft Chapati Soaked in Moong Dal & Pumpkin Stew",
        "desc": "Fresh chapati softened in warm moong dal with cumin and cooked pumpkin for gentle evening digestion.",
        "groups": [2, 3, 7],
        "required_ingredients": ["wheat", "dal", "pumpkin"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Soft soaked pieces",
        "age_min_months": 8,
        "allergens": ["gluten"],
        "prep_steps": [
            "Prepare a warm stew of yellow moong dal and peeled sweet pumpkin cubes.",
            "Tear whole-wheat chapati into small shreds into the warm dal bowl.",
            "Cover and let stand for 3 minutes until roti completely softens and absorbs the liquid.",
            "Mash lightly with a fork to test softness before feeding."
        ],
        "choking_warning": "Discard any dry or crusty edges; all pieces must be completely soaked and soft."
    },
    {
        "id": "d_potato_dal",
        "slot": "dinner",
        "title": "Mashed Potato & Yellow Moong Dal Stew",
        "desc": "Boiled potato cubes mashed with warm dal soup and a drop of cooking oil for comforting evening calories.",
        "groups": [2, 3],
        "required_ingredients": ["potato", "dal"],
        "cost_band": "₹",
        "budget_tier": "budget_conscious",
        "diet": "vegetarian",
        "texture": "Comforting smooth mash",
        "age_min_months": 7,
        "allergens": [],
        "prep_steps": [
            "Boil one small potato until completely tender and peel skin.",
            "Simmer yellow moong dal with turmeric and roasted cumin until soft.",
            "Mash potato into warm dal stew until a smooth, porridge-like texture is formed.",
            "Stir in 1/2 teaspoon ghee or oil."
        ],
        "choking_warning": "Ensure potato has zero hard or uncooked lumps."
    },
    {
        "id": "d_chicken_rice",
        "slot": "dinner",
        "title": "Soft Rice in Chicken & Vegetable Broth",
        "desc": "Warm soft rice soaked in tender shredded chicken broth with soft cooked carrots for bioavailable evening nutrients.",
        "groups": [2, 5, 7],
        "required_ingredients": ["chicken", "rice", "carrot"],
        "cost_band": "₹₹",
        "budget_tier": "standard",
        "diet": "non_vegetarian",
        "texture": "Warm soothing stew",
        "age_min_months": 10,
        "allergens": [],
        "prep_steps": [
            "Simmer boneless chicken pieces with sliced carrot, cumin, and turmeric to create a rich broth.",
            "Shred the cooked chicken into tiny, soft fibers (confirm zero bones).",
            "Mix shredded chicken and soft cooked carrots with warm overcooked white rice.",
            "Mash to a soft spoonable texture."
        ],
        "choking_warning": "Verify zero bone fragments. Chicken fibers must be short and soft."
    }
]

# ---------------------------------------------------------------------------
# Conversational Questions Catalog (Progressive Asking Framework)
# ---------------------------------------------------------------------------
QUESTION_SEQUENCE = [
    # --- INFANT QUESTIONS (AGE 0 TO 5 MONTHS) ---
    {
        "id": "q_infant_feeding_mode",
        "field": "infant_feeding_mode",
        "prompt": "What feeding method is currently being used for your baby?",
        "type": "single_choice",
        "min_age_months": 0,
        "max_age_months": 5.99,
        "options": [
            {"value": "exclusive_breastfeeding", "label": "Exclusive Breastfeeding (Only breast milk — no other milk, water or solids)"},
            {"value": "breastfeeding_plus_water", "label": "Breastfeeding + water, gripe water, or herbal teas"},
            {"value": "formula", "label": "Infant Formula"},
            {"value": "animal_milk", "label": "Animal milk (cow or buffalo milk)"},
            {"value": "early_solids", "label": "Early solid foods (cerelac, biscuits, porridge)"},
        ],
        "guidance": "WHO recommends exclusive breastfeeding for the first 6 months without any water or other liquids."
    },
    {
        "id": "q_infant_nursing_frequency",
        "field": "infant_nursing_frequency",
        "prompt": "How many times does your baby nurse or feed in a 24-hour day?",
        "type": "single_choice",
        "min_age_months": 0,
        "max_age_months": 5.99,
        "options": [
            {"value": "8_to_12_on_demand", "label": "8 to 12+ times (Frequent on demand whenever baby shows hunger cues)"},
            {"value": "6_to_7_times", "label": "6 to 7 times daily"},
            {"value": "less_than_6", "label": "Fewer than 6 times daily (infrequent)"},
        ],
        "guidance": "Newborns and young infants thrive on frequent responsive nursing (8–12+ times per 24 hours)."
    },
    {
        "id": "q_infant_wet_diapers",
        "field": "infant_wet_diapers",
        "prompt": "How many wet diapers does your baby have in a typical 24-hour day?",
        "type": "single_choice",
        "min_age_months": 0,
        "max_age_months": 5.99,
        "options": [
            {"value": "6_plus", "label": "6 or more wet diapers (Pale, clear urine — good hydration)"},
            {"value": "4_to_5", "label": "4 to 5 wet diapers"},
            {"value": "less_than_4", "label": "Fewer than 4 wet diapers (Caution: potential low fluid intake)"},
        ],
        "guidance": "At least 6 wet diapers in 24 hours is the primary clinical sign of adequate milk intake."
    },
    {
        "id": "q_infant_difficulties",
        "field": "infant_feeding_difficulties",
        "prompt": "Have you noticed any feeding difficulties, discomfort, or health concerns?",
        "type": "single_choice",
        "min_age_months": 0,
        "max_age_months": 5.99,
        "options": [
            {"value": "none", "label": "None — Baby feeds comfortably and settles well"},
            {"value": "latch_difficulty", "label": "Difficulty latching or nipple pain during feeds"},
            {"value": "tires_quickly", "label": "Baby tires easily or falls asleep after a few minutes"},
            {"value": "frequent_vomiting", "label": "Frequent forceful vomiting or severe spitting up"},
            {"value": "lethargy_refusal", "label": "Lethargy, fever, or refusal to nurse"},
        ],
        "guidance": "Identifying latch and feeding comfort early helps ensure optimal growth."
    },
    {
        "id": "q_infant_food_recall",
        "field": "food_recall.infant_items",
        "prompt": "What did your baby drink or receive yesterday in the past 24 hours?",
        "type": "text_or_tags",
        "min_age_months": 0,
        "max_age_months": 5.99,
        "suggested_tags": ["Breast milk only", "Plain water", "Infant formula", "Cow milk", "Gripe water", "Biscuit mash"],
        "guidance": "Confirming yesterday's intake helps assess whether any non-breastmilk liquids were introduced."
    },

    # --- COMPLEMENTARY FEEDING QUESTIONS (AGE 6 TO 59 MONTHS) ---
    {
        "id": "q_meal_frequency",
        "field": "meal_frequency",
        "prompt": "How many main meals and snacks does your child usually have in a normal day?",
        "type": "composite_frequency",
        "min_age_months": 6,
        "max_age_months": 999,
        "options": [
            {"label": "2 main meals + 1 snack", "meals": 2, "snacks": 1},
            {"label": "3 main meals + 1 snack", "meals": 3, "snacks": 1},
            {"label": "3 main meals + 2 snacks", "meals": 3, "snacks": 2},
            {"label": "1-2 meals, irregular", "meals": 2, "snacks": 0},
            {"label": "Other / custom count", "meals": None, "snacks": None},
        ],
        "guidance": "Consistent meal frequency supports energy density and growth."
    },
    {
        "id": "q_food_recall_breakfast",
        "field": "food_recall.breakfast",
        "prompt": "What did your child have to eat or drink for breakfast yesterday morning?",
        "type": "text_or_tags",
        "min_age_months": 6,
        "max_age_months": 999,
        "suggested_tags": ["Poha", "Ragi porridge", "Idli", "Suji upma", "Boiled egg", "Milk", "Banana", "Bread / Roti", "Breast milk"],
        "guidance": "Recalling what your child actually ate helps identify which food groups are well-represented."
    },
    {
        "id": "q_food_recall_lunch",
        "field": "food_recall.lunch",
        "prompt": "What did your child have for lunch or the mid-day meal?",
        "type": "text_or_tags",
        "min_age_months": 6,
        "max_age_months": 999,
        "suggested_tags": ["Rice and Dal", "Khichdi", "Curd rice", "Roti with Dal", "Vegetables (carrot/spinach)", "Chicken / Fish", "Boiled potato"],
        "guidance": "Lunch provides vital daytime protein, iron, and energy."
    },
    {
        "id": "q_food_recall_dinner",
        "field": "food_recall.dinner",
        "prompt": "What did your child eat for dinner or the evening meal?",
        "type": "text_or_tags",
        "min_age_months": 6,
        "max_age_months": 999,
        "suggested_tags": ["Dal khichdi", "Rice with dal", "Soft roti soaked in dal", "Mashed potato", "Vegetables", "Milk", "Breast milk"],
        "guidance": "Evening meals support overnight recovery and satiety."
    },
    {
        "id": "q_food_recall_snacks",
        "field": "food_recall.snacks_and_drinks",
        "prompt": "Did your child have any fruit, snacks, or drinks (including milk or breastfeeding) between meals?",
        "type": "text_or_tags",
        "min_age_months": 6,
        "max_age_months": 999,
        "suggested_tags": ["Banana", "Papaya", "Apple / Chikoo", "Plain Curd / Dahi", "Boiled egg yolk", "Breastfeeding", "Water", "Biscuit / Packaged snack"],
        "guidance": "Snacks between meals are an opportunity to introduce fruits and healthy dairy."
    },
    {
        "id": "q_diet_pattern",
        "field": "dietary_pattern",
        "prompt": "What is your household's dietary preference for the child's meals?",
        "type": "single_choice",
        "min_age_months": 6,
        "max_age_months": 999,
        "options": [
            {"value": "vegetarian", "label": "Vegetarian (Plant-based + Dairy)"},
            {"value": "egg_vegetarian", "label": "Egg-Vegetarian (Vegetarian + Eggs)"},
            {"value": "non_vegetarian", "label": "Non-Vegetarian (Includes Chicken, Fish, Meat)"},
            {"value": "mixed", "label": "Mixed / General Family Diet"},
        ],
        "guidance": "Guidance will respect your family's cultural and dietary choices."
    },
    {
        "id": "q_allergies",
        "field": "allergies",
        "prompt": "Does your child have any known food allergies, intolerances, or foods they specifically avoid?",
        "type": "multi_choice_or_text",
        "min_age_months": 6,
        "max_age_months": 999,
        "options": [
            {"value": "none", "label": "No known allergies"},
            {"value": "egg", "label": "Egg"},
            {"value": "dairy", "label": "Cow milk / Dairy products"},
            {"value": "gluten", "label": "Wheat / Gluten"},
            {"value": "nuts", "label": "Peanuts / Tree nuts"},
            {"value": "fish", "label": "Fish / Seafood"},
        ],
        "guidance": "Safety first: We strictly filter out any foods that your child cannot safely tolerate."
    },
    {
        "id": "q_available_foods",
        "field": "available_foods",
        "prompt": "Which foods are currently available at home in your kitchen or pantry?",
        "type": "multi_choice",
        "min_age_months": 6,
        "max_age_months": 999,
        "options": [
            {"value": "rice", "label": "Rice"},
            {"value": "wheat", "label": "Wheat / Atta"},
            {"value": "poha", "label": "Poha (Flattened rice)"},
            {"value": "ragi", "label": "Ragi (Finger millet)"},
            {"value": "suji", "label": "Suji / Semolina"},
            {"value": "dal", "label": "Yellow Moong / Masoor Dal"},
            {"value": "chana", "label": "Chana / Chickpeas"},
            {"value": "sattu", "label": "Sattu / Roasted gram"},
            {"value": "egg", "label": "Eggs"},
            {"value": "milk", "label": "Milk"},
            {"value": "curd", "label": "Curd / Dahi"},
            {"value": "paneer", "label": "Paneer"},
            {"value": "chicken", "label": "Chicken / Poultry"},
            {"value": "fish", "label": "Fish"},
            {"value": "potato", "label": "Potato"},
            {"value": "carrot", "label": "Carrot"},
            {"value": "spinach", "label": "Spinach / Leafy greens"},
            {"value": "pumpkin", "label": "Pumpkin"},
            {"value": "banana", "label": "Banana"},
            {"value": "papaya", "label": "Papaya"},
            {"value": "bottle gourd", "label": "Bottle gourd / Lauki"},
        ],
        "guidance": "Prioritizing what you already have at home makes daily meals practical and achievable."
    },
    {
        "id": "q_budget_tier",
        "field": "budget_tier",
        "prompt": "Which meal planning approach is most practical for your household?",
        "type": "single_choice",
        "min_age_months": 6,
        "max_age_months": 999,
        "options": [
            {"value": "budget_conscious", "label": "Budget-conscious (₹) — Focus on accessible staple foods"},
            {"value": "standard", "label": "Standard (₹₹) — Balanced seasonal variety"},
            {"value": "flexible", "label": "Flexible (₹₹₹) — Expanded options and variety"},
        ],
        "guidance": "Budget-conscious plans deliver full nutritional adequacy using low-cost staple grains and pulses."
    }
]


class ConversationalNutritionEngine:
    """
    Conversational Pediatric Nutrition Decision-Support Assistant.
    Follows: ASK -> UNDERSTAND -> ANALYZE -> ASK MISSING INFORMATION -> PERSONALIZE -> EXPLAIN -> RECOMMEND -> MONITOR.
    """
    MASTER_FOOD_CATALOG = MASTER_FOOD_CATALOG

    @classmethod
    def classify_food_item(cls, item_str: str) -> List[int]:
        """Parse text string to identify matched WHO Food Group IDs (1-8)."""
        if not item_str or not item_str.strip():
            return []
        text = item_str.lower().strip()
        matched = set()
        for group_id, keywords in FOOD_VOCABULARY_MAP.items():
            for kw in keywords:
                if kw in text:
                    matched.add(group_id)
                    break
        return sorted(list(matched))

    @classmethod
    def analyze_food_recall(
        cls,
        recall_data: Optional[Dict[str, Any]],
        age_months: float
    ) -> Dict[str, Any]:
        """
        Evaluate 24-hour food recall against WHO 8 Food Groups.
        STRICT RULE: Distinguishes 'NOT_ASSESSED' from zero!
        If recall_data is empty or not provided, returns status='NOT_ASSESSED' and score=None.
        """
        if not recall_data:
            return {
                "status": "NOT_ASSESSED",
                "mdd_score": None,
                "mdd_achieved": None,
                "display_score": "Not assessed yet.",
                "groups_consumed": [],
                "missing_groups": [g["id"] for g in WHO_8_FOOD_GROUPS],
                "occasions_count": None,
                "slot_details": {},
            }

        slots = ["breakfast", "mid_morning", "lunch", "evening_snack", "dinner", "drinks", "breastfeeding"]
        all_reported_items = []
        slot_details = {}
        consumed_groups_set: Set[int] = set()
        occasions_count = 0

        has_any_entry = False

        for s in slots:
            raw_val = recall_data.get(s, [])
            items = []
            if isinstance(raw_val, list):
                items = [str(x).strip() for x in raw_val if str(x).strip()]
            elif isinstance(raw_val, str) and raw_val.strip():
                # Split comma-separated or newline-separated items
                items = [x.strip() for x in raw_val.replace("\n", ",").split(",") if x.strip()]

            slot_details[s] = items
            if items:
                has_any_entry = True
                if s not in ["drinks"]:  # Main meal or snack occasions
                    occasions_count += 1
                for itm in items:
                    all_reported_items.append(itm)
                    matched_groups = cls.classify_food_item(itm)
                    consumed_groups_set.update(matched_groups)

        # Check special breastfeeding key
        if recall_data.get("is_breastfeeding") is True or recall_data.get("breastfeeding") is True:
            consumed_groups_set.add(1)
            has_any_entry = True

        if not has_any_entry:
            return {
                "status": "NOT_ASSESSED",
                "mdd_score": None,
                "mdd_achieved": None,
                "display_score": "Not assessed yet.",
                "groups_consumed": [],
                "missing_groups": [g["id"] for g in WHO_8_FOOD_GROUPS],
                "occasions_count": None,
                "slot_details": slot_details,
            }

        score = len(consumed_groups_set)
        # WHO MDD target: >= 5 groups for children 6-23 months
        mdd_achieved = (score >= 5) if age_months >= 6 else None
        consumed_list = sorted(list(consumed_groups_set))
        missing_list = [g["id"] for g in WHO_8_FOOD_GROUPS if g["id"] not in consumed_groups_set]

        return {
            "status": "ASSESSED",
            "mdd_score": score,
            "mdd_achieved": mdd_achieved,
            "display_score": f"{score} / 8",
            "groups_consumed": consumed_list,
            "missing_groups": missing_list,
            "occasions_count": occasions_count,
            "slot_details": slot_details,
            "all_items": all_reported_items,
        }

    @classmethod
    def evaluate_questions_state(
        cls,
        child_profile: Dict[str, Any],
        assessment_data: Optional[Dict[str, Any]],
        current_answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determines what is already known vs missing.
        Never asks for information already known from profile or assessment.
        Progressively returns the next unanswered question.
        """
        age_months = float(child_profile.get("age_months") or 12.0)
        known_data = {
            "name": child_profile.get("name", "Child"),
            "gender": child_profile.get("gender", "Child"),
            "age_months": age_months,
            "weight": assessment_data.get("weight") if assessment_data else None,
            "height": assessment_data.get("height") if assessment_data else None,
            "muac": assessment_data.get("muac") if assessment_data else None,
            "whz": assessment_data.get("whz") if assessment_data else None,
            "haz": assessment_data.get("haz") if assessment_data else None,
            "waz": assessment_data.get("waz") if assessment_data else None,
            "prediction": assessment_data.get("prediction", "Normal") if assessment_data else "Normal",
            "triage_level": assessment_data.get("triage_level", "ROUTINE (GREEN)") if assessment_data else "ROUTINE (GREEN)",
            "has_bilateral_edema": bool(assessment_data.get("has_bilateral_edema", False)) if assessment_data else False,
        }

        # Collect questions applicable for this child's age
        applicable_questions = [
            q for q in QUESTION_SEQUENCE
            if q.get("min_age_months", 0) <= age_months and age_months <= q.get("max_age_months", 999)
        ]

        missing_questions = []
        for q in applicable_questions:
            field = q["field"]
            # Check if answer exists in current_answers
            if "." in field:
                top, sub = field.split(".", 1)
                sub_dict = current_answers.get(top, {})
                if isinstance(sub_dict, dict) and sub in sub_dict and sub_dict[sub]:
                    continue
            else:
                if field in current_answers and current_answers[field] is not None:
                    continue
            missing_questions.append(q)

        is_complete = len(missing_questions) == 0
        next_q = missing_questions[0] if missing_questions else None

        return {
            "is_complete": is_complete,
            "total_questions": len(applicable_questions),
            "answered_count": len(applicable_questions) - len(missing_questions),
            "next_question": next_q,
            "missing_questions": missing_questions,
            "known_data": known_data,
        }

    @classmethod
    def conduct_gap_analysis(
        cls,
        age_months: float,
        recall_eval: Dict[str, Any],
        reported_occasions: Optional[int],
        clinical_severity: str,
        edema: bool = False,
        answers: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Analyze gaps using strict non-causal language ('may contribute', 'may be associated with').
        """
        gaps = []

        # 1. Clinical safety gap
        if clinical_severity == "SAM" or edema:
            gaps.append({
                "category": "clinical_safety",
                "severity": "urgent",
                "finding": "Acute nutritional vulnerability / clinical triage criteria present.",
                "explanation": "Anthropometric measurements or physical markers indicate urgent clinical need. Clinical evaluation takes priority over routine dietary adjustments."
            })

        # 2. Food Recall Assessment Status
        if recall_eval["status"] == "NOT_ASSESSED":
            gaps.append({
                "category": "recall_status",
                "severity": "info",
                "finding": "24-hour dietary intake has not been recorded yet.",
                "explanation": "A complete food recall is necessary to identify which specific nutrient groups are present or missing."
            })
            return gaps

        # Infant checks (< 6 months)
        if age_months < 6:
            infant_mode = (answers or {}).get("infant_feeding_mode", "")
            if infant_mode and infant_mode != "exclusive_breastfeeding":
                gaps.append({
                    "category": "infant_exclusive_feeding",
                    "severity": "urgent" if infant_mode in ["animal_milk", "early_solids"] else "moderate",
                    "finding": "Non-exclusive feeding or early liquids/solids reported before 6 months.",
                    "explanation": "Introducing water, animal milk, or early solid feeds before 6 months may irritate the infant's immature intestinal lining and displace antibody-rich breast milk."
                })
            elif recall_eval.get("is_exclusive_breastfeeding") is False:
                gaps.append({
                    "category": "infant_exclusive_feeding",
                    "severity": "moderate",
                    "finding": "Non-breastmilk liquids or items reported in infant intake recall.",
                    "explanation": "WHO guidelines emphasize exclusive breastfeeding on demand. Even plain water is unnecessary and displaces essential milk calories."
                })

            wet_diapers = (answers or {}).get("infant_wet_diapers", "")
            if wet_diapers == "less_than_4":
                gaps.append({
                    "category": "infant_hydration",
                    "severity": "urgent",
                    "finding": "Fewer than 4 wet diapers per 24 hours reported.",
                    "explanation": "Fewer than 6 wet diapers daily may indicate insufficient milk transfer or low fluid intake, requiring immediate clinical hydration check."
                })

            nursing_freq = (answers or {}).get("infant_nursing_frequency", "")
            if nursing_freq == "less_than_6":
                gaps.append({
                    "category": "nursing_frequency",
                    "severity": "moderate",
                    "finding": "Infrequent nursing sessions reported (fewer than 6 times per day).",
                    "explanation": "Infants require frequent responsive feeding (8 to 12+ times per 24 hours) to maintain adequate caloric density and sustain maternal milk supply."
                })

            difficulties = (answers or {}).get("infant_feeding_difficulties", "")
            if difficulties in ["latch_difficulty", "tires_quickly"]:
                gaps.append({
                    "category": "feeding_difficulty",
                    "severity": "moderate",
                    "finding": "Latching difficulty or infant tiring quickly during feeds reported.",
                    "explanation": "Clinical evaluation of latch and positioning by a lactation professional or Anganwadi worker can help ensure comfortable, efficient milk transfer."
                })
            elif difficulties in ["frequent_vomiting", "lethargy_refusal"]:
                gaps.append({
                    "category": "clinical_danger_sign",
                    "severity": "urgent",
                    "finding": "Clinical danger signs (frequent vomiting, extreme lethargy, or feed refusal) noted.",
                    "explanation": "Prompt in-person pediatric review is required to rule out acute medical illness or dehydration."
                })

        # 3. Dietary Diversity Gap (>= 6 months)
        mdd_score = recall_eval["mdd_score"]
        groups_consumed = set(recall_eval.get("groups_consumed", []))

        if age_months >= 6:
            if mdd_score < 5:
                missing_names = [g["name"] for g in WHO_8_FOOD_GROUPS if g["id"] not in groups_consumed]
                gaps.append({
                    "category": "dietary_diversity",
                    "severity": "moderate" if mdd_score >= 3 else "high",
                    "finding": f"Low dietary diversity ({mdd_score}/8 WHO food groups reported).",
                    "explanation": f"The reported intake shows limited dietary variety, which may be one contributing factor worth discussing. Missing groups include: {', '.join(missing_names[:3])}."
                })

            # Check Protein Groups (Pulses #3, Dairy #4, Flesh #5, Eggs #6)
            protein_groups = {3, 4, 5, 6}.intersection(groups_consumed)
            if not protein_groups:
                gaps.append({
                    "category": "protein_adequacy",
                    "severity": "high",
                    "finding": "Limited primary protein-rich food groups in recall.",
                    "explanation": "No regular pulses, dairy, eggs, or tender flesh foods were reported in yesterday's intake, which may contribute to inadequate protein and micronutrient density."
                })

            # Check Vitamin A & Fruits/Vegetables (Groups #7, #8)
            vita_groups = {7}.intersection(groups_consumed)
            other_veg_groups = {8}.intersection(groups_consumed)
            if not vita_groups:
                gaps.append({
                    "category": "micronutrient_diversity",
                    "severity": "moderate",
                    "finding": "Vitamin-A rich fruits and vegetables not observed in reported meals.",
                    "explanation": "Foods rich in vitamin A (such as orange-fleshed vegetables or dark greens) were not noted, which may influence immune and ocular health."
                })
            if not other_veg_groups and not vita_groups:
                gaps.append({
                    "category": "produce_variety",
                    "severity": "moderate",
                    "finding": "Limited fruit and vegetable consumption.",
                    "explanation": "Seasonal fruits and cooked vegetables provide essential potassium, vitamin C, and fiber to support digestion."
                })

            # 4. Meal Frequency Gap
            from ai.models.nutrition_recommender import get_age_appropriate_frequency
            freq_info = get_age_appropriate_frequency(age_months)
            if reported_occasions is not None and reported_occasions > 0:
                if reported_occasions < freq_info["min_meals"]:
                    gaps.append({
                        "category": "meal_frequency",
                        "severity": "moderate",
                        "finding": f"Reported feeding frequency ({reported_occasions} occasions) is below age target.",
                        "explanation": f"Children aged {age_months:.0f} months usually thrive best with {freq_info['min_meals']}–{freq_info['max_meals']} meals plus nutritious snacks, as smaller stomach capacity requires frequent energy intake."
                    })

        return gaps

    @classmethod
    def check_clinical_safety_and_disagreement(
        cls,
        prediction: str,
        triage_level: str,
        whz: Optional[float],
        muac: Optional[float],
        has_bilateral_edema: bool = False,
        haz: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate clinical priority override and detect disagreement between WHO anthropometrics and AI prediction.
        """
        pred_lower = (prediction or "").lower()
        triage_lower = (triage_level or "").lower()

        is_sam = False
        is_mam = False
        reasons = []

        if has_bilateral_edema:
            is_sam = True
            reasons.append("Nutritional bilateral pitting edema detected")
        if muac is not None and muac < 11.5:
            is_sam = True
            reasons.append(f"MUAC {muac:.1f} cm is below 11.5 cm threshold")
        if whz is not None and whz < -3.0:
            is_sam = True
            reasons.append(f"WHZ {whz:.2f} SD indicates severe wasting")
        if whz is not None and whz > 3.0:
            is_sam = True
            reasons.append(f"WHZ {whz:+.2f} SD represents very high weight-for-length / extreme biological outlier requiring clinical verification")
        if haz is not None and haz < -3.0:
            is_sam = True
            reasons.append(f"HAZ {haz:.2f} SD indicates severe stunting")
        if "sam" in pred_lower or "severe" in pred_lower or "red" in triage_lower:
            is_sam = True
            reasons.append("Clinical triage or screening flagged urgent clinical tier")

        if not is_sam:
            if muac is not None and muac < 12.5:
                is_mam = True
                reasons.append(f"MUAC {muac:.1f} cm indicates moderate wasting")
            if whz is not None and whz < -2.0:
                is_mam = True
                reasons.append(f"WHZ {whz:.2f} SD indicates moderate wasting")
            if haz is not None and haz < -2.0:
                is_mam = True
                reasons.append(f"HAZ {haz:.2f} SD indicates moderate stunting")
            if "mam" in pred_lower or "moderate" in pred_lower or "yellow" in triage_lower or "amber" in triage_lower:
                is_mam = True
                reasons.append("Screening flagged moderate nutritional risk")

        severity = "SAM" if is_sam else ("MAM" if is_mam else "Normal")

        # Disagreement check between WHO WHZ and AI prediction
        disagreement_detected = False
        disagreement_note = None

        if whz is not None:
            who_indicates_wasting = (whz < -2.0)
            ai_indicates_normal = ("normal" in pred_lower)
            who_indicates_normal = (-2.0 <= whz <= 2.0)
            ai_indicates_wasting = ("sam" in pred_lower or "mam" in pred_lower or "wast" in pred_lower or "severe" in pred_lower)

            if who_indicates_wasting and ai_indicates_normal:
                disagreement_detected = True
                disagreement_note = "The AI screening result and WHO growth assessment do not fully agree (WHZ indicates wasting while AI screening classified case as Normal). This result should be reviewed using the complete clinical and growth information."
            elif who_indicates_normal and ai_indicates_wasting:
                disagreement_detected = True
                disagreement_note = "The AI screening result and WHO growth assessment do not fully agree (AI model flagged risk features while WHO WHZ is within normal parameters). A comprehensive health worker review is recommended."

        return {
            "severity": severity,
            "requires_professional_assessment": is_sam,
            "safety_status": "SAFETY_REVIEW" if is_sam else ("MODERATE_MONITORING" if is_mam else "ROUTINE"),
            "safety_reasons": reasons,
            "disagreement_detected": disagreement_detected,
            "disagreement_note": disagreement_note,
        }

    @classmethod
    def generate_personalized_plan(
        cls,
        child_profile: Dict[str, Any],
        assessment_data: Optional[Dict[str, Any]],
        answers: Dict[str, Any],
        growth_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Produce a tailored nutrition guidance plan based on gathered information.
        Every single recommendation comes with a documented 'Why' linking to the child's actual assessment.
        """
        age_months = float(child_profile.get("age_months") or 12.0)
        gender = child_profile.get("gender", "Child")
        name = child_profile.get("name", "Child")
        first_name = name.split()[0] if name else "Child"

        wt = float(assessment_data.get("weight") or 9.0) if assessment_data else 9.0
        ht = float(assessment_data.get("height") or 75.0) if assessment_data else 75.0
        muac = float(assessment_data.get("muac")) if (assessment_data and assessment_data.get("muac") is not None) else None
        whz = float(assessment_data.get("whz")) if (assessment_data and assessment_data.get("whz") is not None) else 0.0
        haz = float(assessment_data.get("haz")) if (assessment_data and assessment_data.get("haz") is not None) else 0.0
        waz = float(assessment_data.get("waz")) if (assessment_data and assessment_data.get("waz") is not None) else 0.0
        prediction = str(assessment_data.get("prediction", "Normal")) if assessment_data else "Normal"
        triage_level = str(assessment_data.get("triage_level", "ROUTINE (GREEN)")) if assessment_data else "ROUTINE (GREEN)"
        has_bilateral_edema = bool(assessment_data.get("has_bilateral_edema", False)) if assessment_data else False

        # Extract caregiver answers
        budget_tier = str(answers.get("budget_tier") or "budget_conscious")
        diet_pattern = str(answers.get("dietary_pattern") or "vegetarian")
        raw_allergies = answers.get("allergies", [])
        if isinstance(raw_allergies, str):
            allergies_list = [a.strip().lower() for a in raw_allergies.split(",") if a.strip()]
        else:
            allergies_list = [str(a).strip().lower() for a in (raw_allergies or [])]
        allergies_set = set(a for a in allergies_list if a and a != "none")

        raw_pantry = answers.get("available_foods", [])
        if isinstance(raw_pantry, str):
            available_foods = set(p.strip().lower() for p in raw_pantry.split(",") if p.strip())
        else:
            available_foods = set(str(p).strip().lower() for p in (raw_pantry or []))

        # 24-hr Food Recall analysis
        food_recall = answers.get("food_recall", {})
        recall_eval = cls.analyze_food_recall(food_recall, age_months)

        # Reported occasions
        reported_occasions = None
        meal_freq_ans = answers.get("meal_frequency")
        if isinstance(meal_freq_ans, dict):
            m_count = meal_freq_ans.get("meals", 0) or 0
            s_count = meal_freq_ans.get("snacks", 0) or 0
            reported_occasions = m_count + s_count
        elif isinstance(meal_freq_ans, (int, float)):
            reported_occasions = int(meal_freq_ans)
        elif recall_eval["occasions_count"] is not None:
            reported_occasions = recall_eval["occasions_count"]

        # Safety & Disagreement check
        safety_info = cls.check_clinical_safety_and_disagreement(
            prediction=prediction,
            triage_level=triage_level,
            whz=whz,
            muac=muac,
            has_bilateral_edema=has_bilateral_edema,
            haz=haz
        )
        severity = safety_info["severity"]

        # Gaps analysis
        gaps = cls.conduct_gap_analysis(
            age_months=age_months,
            recall_eval=recall_eval,
            reported_occasions=reported_occasions,
            clinical_severity=severity,
            edema=has_bilateral_edema,
            answers=answers
        )

        # Longitudinal check
        longitudinal_note = None
        has_longitudinal_trajectory = False
        if growth_history and len(growth_history) > 1:
            has_longitudinal_trajectory = True
            first_entry = growth_history[0]
            latest_entry = growth_history[-1]
            wt_diff = float(latest_entry.get("weight", wt)) - float(first_entry.get("weight", wt))
            longitudinal_note = f"Tracked across {len(growth_history)} clinical visits: net weight change of {wt_diff:+.2f} kg recorded."
        else:
            longitudinal_note = "Insufficient history for growth-trend analysis."

        # Filter meals or Infant Nursing Routine
        selected_meals = []
        is_infant_exclusive = (age_months < 6)

        if is_infant_exclusive:
            selected_meals = [
                {
                    "id": "infant_morning_nursing",
                    "slot": "morning",
                    "title": "Early Morning Responsive Nursing",
                    "desc": "Breastfeed on first hunger cues (rooting, smacking lips, hands to mouth). Offer both breasts until baby releases spontaneously.",
                    "groups": [1],
                    "required_ingredients": ["breast milk"],
                    "cost_band": "₹0",
                    "budget_tier": "budget_conscious",
                    "diet": "infant_milk",
                    "texture": "Breast milk (Exclusive liquid nutrition)",
                    "why_selected": "Promotes early morning rehydration and stimulates prolactin for sustained maternal milk production.",
                    "prep_steps": [
                        "Wash hands with clean water and soap before feeding.",
                        "Sit in a comfortable, well-supported posture with baby tummy-to-tummy against mother.",
                        "Wait for baby to open wide, then bring baby to breast ensuring a deep, comfortable latch.",
                        "Allow baby to nurse until satisfied and release the breast naturally."
                    ],
                    "choking_warning": "Zero water, teas, or animal milk should be given. Burp gently over shoulder after feeding."
                },
                {
                    "id": "infant_midday_nursing",
                    "slot": "midday",
                    "title": "Midday Responsive Nursing",
                    "desc": "Quiet, calm daytime feeding session. Ensure chin touches breast and lower lip is curled outwards.",
                    "groups": [1],
                    "required_ingredients": ["breast milk"],
                    "cost_band": "₹0",
                    "budget_tier": "budget_conscious",
                    "diet": "infant_milk",
                    "texture": "Breast milk (Exclusive liquid nutrition)",
                    "why_selected": "Supplies daytime calories, whey proteins, and protective secretory IgA antibodies.",
                    "prep_steps": [
                        "Feed whenever infant shows early hunger signs (aim for 8–12+ total nursing sessions per 24 hours).",
                        "Alternate starting breast each session to balance milk production.",
                        "Mother should drink a glass of clean water or nutritious warm broth before or after feeding."
                    ],
                    "choking_warning": "Keep infant head slightly elevated above stomach level during feeding."
                },
                {
                    "id": "infant_afternoon_nursing",
                    "slot": "afternoon",
                    "title": "Afternoon Responsive Nursing",
                    "desc": "On-demand nursing session to maintain hydration and comfort throughout warm afternoon hours.",
                    "groups": [1],
                    "required_ingredients": ["breast milk"],
                    "cost_band": "₹0",
                    "budget_tier": "budget_conscious",
                    "diet": "infant_milk",
                    "texture": "Breast milk (Exclusive liquid nutrition)",
                    "why_selected": "Provides complete hydration (breast milk is >87% clean biological water) without need for plain water.",
                    "prep_steps": [
                        "Ensure mother rests in a cool, quiet space.",
                        "Encourage unhurried skin-to-skin contact if baby is fussy to stimulate oxytocin and milk let-down."
                    ],
                    "choking_warning": "Do not give plain water or gripe water, which can cause water intoxication and diarrhea."
                },
                {
                    "id": "infant_evening_night_nursing",
                    "slot": "evening_night",
                    "title": "Evening & Night Responsive Nursing",
                    "desc": "Night-time feeds are critical for healthy infant weight gain and stimulate nocturnal prolactin release.",
                    "groups": [1],
                    "required_ingredients": ["breast milk"],
                    "cost_band": "₹0",
                    "budget_tier": "budget_conscious",
                    "diet": "infant_milk",
                    "texture": "Breast milk (Exclusive liquid nutrition)",
                    "why_selected": "Night breast milk is rich in melatonin and healthy fats, supporting brain growth and overnight rest.",
                    "prep_steps": [
                        "Nurse baby whenever waking or showing hunger cues at night.",
                        "Keep room softly lit to promote smooth transition back to sleep.",
                        "Place baby safely on their back on a firm, flat mattress after burping."
                    ],
                    "choking_warning": "Always place infant on their back to sleep. Never prop bottles in baby's mouth."
                }
            ]
        else:
            meal_slots = ["breakfast", "lunch", "snack", "dinner"]

            for slot_key in meal_slots:
                candidates = [m for m in MASTER_FOOD_CATALOG if m["slot"] == slot_key]

                # 1. Filter by age
                candidates = [m for m in candidates if m["age_min_months"] <= age_months]

                # 2. Filter by allergies
                if allergies_set:
                    candidates = [
                        m for m in candidates
                        if not any(a in allergies_set for a in m.get("allergens", []))
                        and not any(a in allergies_set for a in m.get("required_ingredients", []))
                    ]

                # 3. Filter by dietary pattern
                if diet_pattern == "vegetarian":
                    candidates = [m for m in candidates if m["diet"] == "vegetarian"]
                elif diet_pattern == "egg_vegetarian":
                    candidates = [m for m in candidates if m["diet"] in ["vegetarian", "egg_vegetarian"]]
                # non_vegetarian allows all

                # 4. Filter by budget tier
                if budget_tier == "budget_conscious":
                    tier_subset = [m for m in candidates if m["budget_tier"] == "budget_conscious"]
                    if tier_subset:
                        candidates = tier_subset
                elif budget_tier == "standard":
                    tier_subset = [m for m in candidates if m["budget_tier"] in ["budget_conscious", "standard"]]
                    if tier_subset:
                        candidates = tier_subset

                # 5. Prioritize by available pantry foods
                if available_foods:
                    def pantry_score(item: Dict[str, Any]) -> int:
                        reqs = set(item.get("required_ingredients", []))
                        if not reqs:
                            return 0
                        return len(reqs.intersection(available_foods))

                    candidates.sort(key=pantry_score, reverse=True)

                # Pick chosen meal or safe fallback
                if candidates:
                    chosen = dict(candidates[0])
                else:
                    chosen = {
                        "id": f"{slot_key}_safe_default",
                        "slot": slot_key,
                        "title": f"Nutritious {slot_key.capitalize()}",
                        "desc": "Freshly prepared grain and pulse porridge prepared with soft consistency.",
                        "groups": [2, 3],
                        "cost_band": "₹",
                        "prep_steps": ["Boil grains and pulses thoroughly until soft and mash with clean utensils."],
                        "choking_warning": "Ensure soft lump-free consistency.",
                        "texture": "Age-appropriate soft mash",
                        "required_ingredients": ["rice", "dal"]
                    }

                # Generate specific WHY for this meal
                why_reasons = []
                chosen_groups = chosen.get("groups", [])
                req_ingredients = chosen.get("required_ingredients", [])

                # Check if this meal addresses an identified gap
                if 3 in chosen_groups or 4 in chosen_groups or 5 in chosen_groups or 6 in chosen_groups:
                    if any(g["category"] == "protein_adequacy" for g in gaps) or (recall_eval["mdd_score"] is not None and recall_eval["mdd_score"] < 5):
                        why_reasons.append("Supplies bioavailable protein to improve daily nutrient density and address protein variety needs.")
                if 7 in chosen_groups:
                    why_reasons.append("Provides vitamin-A precursors and carotenoids for immune system and tissue development.")
                if 8 in chosen_groups:
                    why_reasons.append("Introduces dietary fiber and potassium from gentle fruits/vegetables.")
                if available_foods and any(ing in available_foods for ing in req_ingredients):
                    matched_ing = [ing for ing in req_ingredients if ing in available_foods]
                    why_reasons.append(f"Uses foods currently available at your home ({', '.join(matched_ing)}).")
                if not why_reasons:
                    why_reasons.append(f"Provides energy-dense complementary feeding appropriate for {age_months:.0f} months.")

                chosen["why_selected"] = " ".join(why_reasons)
                selected_meals.append(chosen)

        # Build 10-Part Explanation Structure (Section 28)
        explanation_10_parts = cls.generate_10_part_explanation(
            child_name=first_name,
            age_months=age_months,
            gender=gender,
            wt=wt,
            ht=ht,
            muac=muac,
            whz=whz,
            safety_info=safety_info,
            recall_eval=recall_eval,
            reported_occasions=reported_occasions,
            gaps=gaps,
            selected_meals=selected_meals,
            diet_pattern=diet_pattern,
            budget_tier=budget_tier,
            available_foods=available_foods,
            longitudinal_note=longitudinal_note
        )

        return {
            "child_name": first_name,
            "age_months": age_months,
            "gender": gender,
            "anthropometrics": {
                "weight": wt,
                "height": ht,
                "muac": muac,
                "whz": whz,
                "haz": haz,
                "waz": waz,
            },
            "dietary_pattern": diet_pattern,
            "budget_tier": budget_tier,
            "allergies": list(allergies_set),
            "available_foods": list(available_foods),
            "safety_info": safety_info,
            "food_recall_evaluation": recall_eval,
            "nutrition_gaps": gaps,
            "meal_schedule": selected_meals,
            "explanation_10_parts": explanation_10_parts,
            "longitudinal_status": {
                "has_trajectory": has_longitudinal_trajectory,
                "note": longitudinal_note
            },
            "is_breastfeeding_exclusive": (age_months < 6),
            "algorithm": "ChildNutri Conversational Pediatric Nutrition Decision-Support Engine v2.0"
        }

    @classmethod
    def generate_pantry_recipes(
        cls,
        available_ingredients: List[str],
        age_months: float,
        diet_pattern: str = "vegetarian",
        allergies: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate meal ideas STRICTLY from selected ingredients + basic staples.
        Never injects unselected foods.
        """
        avail_set = set(str(i).strip().lower() for i in available_ingredients if str(i).strip())
        allergies_set = set(str(a).strip().lower() for a in (allergies or []) if str(a).strip() and a != "none")

        valid_recipes = []
        for meal in MASTER_FOOD_CATALOG:
            if meal["age_min_months"] > age_months:
                continue

            # Allergies check
            if any(a in allergies_set for a in meal.get("allergens", [])):
                continue
            if any(a in allergies_set for a in meal.get("required_ingredients", [])):
                continue

            # Diet pattern check
            if diet_pattern == "vegetarian" and meal["diet"] != "vegetarian":
                continue
            elif diet_pattern == "egg_vegetarian" and meal["diet"] not in ["vegetarian", "egg_vegetarian"]:
                continue

            # STRICT INGREDIENT CHECK:
            # All required ingredients MUST be in avail_set (or permitted basic prep)
            reqs = meal.get("required_ingredients", [])
            all_reqs_met = all(
                (r in avail_set or r in PERMITTED_BASIC_PREP)
                for r in reqs
            )

            if all_reqs_met and reqs:
                valid_recipes.append({
                    "id": meal["id"],
                    "slot": meal["slot"],
                    "title": meal["title"],
                    "desc": meal["desc"],
                    "required_ingredients": reqs,
                    "food_groups": meal["groups"],
                    "texture": meal["texture"],
                    "prep_steps": meal["prep_steps"],
                    "choking_warning": meal["choking_warning"]
                })

        return valid_recipes

    @classmethod
    def generate_substitution(
        cls,
        slot_key: str,
        current_meal_id: str,
        age_months: float,
        diet_pattern: str = "vegetarian",
        allergies: Optional[List[str]] = None,
        budget_tier: str = "budget_conscious",
        available_foods: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a valid nutritional replacement for a meal slot respecting constraints and documenting clinical rationale.
        """
        if current_meal_id and not any(m["id"] == current_meal_id for m in MASTER_FOOD_CATALOG):
            return None

        allergies_set = set(str(a).strip().lower() for a in (allergies or []) if str(a).strip() and a != "none")
        if "all" in allergies_set or "everything" in allergies_set:
            return None

        avail_set = set(str(i).strip().lower() for i in (available_foods or [])) if available_foods else None

        candidates = [
            m for m in MASTER_FOOD_CATALOG
            if m["slot"] == slot_key and m["id"] != current_meal_id
        ]
        candidates = [m for m in candidates if m["age_min_months"] <= age_months]

        if allergies_set:
            candidates = [
                m for m in candidates
                if not any(a in allergies_set for a in m.get("allergens", []))
                and not any(a in allergies_set for a in m.get("required_ingredients", []))
            ]

        if diet_pattern == "vegetarian":
            candidates = [m for m in candidates if m["diet"] == "vegetarian"]
        elif diet_pattern == "egg_vegetarian":
            candidates = [m for m in candidates if m["diet"] in ["vegetarian", "egg_vegetarian"]]

        if budget_tier == "budget_conscious":
            budget_sub = [m for m in candidates if m["budget_tier"] == "budget_conscious"]
            if budget_sub:
                candidates = budget_sub

        if avail_set:
            def p_score(m: Dict[str, Any]) -> int:
                return len(set(m.get("required_ingredients", [])).intersection(avail_set))
            candidates.sort(key=p_score, reverse=True)

        if not candidates:
            return None

        sub = dict(candidates[0])
        sub["substitution_rationale"] = (
            f"Nutritional alternative for {slot_key}: provides compatible energy density and food groups ({', '.join(str(g) for g in sub['groups'])}) "
            f"while aligning with the {diet_pattern.replace('_', ' ')} dietary pattern and allergy exclusions."
        )
        return sub

    @classmethod
    def generate_10_part_explanation(
        cls,
        child_name: str,
        age_months: float,
        gender: str,
        wt: float,
        ht: float,
        muac: Optional[float],
        whz: float,
        safety_info: Dict[str, Any],
        recall_eval: Dict[str, Any],
        reported_occasions: Optional[int],
        gaps: List[Dict[str, str]],
        selected_meals: List[Dict[str, Any]],
        diet_pattern: str,
        budget_tier: str,
        available_foods: Set[str],
        longitudinal_note: Optional[str]
    ) -> Dict[str, str]:
        """
        Build the 10-part structured explanation conforming to Section 28 of specifications.
        """
        # Part 1: WHAT I FOUND
        muac_str = f"{muac:.1f} cm" if muac is not None else "Not recorded"
        whz_str = f"{whz:+.2f} SD" if whz is not None else "Not assessed"
        recall_status_str = recall_eval["display_score"]
        part1 = (
            f"I reviewed the growth information and dietary details shared for {child_name}. "
            f"{child_name} is {age_months:.0f} months old ({gender}), with a recorded weight of {wt:.1f} kg and length/height of {ht:.1f} cm. "
            f"The WHO Weight-for-Height Z-score is {whz_str}, and Mid-Upper Arm Circumference is {muac_str}. "
            f"In terms of daily eating pattern, {reported_occasions if reported_occasions is not None else 'routine'} eating occasions were recorded, "
            f"and dietary diversity from the 24-hour food recall is {recall_status_str}."
        )

        # Part 2: WHAT NEEDS ATTENTION
        if gaps:
            gap_bullets = "\n".join([f"• {g['finding']} {g['explanation']}" for g in gaps])
            part2 = f"Based on the assessment and dietary recall, here are the specific nutritional areas to focus on:\n{gap_bullets}"
        else:
            part2 = f"{child_name}'s reported feeding shows balanced diversity across food groups with age-appropriate meal occasions."

        # Part 3: WHY THIS MATTERS
        if age_months < 6:
            part3 = (
                "For infants under 6 months, exclusive breast milk provides the exact balance of energy, proteins, antibodies, "
                "and hydration required for brain and physical development. Supplementary water or solid foods displace breast milk and increase infection risk."
            )
        elif age_months < 24:
            part3 = (
                "Between 6 and 23 months, children experience rapid brain development and physical growth while their stomach capacity remains small. "
                "Each meal must therefore be nutrient-dense. Missing out on protein-rich pulses, dairy, eggs, or vitamin-rich vegetables may contribute to "
                "slower weight velocity or micronutrient vulnerability over time."
            )
        else:
            part3 = (
                "In young children aged 2 to 5 years, dietary diversity ensures adequate iron, calcium, and zinc for immune resilience and healthy muscle growth. "
                "Relying heavily on single grains without diverse vegetable or protein pairings may limit micronutrient absorption."
            )

        # Part 4: WHAT I WOULD FOCUS ON
        focus_points = []
        if safety_info["severity"] == "SAM":
            focus_points.append("Immediate clinical evaluation by a pediatrician or Nutrition Rehabilitation Centre (NRC) takes primary priority.")
        if recall_eval["status"] == "NOT_ASSESSED":
            focus_points.append("Completing a 24-hour food recall to map out exact food group representation.")
        elif recall_eval["mdd_score"] is not None and recall_eval["mdd_score"] < 5:
            focus_points.append("Gradually adding foods from missing WHO food groups (especially pulses, vegetables, or healthy fats) rather than merely increasing portions of plain grain.")
        if reported_occasions is not None and reported_occasions < 3 and age_months >= 6:
            focus_points.append("Structuring at least 3 small, energy-dense meals plus 1–2 healthy snacks daily to match child stomach capacity.")
        focus_points.append("Practicing patient, responsive feeding where the child is encouraged to self-feed without pressure or force.")

        part4 = "\n".join([f"{i+1}. {pt}" for i, pt in enumerate(focus_points)])

        # Part 5: YOUR CHILD'S PERSONALIZED FOOD OPTIONS / INFANT FEEDING
        if age_months < 6:
            meal_bullets = [
                "• **Early Morning Nursing:** Frequent responsive breastfeeding on early hunger cues (rooting, fists to mouth).",
                "• **Midday Nursing:** Quiet, unhurried feeding ensuring deep comfortable latch with chin touching breast.",
                "• **Afternoon Nursing:** On-demand nursing maintaining complete biological hydration without any water.",
                "• **Night Nursing:** Essential night-time feeds supporting steady weight gain and prolactin stimulation."
            ]
            part5 = (
                f"Here is the individualized infant feeding routine tailored for {child_name} (age {age_months:.1f} months):\n"
                + "\n".join(meal_bullets)
            )
        else:
            meal_bullets = []
            for m in selected_meals:
                meal_bullets.append(f"• **{m['slot'].capitalize()}:** {m['title']} — {m['desc']} (Texture: {m.get('texture', 'Soft mash')})")
            part5 = (
                f"Here are practical, age-appropriate meal options tailored for {child_name}'s {diet_pattern.replace('_', ' ')} diet "
                f"and {budget_tier.replace('_', '-')} planning approach:\n" + "\n".join(meal_bullets)
            )

        # Part 6: WHY I CHOSE THESE FOODS / ROUTINE
        if age_months < 6:
            part6 = (
                "This routine is structured intentionally based on authoritative pediatric guidance for infants under 6 months:\n"
                "• Human breast milk provides 100% of required calories, bioavailable protein, immunoglobulins, and clean hydration.\n"
                "• Responsive feeding on early hunger cues ensures optimal milk transfer and protects maternal lactation supply.\n"
                "• Zero plain water, animal milk, or infant biscuits are needed, as non-milk fluids dilute nutrients and carry infection risk."
            )
        else:
            why_bullets = []
            for m in selected_meals:
                why_bullets.append(f"• **{m['title']}:** {m.get('why_selected', 'Provides age-appropriate energy and nutrients.')}")
            part6 = (
                "Every meal option was chosen intentionally based on your child's specific situation:\n" + "\n".join(why_bullets)
            )

        # Part 7: SAFE FEEDING
        if age_months < 6:
            part7 = (
                "• **Exclusive Nutrition:** Offer only breast milk. Zero water, gripe water, tea, animal milk, or early solid feeds before 6 months.\n"
                "• **Deep Latch Technique:** Wait for a wide open mouth; bring baby chin-first to breast so nipple points toward roof of mouth and lips curl outwards.\n"
                "• **Responsive Nursing:** Feed on early hunger cues (rooting, smacking lips, hands to mouth); do not wait for crying, which causes latch difficulty.\n"
                "• **Hygiene & Safe Sleep:** Wash hands before feeding. Gently burp over shoulder. Always place baby to sleep on their back on a firm, flat surface."
            )
        else:
            part7 = (
                f"• **Texture & Consistency:** For {age_months:.0f} months, food should be {selected_meals[0].get('texture', 'soft moist mash')} and thick enough to stay on a spoon without sliding off.\n"
                f"• **Choking Safety:** Avoid whole round grapes, whole nuts, hard raw carrot chunks, or unmashed chickpeas. Always ensure child is seated upright while eating.\n"
                f"• **Hygiene:** Wash hands with clean water and soap before preparing and feeding meals. Store cooked food safely covered.\n"
                f"• **Responsive Feeding:** Feed patiently, observe hunger and fullness cues, and never force-feed."
            )

        # Part 8: WHAT TO MONITOR
        if age_months < 6:
            part8 = (
                f"• **Wet Diaper Count:** At least 6 clear or pale wet diapers in 24 hours confirms good hydration and adequate milk intake.\n"
                f"• **Feeding Contentment:** Notice whether {child_name} settles peacefully and uncurls fists after nursing.\n"
                f"• **Weight Gain Velocity:** Have {child_name}'s weight measured monthly on a calibrated infant scale.\n"
                f"• **Longitudinal Context:** {longitudinal_note or 'Track growth measurements at your local health centre.'}"
            )
        else:
            part8 = (
                f"• **Appetite & Interest:** Notice whether {child_name} reaches for food and feeds willingly.\n"
                f"• **Digestion & Tolerance:** Watch for comfortable bowel movements without recurring watery stools or vomiting.\n"
                f"• **Growth Velocity:** Have {child_name}'s weight and height measured periodically (monthly if in recovery, every 2-3 months routinely).\n"
                f"• **Longitudinal Context:** {longitudinal_note or 'Track growth measurements at your local health centre.'}"
            )

        # Part 9: WHEN PROFESSIONAL ASSESSMENT IS IMPORTANT
        if safety_info["severity"] == "SAM":
            part9 = (
                "⚠️ **URGENT PROFESSIONAL ASSESSMENT IS IMPORTANT:**\n"
                f"{child_name}'s anthropometric markers or clinical triage indicate an acute clinical priority condition. "
                "Please consult a qualified pediatrician or visit your local Nutrition Rehabilitation Centre (NRC) or Primary Health Centre without delay for supervised clinical care. "
                "Do not rely solely on routine home feeding adjustments."
            )
        elif safety_info["severity"] == "MAM":
            part9 = (
                "**Pediatric Review Advised:**\n"
                "Measurements show moderate nutritional risk. We recommend scheduling a visit with your pediatrician or Anganwadi worker for supplementary nutrition support and growth velocity review within 1–2 weeks."
            )
        else:
            part9 = (
                "Seek prompt pediatric evaluation if you notice persistent refusal to feed, poor weight gain over consecutive checkups, fever, persistent cough, or signs of illness."
            )

        if safety_info.get("disagreement_detected"):
            part9 += f"\n\n**Note on Assessment Agreement:** {safety_info['disagreement_note']}"

        # Part 10: IMPORTANT NOTE
        part10 = (
            "ChildNutri AI provides evidence-based nutrition decision support designed to help caregivers make informed feeding choices. "
            "This system is not a doctor, does not autonomously diagnose conditions, and does not prescribe medication. "
            "Always consult your pediatrician or local community health provider for medical diagnoses and individualized clinical care."
        )

        return {
            "what_i_found": part1,
            "what_needs_attention": part2,
            "why_this_matters": part3,
            "what_i_would_focus_on": part4,
            "personalized_food_options": part5,
            "why_i_chose_these_foods": part6,
            "safe_feeding": part7,
            "what_to_monitor": part8,
            "when_professional_assessment_is_important": part9,
            "important_note": part10,
        }
