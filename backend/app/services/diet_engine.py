"""
ChildNutri AI — Diet & Care Plan Engine (Rule-Based Knowledge Base)

Selection logic:
  plan_id = case × age_band × preference_filters + modifiers

All plans follow the same 8-section structure as per ChildNutriAI_Full_Build_Plan.md §7.
Content based on: WHO IYCF guidance, ICMR-NIN 2020, IAP, POSHAN Abhiyaan.
"""

from __future__ import annotations
from typing import Optional


# ── Age band helper ──────────────────────────────────────────────────────────

def _age_band(age_months: float) -> str:
    if age_months < 6:
        return "0-5m"
    if age_months < 9:
        return "6-8m"
    if age_months < 12:
        return "9-11m"
    if age_months < 24:
        return "12-23m"
    return "24-59m"


# ── Knowledge base ────────────────────────────────────────────────────────────
# Structure: {(case, age_band): plan_dict}

_PLANS: dict[tuple, dict] = {

    # ── SAM ───────────────────────────────────────────────────────────────────
    ("SAM", "0-5m"): {
        "what_this_means": "Your baby has severe acute malnutrition. At this age, the safest treatment is in a hospital. Please go to a health centre or Nutrition Rehabilitation Centre (NRC) immediately.",
        "how_to_feed": "Do not delay seeking medical care. If you are breastfeeding, continue. Do not give formula or other foods without medical advice at this age.",
        "foods_that_help": ["Breast milk (most important)"],
        "foods_to_limit": ["Formula or cow's milk without medical advice", "Any solid food at this age"],
        "keep_healthy": "Go to hospital now. Follow the doctor's feeding plan exactly.",
        "ask_doctor": "All feeding decisions must be made by a doctor for a baby this young with SAM.",
        "government_help": "NRC (Nutrition Rehabilitation Centres) in government hospitals provide free inpatient treatment. Your Anganwadi worker can help.",
        "follow_up": "Hospital admission likely required. Follow-up every week after discharge.",
        "red_flags": ["Won't feed at all", "Pale, cold, or blue skin", "Seizures", "Difficulty breathing", "Swelling of feet or whole body"],
    },

    ("SAM", "6-8m"): {
        "what_this_means": "Your child (6-8 months) has severe acute malnutrition — very low weight-for-height or MUAC below 11.5 cm. This is a medical emergency. Please visit a hospital or NRC today.",
        "how_to_feed": "Hospital-based care first. If uncomplicated (eating, alert, no medical complications), a health worker may give Ready-to-Use Therapeutic Food (RUTF) at home under supervision. Continue breastfeeding. Start mashed foods after medical clearance.",
        "foods_that_help": ["Breast milk", "RUTF (Plumpynut or equivalent — prescribed by health worker)", "Mashed banana", "Diluted dal water"],
        "foods_to_limit": ["Sugary drinks", "Packaged snacks", "Cow's milk as main drink"],
        "keep_healthy": "Give RUTF as directed. Wash hands before feeding. Keep vaccines current. Go back to clinic every 1-2 weeks.",
        "ask_doctor": "RUTF dosage, Vitamin A, Iron and zinc supplementation, deworming",
        "government_help": "RUTF available free at NRC/CMAM centres. Anganwadi can refer to NRC.",
        "follow_up": "Weekly visit to health worker until MUAC > 12.5 cm for 2 consecutive visits.",
        "red_flags": ["Refuses all food", "Vomits everything", "Very sleepy or hard to wake", "Seizures", "Fast breathing", "Swelling anywhere"],
    },

    ("SAM", "9-11m"): {
        "what_this_means": "Your child (9-11 months) has severe acute malnutrition. Immediate medical attention is needed. Do not try to manage this only at home.",
        "how_to_feed": "If under medical supervision and no complications: RUTF + continue breastfeeding + soft mashed complementary foods 5× per day, small portions. Offer every 2-3 hours.",
        "foods_that_help": ["Breast milk", "RUTF", "Soft khichdi (rice+dal+ghee)", "Mashed egg yolk", "Mashed banana or papaya"],
        "foods_to_limit": ["Watery thin porridges (not energy-dense enough)", "Sugary drinks", "Tea/coffee"],
        "keep_healthy": "Small frequent meals. Give ORS if diarrhoea. Handwashing. Keep vaccines updated.",
        "ask_doctor": "RUTF prescription, Vitamin A, iron drops, zinc, deworming schedule",
        "government_help": "NRC free inpatient or outpatient programme, Anganwadi take-home ration",
        "follow_up": "Every 1-2 weeks under health worker until recovered.",
        "red_flags": ["Not eating at all", "Vomiting repeatedly", "Very lethargic", "High fever", "Swelling of feet"],
    },

    ("SAM", "12-23m"): {
        "what_this_means": "Your toddler (12-23 months) has severe acute malnutrition. The priority is medical evaluation. If no medical complications, treatment can sometimes happen at home with RUTF and close follow-up.",
        "how_to_feed": "RUTF + family foods — 5-6 small meals a day. Energy-dense foods at each meal. Add fat (ghee, groundnut paste) and protein (dal, egg, curd) to every meal. Continue breastfeeding if still breastfed.",
        "foods_that_help": ["Khichdi with ghee", "Egg", "Mashed dal", "Groundnut chikki/paste (no allergy)", "Banana", "Curd", "Ragi porridge with jaggery and ghee"],
        "foods_to_limit": ["Biscuits, chips, packaged food", "Sugary drinks", "Very watery food"],
        "keep_healthy": "Feed actively (don't wait for child to ask). Wash hands. Keep water safe. Give zinc + ORS for diarrhoea. See doctor for all vaccines.",
        "ask_doctor": "RUTF amount, iron + zinc + Vitamin A supplements, deworming",
        "government_help": "Anganwadi supplementary food, POSHAN Abhiyaan, NRC referral if needed",
        "follow_up": "Every 1-2 weeks. Discharge criteria: MUAC ≥ 12.5 cm + no oedema for 2 visits.",
        "red_flags": ["Not eating or drinking", "Vomits everything", "Fits/seizures", "Swelling of feet", "Fast breathing", "High fever"],
    },

    ("SAM", "24-59m"): {
        "what_this_means": "Your child (2-5 years) has severe acute malnutrition. Please see a doctor today. With medical clearance and no complications, home treatment with RUTF and nutritious food is possible.",
        "how_to_feed": "RUTF + 3 main meals + 2-3 snacks daily. Make every bite count — add ghee, eggs, groundnut paste, or curd to meals. Don't dilute food with water.",
        "foods_that_help": ["Egg", "Dal + rice with ghee", "Ragi mudde", "Groundnut chikki", "Banana", "Seasonal vegetables", "Curd/paneer"],
        "foods_to_limit": ["Packaged biscuits, chips, sweets", "Sweet drinks/soda", "Tea/coffee"],
        "keep_healthy": "Regular deworming. All vaccines on time. Hand washing before meals. Safe water. Seek care for fever/cough early.",
        "ask_doctor": "RUTF prescription, Vitamin A, iron + zinc supplementation, deworming",
        "government_help": "Anganwadi Kendras, POSHAN Abhiyaan, Mid-Day Meal, NRC",
        "follow_up": "Every 2 weeks until discharge from SAM programme.",
        "red_flags": ["Refuses food and water", "Vomits all food", "Unconscious or very sleepy", "Fits", "Swelling of feet or face", "Fast or difficult breathing"],
    },

    # ── MAM ───────────────────────────────────────────────────────────────────
    ("MAM", "6-8m"): {
        "what_this_means": "Your child (6-8 months) has moderate acute malnutrition — lower weight-for-height or MUAC 11.5-12.5 cm. This can be treated at home with extra nutritious food and close monitoring.",
        "how_to_feed": "Breastfeed as often as possible + start complementary foods 2-3 times per day. Mash food well. Make it thick, not watery.",
        "foods_that_help": ["Breast milk (continue always)", "Mashed rice-dal (thick)", "Mashed banana or papaya", "Soft egg yolk", "Ragi porridge with jaggery"],
        "foods_to_limit": ["Watery porridges", "Sugary water or fruit juice", "Cow's milk as main drink"],
        "keep_healthy": "Feed slowly and lovingly. Wash hands. Give ORS + zinc if diarrhoea. Doctor for all vaccines.",
        "ask_doctor": "Vitamin A drop, iron supplement, Anganwadi supplementary nutrition",
        "government_help": "Anganwadi supplementary nutrition (SNP), POSHAN Abhiyaan",
        "follow_up": "Recheck weight and MUAC in 2 weeks. If not improving, refer to health centre.",
        "red_flags": ["Refuses to eat", "Vomiting", "Fever", "Fast breathing", "MUAC drops below 11.5 cm"],
    },

    ("MAM", "9-11m"): {
        "what_this_means": "Moderate malnutrition at 9-11 months. Treatable at home with extra energy-dense foods + continued breastfeeding.",
        "how_to_feed": "Breastfeed + 3-4 complementary feeds daily. Add a fat source (ghee, oil) to every meal. Aim for thick porridges, mashed soft food.",
        "foods_that_help": ["Breast milk", "Thick khichdi with ghee", "Mashed dal + vegetable", "Soft ragi porridge", "Egg yolk", "Mashed banana", "Curd"],
        "foods_to_limit": ["Very watery porridges", "Tea, coffee", "Sugary drinks"],
        "keep_healthy": "5 small meals. Wash hands. Give zinc for diarrhoea. Vaccines on time.",
        "ask_doctor": "Iron drops, Vitamin A, Anganwadi SNP, zinc for diarrhoea",
        "government_help": "Anganwadi supplementary nutrition",
        "follow_up": "Recheck in 2 weeks.",
        "red_flags": ["Refuses food", "Fever > 2 days", "Persistent diarrhoea", "MUAC drops < 11.5 cm"],
    },

    ("MAM", "12-23m"): {
        "what_this_means": "Your toddler (1-2 years) has moderate malnutrition. With extra nutritious food 5-6 times a day and close follow-up, most children recover fully.",
        "how_to_feed": "5-6 small meals daily. Add energy-dense ingredients to every meal (ghee, groundnut paste, curd). Make food thick. Continue breastfeeding.",
        "foods_that_help": ["Khichdi with ghee + dal", "Egg (well cooked)", "Ragi porridge with jaggery", "Groundnut ladoo (no allergy)", "Banana", "Seasonal veg", "Curd", "Paneer"],
        "foods_to_limit": ["Watery dal without rice", "Biscuits/namkeen as meals", "Sweet drinks"],
        "keep_healthy": "Responsive feeding — don't force, but be patient and encouraging. Safe water. Deworm if prescribed. Vaccines on time.",
        "ask_doctor": "Iron + zinc, Vitamin A, deworming tablet",
        "government_help": "Anganwadi SNP, ICDS take-home ration, POSHAN Abhiyaan",
        "follow_up": "Recheck every 2 weeks. Target: MUAC ≥ 12.5 cm.",
        "red_flags": ["Refuses food and liquids", "Persistent vomiting", "High fever", "MUAC < 11.5 cm — go to SAM programme"],
    },

    ("MAM", "24-59m"): {
        "what_this_means": "Moderate malnutrition at 2-5 years is common but can be reversed. Extra nutritious food and care at home will help your child grow.",
        "how_to_feed": "3 main meals + 2-3 snacks. Make every bite count — protein, fat, and vegetables at every meal.",
        "foods_that_help": ["Egg", "Dal + rice + ghee", "Ragi mudde", "Peanut butter/chikki", "Banana", "Dark green vegetables", "Curd or milk"],
        "foods_to_limit": ["Packaged chips, biscuits", "Sweet drinks, juice boxes", "Tea/coffee with meals"],
        "keep_healthy": "Active play. Good sleep. Hand washing before meals. Deworm every 6 months. Vaccines complete.",
        "ask_doctor": "Vitamin A, iron + zinc tablet, deworming",
        "government_help": "Anganwadi supplementary food, POSHAN Abhiyaan, Mid-Day Meal",
        "follow_up": "Every 4 weeks.",
        "red_flags": ["Not eating for >1 day", "High fever", "Rapid weight loss", "MUAC < 11.5 cm"],
    },

    # ── STUNTED ──────────────────────────────────────────────────────────────
    ("STUNTED", "0-5m"): {
        "what_this_means": "Your baby's height is lower than expected for their age (stunting). This started before or around birth. The first 1,000 days are the critical window — your actions now matter most.",
        "how_to_feed": "Exclusive breastfeeding — nothing else, not even water, for 6 months. Breast milk gives everything the baby needs.",
        "foods_that_help": ["Breast milk (exclusive — no formula, water, or other foods)"],
        "foods_to_limit": ["Formula unless medically necessary", "Water, gripe water, herbal drinks"],
        "keep_healthy": "Feed on demand, 8+ times per day. Hold and respond to your baby. Vitamins only from doctor.",
        "ask_doctor": "Vitamin D supplementation, check for any infection or thyroid issue",
        "government_help": "Janani Shishu Suraksha Karyakram (JSSK), Anganwadi",
        "follow_up": "Monthly weight and length check. Continue monitoring.",
        "red_flags": ["Weight is falling instead of gaining", "Baby seems sick or very sleepy"],
    },

    ("STUNTED", "6-8m"): {
        "what_this_means": "Stunting means your child's height is below expected. Stunting builds up slowly — catching up takes months of consistent, quality feeding.",
        "how_to_feed": "Continue breastfeeding + start thick complementary foods twice daily. Introduce variety slowly.",
        "foods_that_help": ["Breast milk", "Mashed dal, egg yolk, soft ragi, mashed banana"],
        "foods_to_limit": ["Watery porridges — always make thick", "Cow's milk as main drink"],
        "keep_healthy": "Prevent infections: handwashing, safe water. Prevent diarrhoea. Monthly growth monitoring.",
        "ask_doctor": "Micronutrient powder or syrup, Vitamin A, iron",
        "government_help": "Anganwadi SNP",
        "follow_up": "Monthly. Stunting reversal is slow — don't expect overnight change.",
        "red_flags": ["Height and weight both stalling", "Repeated infections"],
    },

    ("STUNTED", "12-23m"): {
        "what_this_means": "Your toddler is shorter than expected. Stunting is a sign of chronic poor nutrition. Focus on quality protein, micronutrients, and preventing infections.",
        "how_to_feed": "5-6 meals. Include protein (egg, dal, curd, fish/chicken if non-veg) + iron-rich (green vegetables, ragi) + vitamin A-rich (carrot, papaya) at every meal.",
        "foods_that_help": ["Egg", "Dal + green veg + rice + ghee", "Ragi porridge", "Curd", "Papaya/banana", "Groundnut"],
        "foods_to_limit": ["Packaged foods", "Sweet drinks"],
        "keep_healthy": "Prevent diarrhoea — safe water, handwashing. Deworm. All vaccines.",
        "ask_doctor": "Iron, zinc, Vitamin A, deworming, micronutrient sprinkles",
        "government_help": "Anganwadi supplementary nutrition",
        "follow_up": "Monthly. 3-6 months to see significant improvement.",
        "red_flags": ["Repeated illness", "Weight also falling (wasting + stunting = more serious)"],
    },

    ("STUNTED", "24-59m"): {
        "what_this_means": "Stunting at this age means the child has had insufficient nutrition for a long time. The window is still open — consistent quality food, fewer infections, and good care can help.",
        "how_to_feed": "3 main meals + 2 snacks. Protein + micronutrient-rich food at every meal. Aim for variety.",
        "foods_that_help": ["Egg", "Dal", "Ragi", "Dark green leafy vegetables", "Seasonal fruit", "Milk/curd", "Fish or chicken (non-veg)"],
        "foods_to_limit": ["Packaged, sugary, fried food"],
        "keep_healthy": "Deworming every 6 months. All vaccines. Active play outdoors.",
        "ask_doctor": "Zinc + iron tablet, Vitamin A dose, deworming",
        "government_help": "Anganwadi, Mid-Day Meal, POSHAN Abhiyaan",
        "follow_up": "Every 3 months.",
        "red_flags": ["Also becoming underweight (both stunted + wasted = urgent referral)"],
    },

    # ── UNDERWEIGHT ──────────────────────────────────────────────────────────
    ("UNDERWEIGHT", "0-5m"): {
        "what_this_means": "Your baby weighs less than expected. At this age, breast milk is the best and only food needed — given frequently and correctly.",
        "how_to_feed": "Exclusive breastfeeding. Feed 8-12 times per day. Ensure good latch. Feed from both breasts.",
        "foods_that_help": ["Breast milk"],
        "foods_to_limit": ["Water, other liquids, formula (unless advised by doctor)"],
        "keep_healthy": "Skin-to-skin contact helps milk supply. Rest well. Mother should eat well.",
        "ask_doctor": "Check for infection, birth complications, or feeding difficulty",
        "government_help": "JSY, JSSK schemes for newborn care",
        "follow_up": "Weigh every 2 weeks.",
        "red_flags": ["No weight gain in 2 weeks", "Very sleepy, not waking for feeds", "Fewer than 6 wet nappies per day"],
    },

    ("UNDERWEIGHT", "12-23m"): {
        "what_this_means": "Your toddler weighs less than expected. This is often due to insufficient food, poor diet quality, or frequent illness. It can be reversed with the right food.",
        "how_to_feed": "5-6 small meals. Add energy-dense food to every meal. Eat together as a family. Be patient — don't force.",
        "foods_that_help": ["Khichdi with ghee", "Egg", "Ragi ladoo", "Banana", "Curd", "Groundnut chikki"],
        "foods_to_limit": ["Sugary snacks", "Fruit juice (low nutrient density)", "Tea/coffee"],
        "keep_healthy": "Deworm. Treat illness promptly. Handwashing before meals.",
        "ask_doctor": "Iron syrup, zinc for diarrhoea, Vitamin A",
        "government_help": "Anganwadi, POSHAN take-home ration",
        "follow_up": "Monthly weight check. Should gain ~200g/month at this age.",
        "red_flags": ["Weight loss over 2 weeks", "Persistent poor appetite (possible worms/infection)"],
    },

    ("UNDERWEIGHT", "24-59m"): {
        "what_this_means": "Your child is underweight. A consistent nutritious diet and keeping infections away will help your child gain weight steadily.",
        "how_to_feed": "3 main meals + 2 high-calorie snacks. No skipping meals. Eat with family.",
        "foods_that_help": ["Egg", "Dal + rice + ghee", "Ragi mudde", "Peanut chikki", "Curd", "Banana"],
        "foods_to_limit": ["Chips, biscuits, sweets instead of meals"],
        "keep_healthy": "Deworming. Outdoor play. Adequate sleep.",
        "ask_doctor": "Vitamin A dose, deworming, iron if anaemia suspected",
        "government_help": "Anganwadi, Mid-Day Meal",
        "follow_up": "Monthly weight.",
        "red_flags": ["Rapid weight loss", "Frequent illness", "Poor appetite for > 1 week"],
    },

    # ── HEALTHY ──────────────────────────────────────────────────────────────
    ("HEALTHY", "0-5m"): {
        "what_this_means": "Great news — your baby is growing well! The first 6 months are crucial. Keep doing what you are doing.",
        "how_to_feed": "Exclusive breastfeeding — no water, no other food. 8-12 feeds daily.",
        "foods_that_help": ["Breast milk (only)"],
        "foods_to_limit": ["Formula unless absolutely necessary", "Water, honey, gripe water"],
        "keep_healthy": "Skin-to-skin, responsive care. Vaccinations on time. Monthly growth monitoring.",
        "ask_doctor": "Vitamin K (at birth), Vitamin D if insufficient sunlight",
        "government_help": "JSY, JSSK, Anganwadi",
        "follow_up": "Monthly weight and length at Anganwadi or PHC.",
        "red_flags": ["No weight gain in 2 weeks", "Very sleepy, jaundice, difficulty breathing"],
    },

    ("HEALTHY", "6-8m"): {
        "what_this_means": "Your baby is growing well — this is the time to start introducing solid foods alongside breastfeeding!",
        "how_to_feed": "Breastfeed + start 2 solid meals daily. Thick porridge or mashed food. Add variety each week.",
        "foods_that_help": ["Breast milk (continue)", "Thick rice porridge", "Mashed dal", "Mashed banana", "Soft boiled veg"],
        "foods_to_limit": ["Salt/sugar in baby food", "Honey (not before 12 months)", "Cow's milk as main drink"],
        "keep_healthy": "Introduce one food at a time. Watch for allergies. Vaccinations on time.",
        "ask_doctor": "Iron drops if needed, Vitamin A",
        "government_help": "Anganwadi SNP begins at 6 months",
        "follow_up": "Monthly weight and length.",
        "red_flags": ["Refuses all food for > 3 days", "Rash or vomiting after new food"],
    },

    ("HEALTHY", "12-23m"): {
        "what_this_means": "Your toddler is growing well! This is a great foundation.",
        "how_to_feed": "5 small meals including 2 snacks. Wide variety — all food groups. Eat together as family. Responsive feeding.",
        "foods_that_help": ["Dal-rice-ghee", "Egg", "Curd", "Seasonal vegetables", "Ragi", "Fruit", "Milk"],
        "foods_to_limit": ["Chips, biscuits instead of meals", "Sweet drinks"],
        "keep_healthy": "Active play. Good sleep. Handwashing. Vaccinations complete.",
        "ask_doctor": "Vitamin A dose at 9 months + every 6 months, deworming, iron if pale",
        "government_help": "Anganwadi",
        "follow_up": "Monthly weight check under 24 months.",
        "red_flags": ["Weight stalling for 2+ months", "Frequent diarrhoea or fever"],
    },

    ("HEALTHY", "24-59m"): {
        "what_this_means": "Your child is healthy and growing well. Keep up the great work!",
        "how_to_feed": "3 meals + 1-2 healthy snacks. All food groups daily: grain, protein, dairy, vegetables, fruit.",
        "foods_that_help": ["Dal + rice + ghee", "Egg", "Seasonal veg", "Fruit", "Curd/milk", "Ragi"],
        "foods_to_limit": ["Chips, sugary drinks, sweet biscuits as regular snacks"],
        "keep_healthy": "Active outdoor play daily. Adequate sleep. Handwashing before food. Deworming every 6 months.",
        "ask_doctor": "Vitamin A every 6 months, deworming, annual check-up",
        "government_help": "Anganwadi, Mid-Day Meal when school starts",
        "follow_up": "Every 3 months.",
        "red_flags": ["Weight loss over 1 month", "Very poor appetite, pale nails/skin (anaemia)"],
    },

    # ── OVERWEIGHT ────────────────────────────────────────────────────────────
    ("OVERWEIGHT", "12-23m"): {
        "what_this_means": "Your toddler's weight is higher than expected for their height. This is not always a problem at this age, but it's worth monitoring and adjusting the diet slightly.",
        "how_to_feed": "Stick to regular meal times. Avoid extra snacks. Don't restrict meals — just avoid added sugar and fried snacks.",
        "foods_that_help": ["Vegetables", "Fruit", "Dal", "Whole grain like ragi"],
        "foods_to_limit": ["Sugary drinks", "Sweet biscuits", "Fried snacks", "Excess fruit juice"],
        "keep_healthy": "Active free play daily. Limit screen time. Do not put on a strict diet without doctor's advice.",
        "ask_doctor": "Check if weight is really a concern or within normal variation",
        "government_help": "Anganwadi",
        "follow_up": "Every 3 months. Monitor height and weight together.",
        "red_flags": ["Rapid weight gain with lethargy — see doctor"],
    },

    ("OVERWEIGHT", "24-59m"): {
        "what_this_means": "Your child's weight is above the expected range. Small dietary changes and active play can help — do not start a restrictive diet without medical advice.",
        "how_to_feed": "Regular family meals. Reduce sugary drinks and snacks. More vegetables and less fried food.",
        "foods_that_help": ["Vegetables", "Fruit (whole, not juice)", "Dal", "Curd", "Ragi"],
        "foods_to_limit": ["Sugary drinks", "Packaged snacks", "Excess sweets"],
        "keep_healthy": "1 hour of active outdoor play daily. Less than 1 hour of screen per day.",
        "ask_doctor": "Do not restrict diet without medical guidance",
        "government_help": "Anganwadi",
        "follow_up": "Every 3 months.",
        "red_flags": ["Very rapid weight gain, difficulty breathing, very tired — see doctor"],
    },

    # ── FUTURE_HIGH ──────────────────────────────────────────────────────────
    ("FUTURE_HIGH", "6-8m"): {
        "what_this_means": "Your child is not malnourished right now, but several risk factors suggest they could become malnourished in the next 3-6 months without action.",
        "how_to_feed": "Breastfeed more frequently + thick complementary foods 2-3 times daily. Increase variety and calorie density.",
        "foods_that_help": ["Breast milk", "Thick ragi or rice porridge", "Mashed dal", "Mashed banana"],
        "foods_to_limit": ["Watery porridges", "Skipping feeds"],
        "keep_healthy": "Prevent diarrhoea: safe water, handwashing. Treat illness early.",
        "ask_doctor": "Iron, Vitamin A — check if supplementation needed",
        "government_help": "Anganwadi SNP",
        "follow_up": "Re-assess in 2-4 weeks.",
        "red_flags": ["Weight stalling", "Loss of appetite", "Frequent illness"],
    },

    ("FUTURE_HIGH", "12-23m"): {
        "what_this_means": "Your child is currently at the edge of normal weight/height, and risk factors (diet, illness history, home situation) suggest a high chance of deterioration. Act now.",
        "how_to_feed": "5-6 meals. Energy-dense food at every meal. Address any feeding problems identified.",
        "foods_that_help": ["Khichdi with ghee", "Egg", "Ragi ladoo", "Groundnut paste", "Banana", "Curd"],
        "foods_to_limit": ["Sugary, low-nutrition snacks"],
        "keep_healthy": "Treat diarrhoea immediately with ORS + zinc. Deworm. All vaccines.",
        "ask_doctor": "Iron drops, zinc, Vitamin A, micronutrient powder",
        "government_help": "Anganwadi, POSHAN Abhiyaan",
        "follow_up": "Every 2-4 weeks.",
        "red_flags": ["Rapid weight loss", "MUAC approaching 12.5 cm — refer to MAM programme"],
    },

    ("FUTURE_HIGH", "24-59m"): {
        "what_this_means": "Risk of malnutrition is high over the next few months. Targeted changes to diet and prevention of illness can significantly reduce this risk.",
        "how_to_feed": "3 main meals + 2 snacks. Increase diet diversity. Add protein (egg, dal, groundnut) to every meal.",
        "foods_that_help": ["Egg", "Dal", "Ragi", "Groundnut chikki", "Seasonal veg and fruit"],
        "foods_to_limit": ["Packaged snacks as meals", "Sweet drinks"],
        "keep_healthy": "Deworming now. Treat illness early. All vaccines. Safe water.",
        "ask_doctor": "Micronutrient powder or tablet, deworming",
        "government_help": "Anganwadi, POSHAN, Mid-Day Meal",
        "follow_up": "Every 4 weeks.",
        "red_flags": ["Weight loss", "Frequent illness", "MUAC < 12.5 cm — see health worker immediately"],
    },

    # ── FUTURE_WATCH ─────────────────────────────────────────────────────────
    ("FUTURE_WATCH", "12-23m"): {
        "what_this_means": "Your child is healthy right now, but some factors put them in a 'watch' zone. Small improvements in diet and prevention of illness will keep them on track.",
        "how_to_feed": "5 small meals. Ensure at least 4 food groups daily (grains, protein, dairy, fruit/veg). Add ghee or oil to meals.",
        "foods_that_help": ["Egg", "Dal + green veg", "Curd", "Seasonal fruit", "Ragi"],
        "foods_to_limit": ["Biscuits/chips as main snacks"],
        "keep_healthy": "Handwashing. Safe water. Vaccines on time.",
        "ask_doctor": "Iron if pale, zinc for diarrhoea, Vitamin A",
        "government_help": "Anganwadi",
        "follow_up": "Recheck in 4-6 weeks.",
        "red_flags": ["Weight not gaining over 1 month", "Repeated diarrhoea", "Loss of appetite"],
    },

    ("FUTURE_WATCH", "24-59m"): {
        "what_this_means": "Currently healthy, but some risk factors identified. Monitoring and a slightly improved diet is the action plan.",
        "how_to_feed": "3 balanced meals + 1-2 snacks. Add more variety — especially protein and vegetables.",
        "foods_that_help": ["Egg", "Dal + vegetables + rice", "Seasonal fruit", "Ragi"],
        "foods_to_limit": ["Replace sugary snacks with fruit or groundnut"],
        "keep_healthy": "Deworming every 6 months. Play and sleep.",
        "ask_doctor": "Annual check-up. Iron if pale.",
        "government_help": "Anganwadi, Mid-Day Meal",
        "follow_up": "Every 4-6 weeks.",
        "red_flags": ["Weight loss over 1 month", "Persistent poor appetite"],
    },
}

# Fallback for missing combinations — generate from closest age band
def _get_plan_key(case: str, age_months: float) -> tuple:
    band = _age_band(age_months)
    key = (case, band)
    if key in _PLANS:
        return key
    # Try adjacent age bands
    for alt_band in ["12-23m", "24-59m", "6-8m", "9-11m", "0-5m"]:
        if (case, alt_band) in _PLANS:
            return (case, alt_band)
    return ("HEALTHY", "24-59m")


# ── Preference modifier ────────────────────────────────────────────────────────

def _apply_modifiers(plan: dict, modifiers: dict) -> dict:
    """Inject condition-specific advice into the plan."""
    import copy
    plan = copy.deepcopy(plan)

    if modifiers.get("diarrhoea"):
        plan["how_to_feed"] = "IMPORTANT: Give ORS (1 cup after each loose stool) + zinc tablet for 14 days. " + plan.get("how_to_feed", "")

    if modifiers.get("anaemia"):
        plan["foods_that_help"] = ["Iron-rich: green leafy veg (palak, methi), ragi, jaggery, liver (non-veg)"] + plan.get("foods_that_help", [])

    if modifiers.get("poor_appetite"):
        plan["how_to_feed"] = "Offer small amounts every 1-2 hours. Don't force. Try different textures. " + plan.get("how_to_feed", "")

    if modifiers.get("veg_only"):
        plan["foods_that_help"] = [f for f in plan.get("foods_that_help", []) if "chicken" not in f.lower() and "fish" not in f.lower()]

    return plan


# ── Public API ────────────────────────────────────────────────────────────────

def get_diet_plan(
    case: str,
    age_months: float,
    veg_only: bool = False,
    diarrhoea: bool = False,
    anaemia: bool = False,
    poor_appetite: bool = False,
    allergies: Optional[list] = None,
) -> dict:
    """
    Returns the diet and care plan for a given case and age.

    Args:
        case: One of SAM | MAM | STUNTED | UNDERWEIGHT | OVERWEIGHT |
              FUTURE_HIGH | FUTURE_WATCH | HEALTHY
        age_months: Child's age in months
    """
    key = _get_plan_key(case, age_months)
    plan = dict(_PLANS[key])

    modifiers = {
        "diarrhoea": diarrhoea,
        "anaemia": anaemia,
        "poor_appetite": poor_appetite,
        "veg_only": veg_only,
    }

    plan = _apply_modifiers(plan, modifiers)

    # Remove allergy foods
    if allergies:
        allergies_lower = [a.lower() for a in (allergies or [])]
        plan["foods_that_help"] = [
            f for f in plan.get("foods_that_help", [])
            if not any(a in f.lower() for a in allergies_lower)
        ]

    plan["case"] = case
    plan["age_band"] = _age_band(age_months)
    plan["disclaimer"] = (
        "ChildNutri AI is a screening and education tool. "
        "It does not diagnose illness and does not replace a doctor, nurse, or Anganwadi worker. "
        "If your child has severe symptoms, go to a hospital immediately."
    )

    return plan


diet_engine = type("DietEngine", (), {"get": staticmethod(get_diet_plan)})()
