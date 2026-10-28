import csv
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

MODEL = "openrouter/free"

with open("maintenance_assets.csv", newline="", encoding="utf-8-sig") as f:
    ASSETS = list(csv.DictReader(f))


def search_assets(status=None, criticality=None, asset_type=None, location=None):
    rows = ASSETS

    for key, val in [
        ("status", status),
        ("criticality", criticality),
        ("asset_type", asset_type),
        ("location", location)
    ]:
        if val:
            rows = [r for r in rows if val.lower() in r[key].lower()]

    return rows[:20]


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_assets",
            "description": "Search the plant asset maintenance records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "criticality": {"type": "string"},
                    "asset_type": {"type": "string"},
                    "location": {"type": "string"}
                }
            }
        }
    }
]


SYSTEM = (
    "You are a plant maintenance assistant agent. "
    "Use the search_assets tool to answer questions about equipment. "
    "Cite asset_ids. "
    "If the records cannot answer, say so."
)


def run_agent(question):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question}
    ]

    for _ in range(5):
        r = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS
        )

        msg = r.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")

            print("TOOL CALLED:", call.function.name)
            print("ARGUMENTS:", args)

            result = search_assets(**args)

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result)
            })

    return "Step limit reached."


if __name__ == "__main__":
    while True:
        q = input("\nAsk about plant assets (or exit): ")

        if q.strip().lower() == "exit":
            break

        print(run_agent(q))