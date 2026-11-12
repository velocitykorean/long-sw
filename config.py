"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY SWAHILI"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "SWAHILI"
HANDLE = "@velocityswahili"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'sw',
 'name': 'Swahili',
 'native_name': 'Kiswahili',
 'history_key': 'swahili',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'sw-KE-RafikiNeural',
 'native_fallback_voice': 'sw-KE-ZuriNeural',
 'native_engine': 'edge',
 'native_lang_code': 'sw',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'KISWAHILI',
 'translit_label': 'SAY IT LIKE',
 'flag': 'ke',
 'greeting': 'Habari!',
 'encouragement': 'Vizuri sana!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Motisha',
 'Love': 'Upendo',
 'Success': 'Mafanikio',
 'Wisdom': 'Hekima',
 'Happiness': 'Furaha',
 'Self Improvement': 'Kujiboresha',
 'Gratitude': 'Shukrani',
 'Friendship': 'Urafiki',
 'Hope': 'Tumaini',
 'Creativity': 'Ubunifu',
 'Inner Peace': 'Amani ya Ndani',
 'Confidence': 'Kujiamini',
 'Perseverance': 'Uvumilivu',
 'Inspiration': 'Msukumo',
 'Positive Life': 'Maisha Chanya',
 'Courage': 'Ujasiri',
 'Kindness': 'Wema',
 'Patience': 'Subira',
 'Forgiveness': 'Msamaha',
 'Strength': 'Nguvu',
 'Joy': 'Shangwe',
 'Balance': 'Usawa',
 'Growth': 'Ukuaji',
 'Purpose': 'Kusudi',
 'Mindfulness': 'Kujitambua',
 'Travel & Airport': 'Usafiri na Uwanja wa Ndege',
 'Ordering Food & Dining': 'Kuagiza Chakula na Kulia',
 'Shopping & Prices': 'Ununuzi na Bei',
 'Asking for Directions': 'Kuuliza Njia',
 'Hotel & Accommodation': 'Hoteli na Malazi',
 'Daily Routine': 'Ratiba ya Kila Siku',
 'Meeting People & Greetings': 'Kukutana na Watu na Salamu',
 'Emergency & Health': 'Dharura na Afya',
 'Public Transportation': 'Usafiri wa Umma',
 'Work & Office': 'Kazi na Ofisi',
 'Weather & Small Talk': 'Hali ya Hewa na Mazungumzo Madogo',
 'Coffee Shop & Bakery': 'Duka la Kahawa na Mkate',
 'Family & Home': 'Familia na Nyumbani',
 'Hobbies & Free Time': 'Mambo ya Kufanya na Wakati wa Upole',
 'Dating & Romance': 'Uchumba na Mapenzi',
 'Phone Calls & Messages': 'Simu na Ujumbe',
 'Banking & Money': 'Benki na Pesa',
 'Doctor & Pharmacy': 'Daktari na Dawa',
 'Sports & Fitness': 'Michezo na Mazoezi',
 'Celebrations & Parties': 'Sherehe na Mikutano',
 'Feelings & Emotions': 'Hisia na Machozi',
 'Agreeing & Disagreeing': 'Kukubali na Kukataa',
 'Making Plans': 'Kupanga Mipango',
 'Common Native Slang': 'Lugha ya Mitaani ya Kawaida',
 'Cultural Traditions': 'Jadi za Kitamaduni'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnswahili',
 '#swahililessons',
 '#swahiliforbeginners',
 '#languagelearning',
 '#swahilivocabulary',
 '#velocityswahili',
 '#dailyswahili',
 '#swahili',
 '#learnlanguages',
 '#speakswahili']
# ==== HASHTAGS END ====
