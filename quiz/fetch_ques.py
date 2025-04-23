import os
import re
import json
import argparse
from dotenv import load_dotenv
from together import Together

def fetch_quiz_questions(count: int) -> list[dict]:
    """
    Use the Together API to generate `count` geography trivia questions.
    Returns a list of dicts: [{"question": ..., "options": [...], "answer": ...}, ...]
    """
    prompt = (
        f"Generate {count} easy to medium level biology trivia multiple choice questions "
        "with 4 options each, and provide the correct answer. "
        "Format the output as a JSON array like: "
        "[{\"question\": \"...\", \"options\": [...], \"answer\": \"...\"}]"
    )

    token = os.getenv("TOGETHER_API_KEY")
    if not token:
        raise RuntimeError("TOGETHER_API_KEY not found in environment.")
    client = Together(api_key=token)

    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        top_p=0.9,
        max_tokens=512,
    )
    raw = response.choices[0].message.content

     # Extract JSON between ``` ``` or fallback to brackets
    m = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', raw, re.DOTALL)
    if m:
        json_str = m.group(1)
    else:
        start = raw.find('[')
        end = raw.rfind(']')
        json_str = raw[start:end+1]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON from model response:", e)
        print(raw)
        raise

    return data

def main():
    parser = argparse.ArgumentParser(description="Fetch trivia questions via Together and save to JSON.")
    parser.add_argument(
        "-n", "--num_questions",
        type=int,
        default=5,
        help="Number of trivia questions to generate"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="quiz_data.json",
        help="Output JSON filename"
    )
    args = parser.parse_args()

    # Load environment
    load_dotenv()

    questions = fetch_quiz_questions(args.num_questions)

    # Save to file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=4)

    print(f"Successfully wrote {len(questions)} questions to '{args.output}'")


if __name__ == "__main__":
    main()