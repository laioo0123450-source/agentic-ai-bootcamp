import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=60.0,
    max_retries=0

)
MODEL = "poolside/laguna-s-2.1:free"

prompt = Path("prompt_template.md").read_text(encoding="utf-8")

print("Sending prompt to OpenRouter...")

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

answer = response.choices[0].message.content

output_dir = Path("outputs/laguna")
output_dir.mkdir(parents=True, exist_ok=True)

(output_dir / "response.md").write_text(
    answer or "",
    encoding="utf-8"
)

print("Requested model:", MODEL)
print("Response model:", response.model)
print("Saved to outputs/laguna/response.md")