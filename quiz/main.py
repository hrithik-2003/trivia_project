import argparse
import random

from builder import build_quiz_video

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a trivia quiz video with customizable options."
    )
    parser.add_argument(
        "-n", "--num_questions",
        type=int,
        default=3,
        help="Number of trivia questions to include in the video"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="quiz_video.mp4",
        help="Output video filename (will be saved under output/)",
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible question/background selection",
    )
    return parser.parse_args()

def main():
    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    build_quiz_video(
        num_questions=args.num_questions,
        output_filename=args.output,
    )

if __name__ == "__main__":
    main()