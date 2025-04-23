from pathlib import Path

# === Project Paths ===
BASE_DIR = Path(__file__).parent.parent
RESOURCES_DIR = BASE_DIR / "resources"
AUDIO_DIR = RESOURCES_DIR / "audio"
VIDEO_DIR = RESOURCES_DIR / "video"
FONTS_DIR = RESOURCES_DIR / "fonts"
OUTPUT_DIR = BASE_DIR / "output"

# === Video Settings ===
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280
FPS = 24
MARGIN = 20

# === Audio Assets ===
TICK_SOUND = AUDIO_DIR / "Clock Ticking Sound Effect.mp3"
CORRECT_SOUND = AUDIO_DIR / "correct answer.mp3"

# === Background Videos ===
BACKGROUND_VIDEOS = [
    VIDEO_DIR / "subway1.mp4",
]

# === Text Templates ===
INTRO_TEMPLATES = [
    "If you can answer all of these questions, you can be my good boy.",
    "Think you've got what it takes? Let's find out!",
]
SHOUTOUT_TEMPLATES = [
    "Subscribe if you like femboys!",
    "Don't forget to hit that like button!",
]
ANSWER_TEMPLATES = [
    "Correct option is {answer}.",
]


# === Countdown Settings ===
COUNTDOWN_RADIUS = 50  # pixels
COUNTDOWN_DURATION = 1  # seconds for each countdown number
COUNTDOWN_START = 5     # start counting from 5
CIRCLE_COLOR = (255, 255, 255)  # white circle color


# === TTS / ElevenLabs Settings ===
VOICE_IDS = [
    "pNInz6obpgDQGcFmaJgB",  # default ElevenLabs
    # add more voice IDs here
]
ELEVENLABS_MODEL_ID = "eleven_flash_v2_5"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"
VOICE_SETTINGS = {
    "speed": 0.9,
    "stability": 0.8,
    "similarity_boost": 0.7,
    "style": 0.3,
    "use_speaker_boost": True,
}


# === Silence Padding ===
SILENCE_DURATION = 0.5  # seconds of padding between clips
