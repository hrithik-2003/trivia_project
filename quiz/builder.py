import random
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from moviepy import (CompositeVideoClip, CompositeAudioClip, VideoFileClip,
    AudioFileClip, TextClip, ImageClip, vfx, afx, AudioClip, concatenate_audioclips)

from config import (
    OUTPUT_DIR, AUDIO_DIR, VIDEO_DIR,
    FONTS_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    MARGIN, SILENCE_DURATION,
    BACKGROUND_VIDEOS, TICK_SOUND, CORRECT_SOUND,
    INTRO_TEMPLATES, SHOUTOUT_TEMPLATES, ANSWER_TEMPLATES,
    COUNTDOWN_START, COUNTDOWN_RADIUS, CIRCLE_COLOR
)
from tts import say
from quiz_data import get_random_questions
from clips import (
    make_background,
    make_text_clip,
    make_silence,
    make_countdown_clips,
    make_option_clip,
)


@dataclass
class Timeline:
    video_clips: list = field(default_factory=list)
    audio_clips: list = field(default_factory=list)
    current_t: float = 0.0

    def add_video(self, clip, start=None):
        clip = clip.with_start(self.current_t if start is None else start)
        self.video_clips.append(clip)
        return clip

    def add_audio(self, clip, start=None):
        clip = clip.with_start(self.current_t if start is None else start)
        self.audio_clips.append(clip)
        return clip

    def advance(self, seconds):
        self.current_t += seconds


def make_silence(duration=SILENCE_DURATION):
    print('abc')
    return AudioClip(lambda t: np.zeros((len(np.atleast_1d(t)),2)), duration=duration, fps=44100)



def build_quiz_video(num_questions=5, output_filename="quiz_video.mp4"):
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / output_filename
    print('def')

    questions = get_random_questions(num_questions)
    tl = Timeline()

    # Background placeholder
    bg_clip = VideoFileClip(str(random.choice(BACKGROUND_VIDEOS)))
    tl.add_video(bg_clip.resized((VIDEO_WIDTH, VIDEO_HEIGHT)).with_fps(FPS), start=0)

    # Intro segment (generic)
    intro_text = random.choice(INTRO_TEMPLATES)
    intro_audio = say(intro_text)
    tl.add_audio(intro_audio)
    intro_clip = TextClip(
        text=intro_text,
        font=str(FONTS_DIR/"LuckiestGuy-Regular.ttf"),
        font_size=70,
        color='white',
        method='caption',
        stroke_color='black', stroke_width=8,
        size=(VIDEO_WIDTH-2*MARGIN, None), margin=(0,8)
    ).with_duration(intro_audio.duration + 0.5)
    h = intro_clip.get_frame(0).shape[0]
    intro_clip = intro_clip.with_position(('center', (VIDEO_HEIGHT - h) // 2))
    tl.add_video(intro_clip)
    tl.advance(intro_audio.duration + 0.5)

    print('def2')

    # Per-question loop
    for idx, item in enumerate(questions):
        question = item['question']
        options = item['options']
        answer = item['answer']

        # QUESTION AUDIO + CLIP
        q_audio = say("Question: " + question)
        # Create audio including silence before options
        option_sil = make_silence()
        print('lol')
        # option_audios = [q_audio] + sum([[option_sil, say(opt)] for opt in options], [])
        option_audios = [q_audio]
        for opt in options:
            option_audios += [option_sil, say(opt)]
        full_q_audio = concatenate_audioclips(option_audios)
        tl.add_audio(full_q_audio)
        countdown_start_time = tl.current_t + full_q_audio.duration + 1
        
        q_clip = TextClip(
            text=question,
            font=str(FONTS_DIR/"LuckiestGuy-Regular.ttf"), font_size=70,
            color='white', method='caption', stroke_color='black', stroke_width=8,
            size=(VIDEO_WIDTH-2*MARGIN, None), margin=(0,8), vertical_align='top'
        ).with_duration(full_q_audio.duration)
        q_clip = CompositeVideoClip([q_clip.with_effects([vfx.SlideIn(0.1, 'bottom')])])

        o_clips = []
        option_fontsize = 40
        option_width = (VIDEO_HEIGHT - 3 * MARGIN) // 2
        for i, opt in enumerate(options):
            clip = TextClip(
                text=opt,
                font=str(FONTS_DIR/"LuckiestGuy-Regular.ttf"),
                font_size=option_fontsize,
                color='yellow',
                method='caption',
                stroke_color='black',
                stroke_width=4,
                size=(option_width, None),
                margin=(0, 8), 
            ).with_duration(full_q_audio.duration)

            freq = random.uniform(2, 4)
            amp = random.uniform(2, 5)
            phase = random.uniform(0, 2 * np.pi)
            def make_shake(freq, amp, phase):
                return lambda t: amp * np.sin(2 * np.pi * freq * t + phase)
            shake = make_shake(freq, amp, phase)
            clip = CompositeVideoClip([clip.with_effects([vfx.SlideIn( 0.1, 'bottom')])])
            clip = clip.rotated(angle=shake, unit='deg')
            o_clips.append(clip)


        question_height = q_clip.get_frame(0).shape[0]
        option_height = o_clips[0].get_frame(0).shape[0]
    
    
        spacing = 40
        total_content_height = question_height + spacing + 2 * option_height + spacing
        start_y = (VIDEO_HEIGHT - total_content_height) // 2

        tl.add_video(q_clip.with_position(('center', start_y)))

        for i, clip in enumerate(o_clips):
            row = i // 2
            col = i % 2
            x_pos = VIDEO_WIDTH // 4 if col == 0 else 3 * VIDEO_WIDTH // 4
            y_pos = start_y + question_height + spacing + row * (option_height + spacing)
            tl.add_video(clip.with_position((x_pos - option_width // 2, y_pos)))

        

        print('def3')

        # SHOUT-OUT AFTER FIRST QUESTION
        if idx == 0:
            shout = random.choice(SHOUTOUT_TEMPLATES)
            shout_audio = say(shout)
            shout_audio = tl.add_audio(shout_audio, tl.current_t + full_q_audio.duration + 3)
            mixed_aud = CompositeAudioClip([full_q_audio, shout_audio])
        else:
            mixed_aud = full_q_audio
        
        tl.advance(full_q_audio.duration + 6)

        print('def4')

        # tick sounds
        tl.add_audio(AudioFileClip(str(TICK_SOUND)), start=countdown_start_time)
        # visuals
        for j in range(COUNTDOWN_START, 0, -1):
            start_time = countdown_start_time + (5 - j)
            circle_img = np.zeros((COUNTDOWN_RADIUS*2, COUNTDOWN_RADIUS*2, 4), dtype=np.uint8)
            yy, xx = np.ogrid[:COUNTDOWN_RADIUS*2, :COUNTDOWN_RADIUS*2]
            mask = (xx - COUNTDOWN_RADIUS)**2 + (yy - COUNTDOWN_RADIUS)**2 <= COUNTDOWN_RADIUS**2
            circle_img[mask] = (*CIRCLE_COLOR, 255)  # Set circle color (white)
            circle_clip = (
                ImageClip(circle_img)
                .with_duration(1)
                .with_position(('center', 130))   
             )
            tl.add_video(circle_clip,start_time)

            cnt = (
            TextClip(
                text=str(j),
            font=str(FONTS_DIR/"WinkyRough-VariableFont_wght.ttf"),
                font_size=60,
                color='red',
                method='caption',
                size=(COUNTDOWN_RADIUS*2, COUNTDOWN_RADIUS*2),  # Use the circle's diameter for size
        
                )
            .with_duration(1)
            .with_position(('center', 130))
            )  
            tl.add_video(cnt,start_time)

        # ANSWER SEGMENT
        # correct sound + TTS answer
        ans_audio = say(f"Correct option is {answer}.")
        tl.add_audio(AudioFileClip(str(CORRECT_SOUND)))
        tl.add_audio(ans_audio)
        ans_clip = TextClip(
            text=f"Answer: {answer}",
            font=str(FONTS_DIR/"LuckiestGuy-Regular.ttf"), font_size=60,
            color='green', method='caption', stroke_color='black', stroke_width=8,
            size=(VIDEO_WIDTH-2*MARGIN, None), margin=(0,8)
        ).with_duration(ans_audio.duration + 1)
        h_ans = ans_clip.get_frame(0).shape[0]
        ans_clip = ans_clip.with_position(('center', (VIDEO_HEIGHT - h_ans) // 2))
        tl.add_video(ans_clip)
        tl.advance(ans_audio.duration + 1)

        print('def5')

    # Trim background and add music
    total_dur = tl.current_t
    bg_final = tl.video_clips[0].subclipped(0, total_dur)
    tl.video_clips[0] = bg_final
    music = AudioFileClip(str(AUDIO_DIR/"Wii Music - Gaming Background Music (HD).mp3")).subclipped(0, total_dur)
    music = music.with_effects([afx.MultiplyVolume(0.2)])
    tl.audio_clips.insert(0, music)

    # Compose and write file
    final = CompositeVideoClip(tl.video_clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    final = final.with_audio(CompositeAudioClip(tl.audio_clips)).with_duration(total_dur)
    final.write_videofile(str(out_path), fps=FPS)


def main():
    build_quiz_video()

if __name__ == "__main__":
    main()
