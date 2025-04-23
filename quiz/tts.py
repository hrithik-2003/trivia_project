import os
import random
from pathlib import Path
from hashlib import md5

from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings
from moviepy import AudioFileClip

from config import (
    AUDIO_DIR,
    VOICE_IDS,
    ELEVENLABS_MODEL_ID,
    ELEVENLABS_OUTPUT_FORMAT,
    VOICE_SETTINGS,
)

load_dotenv()

# Initialize ElevenLabs client once
a_pi_key = os.getenv("ELEVENLABS_API_KEY")
_client = ElevenLabs(api_key=a_pi_key)

def _cache_path_for(text: str, voice_id: str) -> Path:
    """
    Generate a deterministic cache filename based on text + voice_id.
    """
    digest = md5(f"{voice_id}:{text}".encode("utf-8")).hexdigest()
    return AUDIO_DIR / f"{digest}.wav"

def say(text: str, voice_id: str = None) -> AudioFileClip:
    """
    Generate (or load from cache) a TTS clip for `text`, using a random or specified voice.

    Returns:
        AudioFileClip
    """
    if voice_id is None:
        voice_id = random.choice(VOICE_IDS)

    cache_path = _cache_path_for(text, voice_id)
    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        stream = _client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=ELEVENLABS_MODEL_ID,
            voice_settings=VoiceSettings(**VOICE_SETTINGS),
            output_format=ELEVENLABS_OUTPUT_FORMAT,
        )
        with open(cache_path, "wb") as f:
            for chunk in stream:
                f.write(chunk)

    return AudioFileClip(str(cache_path))