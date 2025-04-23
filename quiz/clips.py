import random
import numpy as np
from pathlib import Path
from moviepy import TextClip, ImageClip, VideoFileClip, AudioClip, CompositeVideoClip, vfx
from moviepy.video.fx import Loop

from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS, MARGIN,
    COUNTDOWN_RADIUS, COUNTDOWN_DURATION, COUNTDOWN_START,
    BACKGROUND_VIDEOS, SILENCE_DURATION, FONTS_DIR,
)

# === Text clip factory ===
def make_text_clip(
    text: str,
    duration: float,
    font_path: Path,
    font_size: int,
    color: str = 'white',
    stroke_color: str = 'black',
    stroke_width: int = 4,
    size: tuple[int, int] | tuple[int, None] = (VIDEO_WIDTH - 2 * MARGIN, None),
) -> TextClip:
    """
    Create a styled TextClip with a caption method.
    """
    clip = TextClip(
        text=text,
        font=str(font_path),
        font_size=font_size,
        color=color,
        method='caption',
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        size=size,
        margin=(0, 8),
        
    )
    return clip.with_position('center').with_duration(duration)

# === Silence padding ===
def make_silence(duration: float = SILENCE_DURATION, fps: int = 44100) -> AudioClip:
    """
    Generate a silent stereo AudioClip of given duration.
    """
    return AudioClip(lambda t: np.zeros((np.atleast_1d(t).shape[0], 2)), duration=duration, fps=fps)

# === Countdown overlay clips ===
def make_countdown_clips(start_time: float, center: tuple[int, int]) -> list:
    """
    Generate countdown circle + number clips from COUNTDOWN_START to 1.
    Returns a list of ImageClip/TextClip with start times.
    """
    clips = []
    radius = COUNTDOWN_RADIUS
    diameter = 2 * radius
    # white circle color
    circle_color = (255, 255, 255)

    for idx, number in enumerate(range(COUNTDOWN_START, 0, -1)):
        t0 = start_time + idx * COUNTDOWN_DURATION

        # Circle background
        img = np.zeros((diameter, diameter, 4), dtype=np.uint8)
        yy, xx = np.ogrid[:diameter, :diameter]
        mask = (xx - radius)**2 + (yy - radius)**2 <= radius**2
        img[mask] = (*circle_color, 255)
        circle = (
            ImageClip(img)
            .with_start(t0)
            .with_duration(COUNTDOWN_DURATION)
            .with_position(center)
        )
        clips.append(circle)

        # Number overlay
        number_clip = (
            TextClip(
                text=str(number),
                font=str(FONTS_DIR / "WinkyRough-VariableFont_wght.ttf"),
                font_size=60,
                color='red',
                method='caption',
                size=(diameter, diameter),
            )
            .with_start(t0)
            .with_duration(COUNTDOWN_DURATION)
            .with_position(center)
        )
        clips.append(number_clip)

    return clips

def make_background(duration: float) -> VideoFileClip:
    """
    Load a random background video, loop or trim to `duration`, resize to project resolution.
    """
    bg_path = random.choice(BACKGROUND_VIDEOS)
    clip = VideoFileClip(str(bg_path))
    # if clip.duration < duration:
    #     clip = loop(clip, duration=duration)
    # else:
    clip = clip.subclipped(0, duration)

    return clip.resized((VIDEO_WIDTH, VIDEO_HEIGHT)).with_fps(FPS)

# === Option clip with shake effect ===
def make_option_clip(
    text: str,
    duration: float,
    font_path: Path,
    font_size: int = 50,
) -> TextClip:
    """
    Create an option TextClip with slide-in + subtle shake.
    """
    base = make_text_clip(
        text=text,
        duration=duration,
        font_path=font_path,
        font_size=font_size,
        color='yellow',
        stroke_color='black',
        stroke_width=4,
        size=((VIDEO_WIDTH - 3 * MARGIN) // 2, None),
    )
    # slide in
    slid = CompositeVideoClip([base.with_effects([vfx.SlideIn( 0.1, 'bottom')])])

    # shake parameters
    freq = random.uniform(2, 4)
    amp = random.uniform(2, 5)
    phase = random.uniform(0, 2 * np.pi)
    def shake(t): return amp * np.sin(2 * np.pi * freq * t + phase)

    return slid.rotated(angle=shake, unit='deg')

