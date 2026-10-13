"""
YouTube Long-Form Video Automation - Bilingual English/Swahili Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Swahili translations
CATEGORIES_SWAHILI = {
    "Motivation": "Motisha",
    "Love": "Upendo",
    "Success": "Mafanikio",
    "Wisdom": "Hekima",
    "Happiness": "Furaha",
    "Self Improvement": "Kujiboresha",
    "Gratitude": "Shukrani",
    "Friendship": "Urafiki",
    "Hope": "Tumaini",
    "Creativity": "Ubunifu",
    "Inner Peace": "Amani ya Ndani",
    "Confidence": "Kujiamini",
    "Perseverance": "Uvumilivu",
    "Inspiration": "Msukumo",
    "Positive Life": "Maisha Chanya",
    "Courage": "Ujasiri",
    "Kindness": "Wema",
    "Patience": "Subira",
    "Forgiveness": "Msamaha",
    "Strength": "Nguvu",
    "Joy": "Shangwe",
    "Balance": "Usawa",
    "Growth": "Ukuaji",
    "Purpose": "Kusudi",
    "Mindfulness": "Kujitambua",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "sw-KE-ZuriNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "swahili": phrase["swahili"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def repair_and_parse_json(content: str):
    """Robustly parse JSON from LLM output with truncation repair and regex recovery."""
    import re
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1])
        except Exception:
            pass

    if start != -1:
        sub = cleaned[start:]
        last_brace = sub.rfind("}")
        if last_brace != -1:
            try:
                return json.loads(sub[:last_brace+1] + "]")
            except Exception:
                pass

    matches = re.findall(r'\{[^{}]*\"english\"[^{}]*\}', cleaned)
    results = []
    for m in matches:
        try:
            obj = json.loads(m)
            if isinstance(obj, dict) and "english" in obj:
                results.append(obj)
        except Exception:
            continue
    if results:
        return results

    raise ValueError("Could not parse or repair JSON from content")


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_swahili = CATEGORIES_SWAHILI[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Swahili.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Swahili IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Swahili words at all.
The "swahili" field contains the Swahili translation.
The "pronunciation" field is phonetic English spelling approximating Swahili sounds.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Swahili words): {{"english": "Don't say 'jambo,' it's not just hello.", ...}}
WRONG (Swahili word in english): {{"english": "Use 'asante' for thank you", ...}}
WRONG (lesson tip): {{"english": "Say 'kwaheri' for goodbye", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "swahili": "Hekima ni ufunguo wa maarifa.", "pronunciation": "he-kee-ma nee oo-foon-goo-wa ma-a-ree-fa"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "swahili": "Mtu mwenye hekima husikiliza zaidi kuliko kusema.", "pronunciation": "m-too mwe-nye he-kee-ma hoo-see-kee-lee-za za-ee-dee koo-lee-ko koo-se-ma"}}

The english field MUST be 100% English words only. Absolutely NO Swahili words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Swahili words) with commas for natural pauses
2. Swahili translation
3. Pronunciation guide (phonetic English spelling)

Return as JSON array:
[{{"english": "...", "swahili": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Swahili words - no Swahili words at all. These are universal inspirational phrases, NOT language learning tips. Swahili goes ONLY in the 'swahili' field."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = repair_and_parse_json(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    if not all_phrases:
        print(f"[content] AI generation produced 0 phrases. Loading fresh fallback phrases for '{category_english}'...")
        all_phrases = get_fresh_fallback_phrases(category_english, num_phrases)
    elif len(all_phrases) < num_phrases:
        print(f"[content] Only {len(all_phrases)} phrases generated. Padding with fresh fallback phrases...")
        extras = get_fresh_fallback_phrases(category_english, num_phrases - len(all_phrases))
        for ex in extras:
            if ex not in all_phrases:
                all_phrases.append(ex)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "swahili": "Jiamini mwenyewe.", "pronunciation": "jee-ah-mee-nee mwe-nye-we"},
            {"english": "You are capable of amazing things.", "swahili": "Una uwezo wa mambo ya kushangaza.", "pronunciation": "oo-na oo-we-zo wa mam-bo ya koo-shan-ga-za"},
            {"english": "Dream big, start small.", "swahili": "Ota ndoto kubwa, anza kidogo.", "pronunciation": "o-ta n-do-to koo-bwa, an-za kee-do-go"},
            {"english": "Your future is created by your actions.", "swahili": "Mustakabali wako unajengwa na matendo yako.", "pronunciation": "moo-sta-ka-ba-lee wa-ko oo-na-jeng-wa na ma-ten-do ya-ko"},
            {"english": "Never give up on your dreams.", "swahili": "Usikate tamaa kwenye ndoto zako.", "pronunciation": "oo-see-ka-te ta-ma-a kwe-nye n-do-to za-ko"},
            {"english": "Small steps lead to big changes.", "swahili": "Hatua ndogo ndogo zinaleta mabadiliko makubwa.", "pronunciation": "ha-too-a n-do-go n-do-go zee-na-le-ta ma-ba-dee-lee-ko ma-koo-bwa"},
            {"english": "You are stronger than you think.", "swahili": "Wewe una nguvu kuliko unavyofikiri.", "pronunciation": "we-we oo-na ngoo-voo koo-lee-ko oo-na-vyo-fee-kee-ree"},
        ],
        "Love": [
            {"english": "Love yourself first.", "swahili": "Jipende kwanza.", "pronunciation": "jee-pen-de kwan-za"},
            {"english": "Love makes everything possible.", "swahili": "Upendo hufanya kila kitu kiwezekane.", "pronunciation": "oo-pen-do hoo-fan-ya kee-la kee-too kee-we-ze-ka-ne"},
            {"english": "My heart beats for you.", "swahili": "Moyo wangu unakupigia.", "pronunciation": "mo-yo wan-goo oo-na-koo-pee-gee-a"},
            {"english": "You are my everything.", "swahili": "Wewe ni kila kitu kwangu.", "pronunciation": "we-we nee kee-la kee-too kwan-goo"},
            {"english": "Together forever, hand in hand.", "swahili": "Pamoja milele, mkono kwa mkono.", "pronunciation": "pa-mo-ja mee-le-le, m-ko-no kwa m-ko-no"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "swahili": "Mafanikio yanatokana na kazi ngumu.", "pronunciation": "ma-fa-nee-kee-o ya-na-to-ka-na na ka-zee ngoo-moo"},
            {"english": "Keep going, you're getting there.", "swahili": "Endelea, unafika huko.", "pronunciation": "en-de-le-a, oo-na-fee-ka hoo-ko"},
            {"english": "Winners never quit.", "swahili": "Washindi hawakati tamaa.", "pronunciation": "wa-sheen-dee ha-wa-ka-tee ta-ma-a"},
            {"english": "Your effort will pay off.", "swahili": "Jitihada zako zitalipa.", "pronunciation": "jee-tee-ha-da za-ko zee-ta-lee-pa"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "swahili": "Maarifa ni nguvu.", "pronunciation": "ma-a-ree-fa nee ngoo-voo"},
            {"english": "Learn from yesterday, live for today.", "swahili": "Jifunze kutoka jana, ishi kwa ajili ya leo.", "pronunciation": "jee-foon-ze koo-to-ka ja-na, ee-shee kwa a-jee-lee ya le-o"},
            {"english": "Think before you act.", "swahili": "Fikiri kabla ya kutenda.", "pronunciation": "fee-kee-ree kab-la ya koo-ten-da"},
            {"english": "Experience is the best teacher.", "swahili": "Uzoefu ndio mwalimu bora.", "pronunciation": "oo-zo-e-foo n-dee-o mwa-lee-moo bo-ra"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "swahili": "Furaha ni chaguo.", "pronunciation": "foo-ra-ha nee cha-goo-o"},
            {"english": "Find joy in the little things.", "swahili": "Pata furaha katika vitu vidogo.", "pronunciation": "pa-ta foo-ra-ha ka-tee-ka vee-too vee-do-go"},
            {"english": "Smile, it makes others happy.", "swahili": "Tabasamu, inawafurahisha wengine.", "pronunciation": "ta-ba-sa-moo, ee-na-wa-foo-ra-hee-sha wen-ge-ne"},
            {"english": "Today is a gift.", "swahili": "Leo ni zawadi.", "pronunciation": "le-o nee za-wa-dee"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "swahili": "Kuwa bora kuliko jana.", "pronunciation": "koo-wa bo-ra koo-lee-ko ja-na"},
            {"english": "Grow through what you go through.", "swahili": "Kua kwa kupitia kile unachopitia.", "pronunciation": "koo-a kwa koo-pee-tee-a kee-le oo-na-cho-pee-tee-a"},
            {"english": "Invest in yourself daily.", "swahili": "Wekeza ndani yako kila siku.", "pronunciation": "we-ke-za n-da-nee ya-ko kee-la see-koo"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "swahili": "Asante kwa kila kitu.", "pronunciation": "a-san-te kwa kee-la kee-too"},
            {"english": "I appreciate your help.", "swahili": "Nashukuru msaada wako.", "pronunciation": "na-shoo-koo-roo m-sa-a-da wa-ko"},
            {"english": "Grateful for this moment.", "swahili": "Nina shukrani kwa wakati huu.", "pronunciation": "nee-na shook-ra-nee kwa wa-ka-tee hoo-oo"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "swahili": "Marafiki milele, bila kujali nini.", "pronunciation": "ma-ra-fee-kee mee-le-le, bee-la koo-ja-lee nee-nee"},
            {"english": "You are my best friend.", "swahili": "Wewe ni rafiki yangu bora.", "pronunciation": "we-we nee ra-fee-kee yan-goo bo-ra"},
            {"english": "True friends stick together.", "swahili": "Marafiki wa kweli hushikamana.", "pronunciation": "ma-ra-fee-kee wa kwe-lee hoo-she-ka-ma-na"},
        ],
        "Hope": [
            {"english": "There is always hope.", "swahili": "Daima kuna tumaini.", "pronunciation": "da-ee-ma koo-na too-ma-ee-nee"},
            {"english": "Better days are coming.", "swahili": "Siku nzuri zinakuja.", "pronunciation": "see-koo n-zoo-ree zee-na-koo-ja"},
            {"english": "Keep faith, keep going.", "swahili": "Shikilia imani, endelea.", "pronunciation": "shee-kee-lee-a ee-ma-nee, en-de-le-a"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "swahili": "Unda kitu kizuri leo.", "pronunciation": "oon-da kee-too kee-zoo-ree le-o"},
            {"english": "Your imagination is unlimited.", "swahili": "Mawazo yako hayana kikomo.", "pronunciation": "ma-wa-zo ya-ko ha-ya-na kee-ko-mo"},
            {"english": "Art comes from the heart.", "swahili": "Sanaa inatoka moyoni.", "pronunciation": "sa-na-a ee-na-to-ka mo-yo-nee"},
            {"english": "Express yourself freely.", "swahili": "Jieleze kwa uhuru.", "pronunciation": "jee-e-le-ze kwa oo-hoo-roo"},
            {"english": "Innovation starts with curiosity.", "swahili": "Ubunifu huanza na udadisi.", "pronunciation": "oo-boo-nee-foo hoo-an-za na oo-da-dee-see"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "swahili": "Pata amani ndani yako.", "pronunciation": "pa-ta a-ma-nee n-da-nee ya-ko"},
            {"english": "Breathe, relax, let go.", "swahili": "Pumua, pumzika, acha kwenda.", "pronunciation": "poo-moo-a, poom-zee-ka, a-cha kwen-da"},
            {"english": "Calm mind, happy heart.", "swahili": "Akili tulivu, moyo wenye furaha.", "pronunciation": "a-kee-lee too-lee-voo, mo-yo we-nye foo-ra-ha"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "swahili": "Unatosha, jinsi ulivyo.", "pronunciation": "oo-na-to-sha, jeen-see oo-lee-vyo"},
            {"english": "Stand tall, speak up.", "swahili": "Simama wima, sema kwa sauti.", "pronunciation": "see-ma-ma wee-ma, se-ma kwa sa-oo-tee"},
            {"english": "Believe in your abilities.", "swahili": "Amini uwezo wako.", "pronunciation": "a-mee-nee oo-we-zo wa-ko"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "swahili": "Usikate tamaa, endelea kusonga mbele.", "pronunciation": "oo-see-ka-te ta-ma-a, en-de-le-a koo-son-ga m-be-le"},
            {"english": "Storms make trees take deeper roots.", "swahili": "Dhoruba hufanya miti ichukue mizizi mirefu.", "pronunciation": "dho-roo-ba hoo-fan-ya mee-tee ee-choo-koo-e mee-zee-zee mee-re-foo"},
            {"english": "Patience and persistence win.", "swahili": "Subira na uvumilivu hushinda.", "pronunciation": "soo-bee-ra na oo-voo-mee-lee-voo hoo-sheen-da"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "swahili": "Acha nuru yako ing'ae kwa mwangaza.", "pronunciation": "a-cha noo-roo ya-ko een-ga-e kwa mwan-ga-za"},
            {"english": "Inspire others by your actions.", "swahili": "Wahamasisha wengine kwa matendo yako.", "pronunciation": "wa-ha-ma-see-sha wen-ge-ne kwa ma-ten-do ya-ko"},
            {"english": "Be the change you want to see.", "swahili": "Kuwa mabadiliko unayotaka kuona.", "pronunciation": "koo-wa ma-ba-dee-lee-ko oo-na-yo-ta-ka koo-o-na"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "swahili": "Chagua chanya kila siku.", "pronunciation": "cha-goo-a chan-ya kee-la see-koo"},
            {"english": "Good vibes only.", "swahili": "Mawazo mazuri tu.", "pronunciation": "ma-wa-zo ma-zoo-ree too"},
            {"english": "Life is what you make it.", "swahili": "Maisha ni kile unachoyafanya.", "pronunciation": "ma-ee-sha nee kee-le oo-na-cho-ya-fan-ya"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "swahili": "Kuwa jasiri, chukua hatua ya kwanza.", "pronunciation": "koo-wa ja-see-ree, choo-koo-a ha-too-a ya kwan-za"},
            {"english": "Courage is not the absence of fear.", "swahili": "Ujasiri si kutokuwepo kwa woga.", "pronunciation": "oo-ja-see-ree see koo-to-koo-we-po kwa wo-ga"},
            {"english": "Face your fears head on.", "swahili": "Kabiliana na hofu zako moja kwa moja.", "pronunciation": "ka-bee-lee-a-na na ho-foo za-ko mo-ja kwa mo-ja"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "swahili": "Kuwa mwema kwa kila mtu unayekutana naye.", "pronunciation": "koo-wa mwe-ma kwa kee-la m-too oo-na-ye-koo-ta-na na-ye"},
            {"english": "Kindness costs nothing, means everything.", "swahili": "Wema haugharimu chochote, maana yake ni yote.", "pronunciation": "we-ma how-gha-ree-moo cho-cho-te, ma-a-na ya-ke nee yo-te"},
            {"english": "Spread kindness wherever you go.", "swahili": "Enea wema kokote uendako.", "pronunciation": "e-ne-a we-ma ko-ko-te oo-en-da-ko"},
        ],
        "Patience": [
            {"english": "Good things take time.", "swahili": "Mambo mazuri huchukua muda.", "pronunciation": "mam-bo ma-zoo-ree hoo-choo-koo-a moo-da"},
            {"english": "Wait patiently, trust the process.", "swahili": "Subiri kwa uvumilivu, amini mchakato.", "pronunciation": "soo-bee-ree kwa oo-voo-mee-lee-voo, a-mee-nee m-cha-ka-to"},
            {"english": "Rome wasn't built in a day.", "swahili": "Roma haikujengwa kwa siku moja.", "pronunciation": "ro-ma ha-ee-koo-jeng-wa kwa see-koo mo-ja"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "swahili": "Samehe na ujiweke huru.", "pronunciation": "sa-me-he na oo-jee-we-ke hoo-roo"},
            {"english": "Let go of grudges, find peace.", "swahili": "Acha kichukizo, pata amani.", "pronunciation": "a-cha kee-choo-kee-zo, pa-ta a-ma-nee"},
            {"english": "Forgiveness is a gift to yourself.", "swahili": "Msamaha ni zawadi kwako mwenyewe.", "pronunciation": "m-sa-ma-ha nee za-wa-dee kwa-ko mwe-nye-we"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "swahili": "Una nguvu kuliko unavyojua.", "pronunciation": "oo-na ngoo-voo koo-lee-ko oo-na-vyo-ju-a"},
            {"english": "Inner strength comes from within.", "swahili": "Nguvu ya ndani inatoka ndani.", "pronunciation": "ngoo-voo ya n-da-nee ee-na-to-ka n-da-nee"},
            {"english": "Challenges make you stronger.", "swahili": "Changamoto hukufanya uwe na nguvu zaidi.", "pronunciation": "chan-ga-mo-to hoo-koo-fan-ya oo-we na ngoo-voo za-ee-dee"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "swahili": "Pata shangwe katika kila wakati.", "pronunciation": "pa-ta shang-we ka-tee-ka kee-la wa-ka-tee"},
            {"english": "Joy is contagious, spread it.", "swahili": "Shangwe inaambukiza, eneza.", "pronunciation": "shang-we ee-na-am-boo-kee-za, e-ne-za"},
            {"english": "Dance like nobody's watching.", "swahili": "Cheza kama hakuna anayekutazama.", "pronunciation": "che-za ka-ma ha-koo-na a-na-ye-koo-ta-za-ma"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "swahili": "Pata usawa katika maisha yako.", "pronunciation": "pa-ta oo-sa-wa ka-tee-ka ma-ee-sha ya-ko"},
            {"english": "Work hard, rest well.", "swahili": "Fanya kazi kwa bidii, pumzika vizuri.", "pronunciation": "fan-ya ka-zee kwa bee-dee, poom-zee-ka vee-zoo-ree"},
            {"english": "Too much of anything is not good.", "swahili": "Kupita kiasi cha kitu chochote si kizuri.", "pronunciation": "koo-pee-ta kee-a-see cha kee-too cho-cho-te see kee-zoo-ree"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "swahili": "Ukuaji hutokea nje ya eneo lako la faraja.", "pronunciation": "oo-koo-a-jee hoo-to-ke-a n-je ya e-ne-o la-ko la fa-ra-ja"},
            {"english": "Embrace change, grow stronger.", "swahili": "Kumbatia mabadiliko, kua na nguvu zaidi.", "pronunciation": "koom-ba-tee-a ma-ba-dee-lee-ko, koo-a na ngoo-voo za-ee-dee"},
            {"english": "Every challenge is a chance to grow.", "swahili": "Kila changamoto ni nafasi ya kukua.", "pronunciation": "kee-la chan-ga-mo-to nee na-fa-see ya koo-koo-a"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "swahili": "Pata kusudi lako, lishike.", "pronunciation": "pa-ta koo-soo-dee la-ko, lee-shee-ke"},
            {"english": "Your life has meaning.", "swahili": "Maisha yako yana maana.", "pronunciation": "ma-ee-sha ya-ko ya-na ma-a-na"},
            {"english": "Live with intention, not accident.", "swahili": "Ishi kwa makusudi, si kwa bahati.", "pronunciation": "ee-shee kwa ma-koo-soo-dee, see kwa ba-ha-tee"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "swahili": "Kuwa katika wakati huu.", "pronunciation": "koo-wa ka-tee-ka wa-ka-tee hoo-oo"},
            {"english": "Breathe deeply, stay grounded.", "swahili": "Pumua kwa kina, kaa chini.", "pronunciation": "poo-moo-a kwa kee-na, ka-a chee-nee"},
            {"english": "Notice the little things around you.", "swahili": "Angalia vitu vidogo vidogo vinavyokuzunguka.", "pronunciation": "an-ga-lee-a vee-too vee-do-go vee-do-go vee-na-vyo-koo-zoo-ngoo-ka"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

def generate_google_tts(text: str, voice_or_lang: str, output_path: str) -> bool:
    """Fallback TTS using Google Translate TTS if Edge TTS fails."""
    import urllib.request
    import urllib.parse

    lang_code = "en"
    voice_lower = str(voice_or_lang).lower()
    if voice_lower.startswith("en"):
        lang_code = "en"
    elif "-" in str(voice_or_lang):
        part = str(voice_or_lang).split("-")[0].lower()
        if part == "zh":
            lang_code = "zh-CN"
        elif part == "fil":
            lang_code = "tl"
        elif part == "nb":
            lang_code = "no"
        else:
            lang_code = part
    else:
        lang_code = voice_lower

    clean_text = text.replace("*", "").replace("#", "").strip()
    if not clean_text:
        return False

    try:
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(clean_text)}&tl={lang_code}&client=tw-ob"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if len(data) > 200:
            with open(output_path, "wb") as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"  Google TTS fallback error ({lang_code}): {e}")
    return False


async def generate_single_audio(text: str, voice: str, output_path: str, retries: int = 2):
    """Generate audio using Edge TTS with automatic Google TTS fallback"""
    import edge_tts
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            if Path(output_path).exists() and Path(output_path).stat().st_size > 300:
                return True
        except Exception as e:
            if attempt == retries - 1:
                print(f"  Edge TTS notice ({e}), switching to Google TTS fallback...")

    # Fallback to Google TTS
    if generate_google_tts(text, voice, output_path):
        return True

    return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["swahili"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a]apad=pad_dur=0.5[a0];[a0][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    swahili = phrase_data.get("swahili", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(swahili, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Swahili Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY SWAHILI"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_swahili: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER SWAHILI", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_swahili, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 SWAHILI PHRASES"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY SWAHILI", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_swahili: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Swahili in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_swahili})",
        f"60 Swahili Phrases for {category_english} | Speak Swahili Like a Native! ({category_swahili})",
        f"Master Swahili {category_english} | 60 Essential Swahili Phrases with Pronunciation | Velocity Swahili",
        f"Swahili Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Swahili Fluently | {category_english} Phrases | English + Swahili + Pronunciation",
    ]

    description = f"""\U0001F1F0\U0001F1EA Learn Swahili with Velocity Swahili! \U0001F1F0\U0001F1EA

In this video, you'll learn 60 essential Swahili phrases about {category_english} ({category_swahili}).
Perfect for beginners and intermediate learners!

\U0001F4DA WHAT YOU'LL LEARN:
\u2022 60 practical {category_english} phrases in Swahili
\u2022 Correct pronunciation guide
\u2022 Natural pauses for speaking practice
\u2022 Common expressions used by native speakers

\U0001F551 VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
\U0001F4DD ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Swahili: {phrase['swahili']}
    Pronunciation: {phrase['pronunciation']}
"""

    description += """
\U0001F3AF PERFECT FOR:
\u2022 Swahili beginners wanting to expand vocabulary
\u2022 Intermediate learners practicing pronunciation
\u2022 Anyone interested in Swahili language and culture
\u2022 Language enthusiasts and polyglots
\u2022 Students preparing for exams

\U0001F4A1 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

\U0001F514 SUBSCRIBE for more Swahili learning content!
\U0001F44D LIKE this video if you found it helpful!
\U0001F4AC COMMENT which phrases you want to learn next!

\U0001F4F1 FOLLOW VELOCITY SWAHILI:
[Add your social media links here]

\U0001F3B5 MUSIC:
[Add music credits if applicable]

\U0001F4D6 RELATED VIDEOS:
\u2022 Swahili Motivation Phrases
\u2022 Swahili Love Expressions
\u2022 Basic Swahili Greetings

#LearnSwahili #SwahiliPhrases #SwahiliLanguage #{category_english.replace(' ', '')} #VelocitySwahili #SwahiliForBeginners #SpeakSwahili #SwahiliVocabulary #Pronunciation #LanguageLearning #Swahili101 #SwahiliLesson

---
\u00A9 Velocity Swahili - Making Swahili learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Swahili",
            "Swahili Phrases",
            "Swahili Language",
            category_english,
            "Velocity Swahili",
            "Swahili for Beginners",
            "Speak Swahili",
            "Swahili Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Swahili 101",
            "Swahili Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_swahili": category_swahili,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_SWAHILI[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['swahili']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_SWAHILI[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_SWAHILI[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_SWAHILI[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Swahili: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Swahili", "Swahili Phrases", "Swahili", category_english, "Velocity Swahili"],
        "category_english": category_english,
        "category_swahili": CATEGORIES_SWAHILI[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Swahili")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Swahili YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY SWAHILI - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_SWAHILI[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)