import json
from moviepy import CompositeVideoClip, ColorClip, TextClip, AudioClip,concatenate_audioclips, concatenate_videoclips, AudioFileClip,VideoFileClip, CompositeAudioClip
import pyttsx3
import os
import numpy as np
import random
import time

import Voice.fakeyou.fakeyou2 as fymod
from importlib import reload
import Voice.fakeyou.util.service as service_module


reload(service_module)
reload(fymod)

accounts = [
    "dumpmedia3+abc@gmail.com",
    "dumpmedia3+def@gmail.com",
    # add more as needed...
]
password = "hri2.03.0"
current_account = 0

def login_with(idx):
    global fy, login
    fy = fymod.FakeYou2()
    login = fy.login(accounts[idx], password)
    print("Logged in as:", login.username)

def safe_say(text, model_token):
    """Try to generate TTS; on failure, rotate to next account and retry."""
    global current_account
    attempts = 0
    while attempts < len(accounts):
        try:
            return fy.say(text, tts_model_token=model_token)
        except Exception as e:
            print(f"TTS failed on {accounts[current_account]}: {e}")
            current_account = (current_account + 1) % len(accounts)
            login_with(current_account)
            attempts += 1
    raise RuntimeError("All TTS accounts failed.")

def safe_say_with_retries(text, model_token, max_attempts=5, delay=10):
    """
    Calls safe_say(text, model_token), retrying up to max_attempts
    with a delay (in seconds) between attempts.
    """
    attempt = 1
    while True:
        try:
            return safe_say(text, model_token)
        except Exception as e:
            if attempt >= max_attempts:
                # after exhausting retries, re-raise
                raise RuntimeError(f"TTS failed after {max_attempts} attempts: {e}") from e
            print(f"TTS attempt {attempt} failed: {e}. Retrying in {delay}s…")
            time.sleep(delay)
            attempt += 1

def make_silence(duration=0.5, fps=44100):
    """Return a silent AudioClip of given duration."""
    return AudioClip(lambda t: np.zeros((np.atleast_1d(t).shape[0], 2)), duration=duration, fps=fps)


fy = fymod.FakeYou2()
login = fy.login("dumpmedia3@gmail.com", password)
print("Logged in as:", login.username)
voices = fy.get_voices()
token = ""
for modelTokens, title in zip(voices.modelTokens, voices.title):
    if 'Sexy Beatrice (British Accent)' in title:
        token = modelTokens
        break

# Load quiz data
with open('quiz_data.json', 'r') as f:
    quiz_data = json.load(f)

clips = []

# Video settings
W, H = 720, 1280         # Video resolution
bg_color = (0, 0, 0)       # Background color (black)
margin = 20                # General margin for placing texts

# Font path (adjust according to your directory structure)
font_path = "./resources/WinkyRough-VariableFont_wght.ttf"

for idx, item in enumerate(quiz_data):
    question = item['question']
    options = item['options']
    answer = item['answer']

    # --- Generate TTS for question + options using safe_say ---
    # … inside your loop, replace the single safe_say(...) with:

    # 1) TTS the question…
    q_wav = f"audio_q_{idx}.wav"
    if not os.path.exists(q_wav):
        tts_q = safe_say_with_retries("Question: " + question, token)
        with open(q_wav,"wb") as f: f.write(tts_q.content)
    audio_q_clip = AudioFileClip(q_wav)

    # 2) For each option, TTS + load
    option_clips_audio = []
    for i, opt in enumerate(options):
        o_wav = f"audio_opt_{idx}_{i}.wav"
        if not os.path.exists(o_wav):
            tts_o = safe_say_with_retries(f"{opt}", token)
            with open(o_wav,"wb") as f: f.write(tts_o.content)
        option_clips_audio.append(AudioFileClip(o_wav))

    print('bruh')
    # 3) Build a 0.5 s silent clip
    sil = make_silence(0.5, audio_q_clip.fps)

    # 4) Concatenate: question → silence → opt A → silence → opt B → … 
    print('abc')

    all_audio = [audio_q_clip]
    for opt_clip in option_clips_audio:
        all_audio += [sil, opt_clip]

    print('def')

    full_q_audio = concatenate_audioclips(all_audio)

    # Create a background color clip
    background = ColorClip(size=(W, H), color=bg_color, duration=full_q_audio.duration+6)

    # Create the question text clip
    question_clip = TextClip(
        text=question,
        font=font_path,
        font_size=70,
        color='white',
        method='caption',
        size=(W - 2 * margin, None)
    ).with_duration(full_q_audio.duration+6)
    

    if idx ==0:
        t_wav = f"audio_t_{idx}.wav"
        if not os.path.exists(t_wav):
            text = "Subscribe if you like femboys!"
            tts_t = safe_say_with_retries(text, token)
            with open(t_wav, "wb") as f:
                f.write(tts_t.content)
        audio_t_clip = AudioFileClip(t_wav).with_start(full_q_audio.duration+3)

        mixed_audio = CompositeAudioClip([full_q_audio, audio_t_clip])
    else:
        mixed_audio = full_q_audio

    # Measure question height
    question_frame = question_clip.get_frame(0)
    question_height = question_frame.shape[0]

    # Create option text clips with shaking effect
    option_fontsize = 50
    option_color = "yellow"
    option_width = (W - 3 * margin) // 2
    option_clips = []
    for i, opt in enumerate(options):
        clip = TextClip(
            text=opt,
            font=font_path,
            font_size=option_fontsize,
            color=option_color,
            method='caption',
            size=(option_width, None)
        ).with_duration(full_q_audio.duration+6)

        # Define a unique shake function for each option
        freq = random.uniform(2, 4)  # Frequency of shake
        amp = random.uniform(2, 5)   # Amplitude of shake in degrees
        phase = random.uniform(0, 2 * np.pi)  # Phase shift

        def make_shake(freq, amp, phase):
            return lambda t: amp * np.sin(2 * np.pi * freq * t + phase)

        shake = make_shake(freq, amp, phase)
        clip = clip.rotated( angle=shake, unit='deg')
        option_clips.append(clip)

    # Measure option height
    option_frame = option_clips[0].get_frame(0)
    option_height = option_frame.shape[0]

    # Calculate total content height
    spacing = 40  # spacing between question and options, and between option rows
    total_content_height = question_height + spacing + 2 * option_height + spacing

    # Starting Y position to center content
    start_y = (H - total_content_height) // 2

    # Position question
    question_clip = question_clip.with_position(('center', start_y))

    # Position options
    option_positions = [
        ('center', start_y + question_height + spacing),
        ('center', start_y + question_height + spacing + option_height + spacing)
    ]

    positioned_option_clips = []
    for i, clip in enumerate(option_clips):
        row = i // 2
        col = i % 2
        x_pos = W // 4 if col == 0 else 3 * W // 4
        y_pos = option_positions[row][1]
        positioned_option_clips.append(clip.with_position((x_pos - option_width // 2, y_pos)))

    # Create countdown clips
    countdown_clips = []
    countdown_start_time = full_q_audio.duration + 1   # Start countdown at 2 seconds
    for i in range(5, 0, -1):
        countdown_clip = TextClip(
            text=str(i),
            font=font_path,
            font_size=60,
            color='red',
            method='caption',
            size=(W - 2 * margin, None)
        ).with_duration(1).with_start(countdown_start_time + (5 - i)).with_position(('center', 150))
        countdown_clips.append(countdown_clip)

    # Compose the composite clip with countdown
    composite = CompositeVideoClip(
        [background, question_clip] + positioned_option_clips + countdown_clips
    ).with_duration(full_q_audio.duration+6).with_audio(mixed_audio)
    clips.append(composite)

    # --- Generate TTS for answer using safe_say ---
    a_wav = f"audio_a_{idx}.wav"
    if not os.path.exists(a_wav):
        answer_text = f"Correct option is {answer}."
        tts_a = safe_say_with_retries(answer_text, token)
        with open(a_wav, "wb") as f:
            f.write(tts_a.content)
    audio_a_clip = AudioFileClip(a_wav)

    # Create the answer text clips
    answer_label_clip = TextClip(
        text="Answer",
        font=font_path,
        font_size=80,
        color='white',
        method='caption',
        size=(W - 2 * margin, None)
    ).with_duration(audio_a_clip.duration+2)

    answer_text_clip = TextClip(
        text=item['answer'],
        font=font_path,
        font_size=60,
        color='yellow',
        method='caption',
        size=(W - 2 * margin, None)
    ).with_duration(audio_a_clip.duration+2)

    # Measure heights
    answer_label_height = answer_label_clip.get_frame(0).shape[0]
    answer_text_height = answer_text_clip.get_frame(0).shape[0]

    # Calculate total height and starting Y position for vertical centering
    spacing = 40  # spacing between label and answer
    total_answer_height = answer_label_height + spacing + answer_text_height
    start_y = (H - total_answer_height) // 2

    # Set positions
    answer_label_clip = answer_label_clip.with_position(('center', start_y))
    answer_text_clip = answer_text_clip.with_position(('center', start_y + answer_label_height + spacing))

    # Create background for the answer clip
    answer_background = ColorClip(size=(W, H), color=bg_color, duration=audio_a_clip.duration+1)

    # Compose the answer clip
    answer_composite = CompositeVideoClip(
        [answer_background, answer_label_clip, answer_text_clip]
    ).with_duration(audio_a_clip.duration+1).with_audio(audio_a_clip)

    # Append the answer clip to the list
    clips.append(answer_composite)

# Concatenate all question clips into one final video
final_video = concatenate_videoclips(clips, method="compose")
final_video.write_videofile("output/quiz_video2.mp4", fps=24)
