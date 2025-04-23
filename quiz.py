import json
from moviepy import CompositeVideoClip, ImageClip, TextClip, AudioClip, concatenate_audioclips, concatenate_videoclips, AudioFileClip,VideoFileClip, CompositeAudioClip, vfx
import pyttsx3
import os
import numpy as np
import random
import time
import json
import re
from dotenv import load_dotenv


from together import Together
from elevenlabs import  ElevenLabs, VoiceSettings

# ─── ELEVENLABS SETUP ──────────────────────────────────

load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=api_key)  # initialize client once

# pick your favorite voice from GET /v1/voices
voice_id      = "pNInz6obpgDQGcFmaJgB"   # default ElevenLabs voice ID :contentReference[oaicite:4]{index=4}
model_id      = "eleven_flash_v2_5"
output_format = "mp3_44100_128"                # high‑quality WAV output :contentReference[oaicite:5]{index=5}
voice_settings=VoiceSettings(
        speed=0.9,            # 10% faster than normal :contentReference[oaicite:6]{index=6}
        stability=0.8,        # fairly consistent tone :contentReference[oaicite:7]{index=7}
        similarity_boost=0.7, # close to base voice :contentReference[oaicite:8]{index=8}
        style=0.3,            # a touch of style exaggeration :contentReference[oaicite:9]{index=9}
        use_speaker_boost=True
    )



gen_client = Together() # auth defaults to os.environ.get("TOGETHER_API_KEY")

response = gen_client.chat.completions.create(
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    messages=[{"role": "user", "content": '''Generate 3 easy to medium level geography trivia multiple choice questions with 4 options each, and provide the correct answer. But the format should be in JSON - for example [
    {
      "question": "What is the capital of France?",
      "options": ["Paris", "London", "Berlin", "Rome"],
      "answer": "Paris"
    }
  ]
  '''}],
)

raw = response.choices[0].message.content

# 1) Try to grab JSON inside ``` code fences
m = re.search(r'```(?:json)?\s*(\[\s*[\s\S]*?\])\s*```', raw)
if m:
    json_str = m.group(1)
else:
    # 2) Fallback: grab from first '[' to last ']'
    start = raw.find('[')
    end   = raw.rfind(']')
    json_str = raw[start:end+1]

# Now parse
quiz_data = json.loads(json_str)

# Save it
with open('quiz_data.json', 'w') as f:
    json.dump(quiz_data, f, indent=4)

# accounts = [
#     "dumpmedia3+abc@gmail.com",
#     "dumpmedia3+def@gmail.com",
#     # add more as needed...
# ]
# password = "hri2.03.0"
# current_account = 0

# def login_with(idx):
#     global fy, login
#     fy = fymod.FakeYou2()
#     login = fy.login(accounts[idx], password)
#     print("Logged in as:", login.username)

# def safe_say(text, model_token):
#     """Try to generate TTS; on failure, rotate to next account and retry."""
#     global current_account
#     attempts = 0
#     while attempts < len(accounts):
#         try:
#             return fy.say(text, tts_model_token=model_token)
#         except Exception as e:
#             print(f"TTS failed on {accounts[current_account]}: {e}")
#             current_account = (current_account + 1) % len(accounts)
#             login_with(current_account)
#             attempts += 1
#     raise RuntimeError("All TTS accounts failed.")

# def safe_say_with_retries(text, model_token, max_attempts=5, delay=10):
#     """
#     Calls safe_say(text, model_token), retrying up to max_attempts
#     with a delay (in seconds) between attempts.
#     """
#     attempt = 1
#     while True:
#         try:
#             return safe_say(text, model_token)
#         except Exception as e:
#             if attempt >= max_attempts:
#                 # after exhausting retries, re-raise
#                 raise RuntimeError(f"TTS failed after {max_attempts} attempts: {e}") from e
#             print(f"TTS attempt {attempt} failed: {e}. Retrying in {delay}s…")
#             time.sleep(delay)
#             attempt += 1

def make_silence(duration=0.5, fps=44100):
    """Return a silent AudioClip of given duration."""
    return AudioClip(lambda t: np.zeros((np.atleast_1d(t).shape[0], 2)), duration=duration, fps=fps)

# ── ADDED ──
# Prepare for timeline-based composition
video_overlays = []
audio_clips    = []
current_t = 0.0


countdown_radius = 50  # Adjust circle size as needed
diameter = countdown_radius * 2
circle_color = (255, 255, 255)  # White circle color

tick_sound_path = "resources/audio/Clock Ticking Sound Effect.mp3"
tick_sound = AudioFileClip(tick_sound_path)

correct_sound_path = "resources/audio/correct answer.mp3"
correct_sound = AudioFileClip(correct_sound_path)

# fy = fymod.FakeYou2()
# login = fy.login("dumpmedia3@gmail.com", password)
# print("Logged in as:", login.username)
# voices = fy.get_voices()
# token = ""
# for modelTokens, title in zip(voices.modelTokens, voices.title):
#     if 'Sexy Angie' in title:
#         token = modelTokens
#         break

# Load quiz data
with open('quiz_data.json', 'r') as f:
    quiz_data = json.load(f)

# Video settings
W, H = 720, 1280         # Video resolution
bg_color = (0, 0, 0)       # Background color (black)
margin = 20                # General margin for placing texts

# Font path (adjust according to your directory structure)
font_path = "./resources/LuckiestGuy-Regular.ttf"
font_path2 = "./resources/WinkyRough-VariableFont_wght.ttf"

for idx, item in enumerate(quiz_data):
    question = item['question']
    options = item['options']
    answer = item['answer']

    s_text = "If you can answer all of these questions, you can be my good boy."
    if idx == 0:
        s_wav = f"audio_s_{idx}.wav"
        if not os.path.exists(s_wav):
            print(f"Generating TTS for {s_wav}")
            audio_stream = client.text_to_speech.convert(
                text=s_text,
                voice_id=voice_id,
                model_id=model_id,
                voice_settings=voice_settings,
                output_format=output_format
            )
            with open(s_wav, "wb") as f:
                for chunk in audio_stream:
                    f.write(chunk)
                
        audio_s_clip = AudioFileClip(s_wav)
        audio_clips.append(audio_s_clip.with_start(current_t))
        current_t += audio_s_clip.duration + 0.5 

        start_clip = TextClip(
            text=s_text,
            font=font_path,
            font_size=70,
            color='white',
            method='caption',
            stroke_color='black',
            stroke_width=8,
            size=(W - 2 * margin, None),
            margin=(0, 8),                   # vertical padding for stroke
            vertical_align='top'             # anchor text to top of box
        ).with_duration(audio_s_clip.duration+0.5)

        start_height = start_clip.get_frame(0).shape[0]
        total_content_height = start_height
        start_y = (H - total_content_height) // 2

        start_clip = start_clip.with_position(('center', start_y))
        video_overlays.append(start_clip)

    # --- Generate TTS for question + options using safe_say ---
    q_wav = f"audio_q_{idx}.wav"
    if not os.path.exists(q_wav):
        print(f"Generating TTS for {q_wav}")
        audio_stream = client.text_to_speech.convert(
            text="Question: " + question,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=voice_settings,
            output_format=output_format
        )
        with open(q_wav, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
    audio_q_clip = AudioFileClip(q_wav)

    option_clips_audio = []
    for i, opt in enumerate(options):
        o_wav = f"audio_opt_{idx}_{i}.wav"
        if not os.path.exists(o_wav):
            print(f"Generating TTS for {o_wav}")
            audio_stream = client.text_to_speech.convert(
                text=opt,
                voice_id=voice_id,
                model_id=model_id,
                voice_settings=voice_settings,
                output_format=output_format
            )
            with open(o_wav, "wb") as f:
                for chunk in audio_stream:
                    f.write(chunk)
        option_clips_audio.append(AudioFileClip(o_wav))

    sil = make_silence(0.5, audio_q_clip.fps)

    all_audio = [audio_q_clip]
    for opt_clip in option_clips_audio:
        all_audio += [sil, opt_clip]
    full_q_audio = concatenate_audioclips(all_audio)

    # Add "subscribe" shout-out on first question
    if idx == 0:
        text = 'Subscribe is you like femboys!'
        t_wav = f"audio_t_{idx}.wav"
        if not os.path.exists(t_wav):
            print(f"Generating TTS for {t_wav}")
            audio_stream = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                voice_settings=voice_settings,
                output_format=output_format
            )
            with open(t_wav, "wb") as f:
                for chunk in audio_stream:
                    f.write(chunk)
        audio_t_clip = AudioFileClip(t_wav).with_start(full_q_audio.duration+3)
        mixed_audio = CompositeAudioClip([full_q_audio, audio_t_clip])
    else:
        mixed_audio = full_q_audio

    # Create the question text clip
    question_clip = TextClip(
        text=question,
        font=font_path,
        font_size=70,
        color='white',
        method='caption',
        stroke_color='black',
        stroke_width=8,
        size=(W - 2 * margin, None),
        margin=(0, 8),                   # vertical padding for stroke
        vertical_align='top'             # anchor text to top of box
    ).with_duration(full_q_audio.duration+6)
    question_clip = CompositeVideoClip([question_clip.with_effects([vfx.SlideIn( 0.1, 'bottom')])])

    # Create option text clips with shaking
    option_clips = []
    option_fontsize = 50
    option_width = (W - 3 * margin) // 2
    for i, opt in enumerate(options):
        clip = TextClip(
            text=opt,
            font=font_path,
            font_size=option_fontsize,
            color='yellow',
            method='caption',
            stroke_color='black',
            stroke_width=4,
            size=(option_width, None),
            margin=(0, 8), 
        ).with_duration(full_q_audio.duration+6)

        freq = random.uniform(2, 4)
        amp = random.uniform(2, 5)
        phase = random.uniform(0, 2 * np.pi)
        def make_shake(freq, amp, phase):
            return lambda t: amp * np.sin(2 * np.pi * freq * t + phase)
        shake = make_shake(freq, amp, phase)
        clip = CompositeVideoClip([clip.with_effects([vfx.SlideIn( 0.1, 'bottom')])])
        clip = clip.rotated(angle=shake, unit='deg')
        option_clips.append(clip)

    # Measure sizes
    question_height = question_clip.get_frame(0).shape[0]
    option_height = option_clips[0].get_frame(0).shape[0]
    
    spacing = 40
    total_content_height = question_height + spacing + 2 * option_height + spacing
    start_y = (H - total_content_height) // 2

    # Position question & options
    question_clip = question_clip.with_position(('center', start_y)).with_start(current_t)
    video_overlays.append(question_clip)

    for i, clip in enumerate(option_clips):
        row = i // 2
        col = i % 2
        x_pos = W // 4 if col == 0 else 3 * W // 4
        y_pos = start_y + question_height + spacing + row * (option_height + spacing)
        video_overlays.append(clip.with_position((x_pos - option_width // 2, y_pos)).with_start(current_t))

    # Countdown
    countdown_start_time = current_t + full_q_audio.duration + 1

    audio_clips.append(tick_sound.with_start(countdown_start_time))


    for i in range(5, 0, -1):
        start_time = countdown_start_time + (5 - i)
        
        # 1) Create a white circle image as the background for the number
        circle_img = np.zeros((diameter, diameter, 4), dtype=np.uint8)
        yy, xx = np.ogrid[:diameter, :diameter]
        mask = (xx - countdown_radius)**2 + (yy - countdown_radius)**2 <= countdown_radius**2
        circle_img[mask] = (*circle_color, 255)  # Set circle color (white)
        circle_clip = (
            ImageClip(circle_img)
            .with_duration(1)
            .with_start(start_time)
            .with_position(('center', 130))
        )
        video_overlays.append(circle_clip)

        # 2) Overlay the countdown number on top of the circle
        cnt = (
            TextClip(
                text=str(i),
                font=font_path2,
                font_size=60,
                color='red',
                method='caption',
                size=(diameter, diameter),  # Use the circle's diameter for size
        
            )
            .with_duration(1)
            .with_start(start_time)
            .with_position(('center', 130))
        )
        video_overlays.append(cnt)

    # Add the audio for question + options
    audio_clips.append(mixed_audio.with_start(current_t))

    # Advance timeline
    current_t += full_q_audio.duration + 6

    # --- Answer segment ---
    a_wav = f"audio_a_{idx}.wav"
    if not os.path.exists(a_wav):
        answer_text = f"Correct option is {answer}."
        print(f"Generating TTS for {a_wav}")
        audio_stream = client.text_to_speech.convert(
            text=answer_text,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=voice_settings,
            output_format=output_format
        )
        with open(a_wav, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
    audio_a_clip = AudioFileClip(a_wav)

    answer_label_clip = TextClip(
        text="Answer",
        font=font_path,
        font_size=80,
        color='white',
        method='caption',
        stroke_color='black',
        stroke_width=8,
        size=(W - 2 * margin, 130)
    ).with_duration(audio_a_clip.duration+1).with_start(current_t)

    answer_text_clip = TextClip(
        text=item['answer'],
        font=font_path,
        font_size=60,
        color='yellow',
        method='caption',
        stroke_color='black',
        stroke_width=4,
        size=(W - 2 * margin, 130)
    ).with_duration(audio_a_clip.duration+1).with_start(current_t)  # approx positioning inside

    audio_clips.append(
    correct_sound.with_start(current_t)  # starts exactly when answer text shows
    )

    # center them vertically
    label_h = answer_label_clip.get_frame(0).shape[0]
    text_h  = answer_text_clip.get_frame(0).shape[0]
    total_h = label_h + spacing + text_h
    y0 = (H - total_h) // 2
    video_overlays.append(answer_label_clip.with_position(('center', y0)))
    video_overlays.append(answer_text_clip.with_position(('center', y0 + label_h + spacing)))

    audio_clips.append(audio_a_clip.with_start(current_t))
    current_t += audio_a_clip.duration + 1

# ── ADDED ──
# Now that current_t == total duration, load & loop the background once:
bg_path = "C:/Users/Hrithik/OneDrive/Documents/AI/Fnite/trivia_quiz_project/resources/Video/subway1.mp4"
bg = VideoFileClip(bg_path)
# if bg.duration < current_t:
#     background = bg.fx(vfx.loop, duration=current_t)
# else:
background = bg.subclipped(0, current_t)
background = background.resized((W, H)).with_fps(24)
video_overlays.insert(0, background)

from moviepy.audio.fx import MultiplyVolume
from moviepy import afx

bg_music_path = r"C:/Users/Hrithik/OneDrive/Documents/AI/Fnite/Resources/Audio/Wii Music - Gaming Background Music (HD).mp3"
bg_music = AudioFileClip(bg_music_path)

# 1) Loop or trim it so it covers the whole quiz (current_t is your total duration)

bg_music = bg_music.subclipped(0, current_t)

print(type(bg_music))

# 2) Lower the volume so voices stay clear
bg_music = bg_music.with_effects([afx.MultiplyVolume(0.2)])

# 3) Start it at t=0
bg_music = bg_music.with_start(0)

# Finally, include it in the mix
audio_clips.insert(0, bg_music)

# Final composite
final = CompositeVideoClip(video_overlays, size=(W, H))\
            .with_duration(current_t)\
            .with_audio(CompositeAudioClip(audio_clips))

final.write_videofile("output/quiz_video_continuous_bg.mp4", fps=24)
