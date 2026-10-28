
import json
import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

load_dotenv()

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    model="openrouter/free",
    temperature=0,
    timeout=180,
    max_retries=2,
)

PROMPT_TEMPLATE = Path("prompt_template.md").read_text(
    encoding="utf-8"
)

REQUIRED = ["main.py", "index.html", "test_api.py", "README.md"]
OUTPUT_DIR = Path("scaffold_out")


class State(TypedDict):
    spec: str
    plan: str
    files: dict
    errors: list
    attempts: int


def plan_node(state: State):
    print("\n[PLAN] Creating file plan...")

    response = llm.invoke(
        "You are a software planner. List the files and their "
        "purposes for this project. Required files: main.py, "
        "index.html, test_api.py, README.md.\n"
        f"SPEC:\n{state['spec']}"
    )

    return {"plan": str(response.content)}


def generate_node(state: State):
    attempt = state["attempts"] + 1
    print(f"\n[GENERATE] Attempt {attempt}...")

    response = llm.invoke(
        f"{PROMPT_TEMPLATE}\n\n"
        f"PROJECT SPEC:\n{state['spec']}\n\n"
        f"FILE PLAN:\n{state['plan']}\n\n"
        f"Known issues to fix: {state['errors']}\n\n"
        'Return ONLY valid JSON in this format:\n'
        '{"files": {"main.py": "code", '
        '"index.html": "html", '
        '"test_api.py": "tests", '
        '"README.md": "instructions"}}\n'
        "Do not wrap JSON in markdown."
    )

    content = response.content
    if not isinstance(content, str):
        content = str(content)

    content = content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content[:-3].strip()

    try:
        files = json.loads(content)["files"]

        if not isinstance(files, dict):
            raise ValueError("files must be a dictionary")

        for name, body in files.items():
            path = Path(name)
            if (
                not isinstance(body, str)
                or path.is_absolute()
                or ".." in path.parts
            ):
                raise ValueError(f"Invalid file entry: {name}")

        return {
            "files": files,
            "errors": [],
            "attempts": attempt,
        }

    except (ValueError, KeyError, TypeError) as error:
        return {
            "files": {},
            "errors": [f"Invalid generated JSON: {error}"],
            "attempts": attempt,
        }


def write_node(state: State):
    print("\n[WRITE] Writing generated files...")

    if state["errors"]:
        print("Skipping write because generation failed.")
        return {}

    for name, content in state["files"].items():
        destination = OUTPUT_DIR / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    return {}


def verify_node(state: State):
    print("\n[VERIFY] Checking required files...")

    if state["errors"]:
        return {}

    missing = [
        name
        for name in REQUIRED
        if (
            name not in state["files"]
            or not str(state["files"][name]).strip()
            or not (OUTPUT_DIR / name).is_file()
        )
    ]

    errors = [f"Missing or empty file: {name}" for name in missing]

    if errors:
        print("Verification failed:", errors)
    else:
        print("All required files found!")

    return {"errors": errors}


def route(state: State):
    if not state["errors"]:
        print("\n[DONE] Scaffold generated successfully.")
        return "done"

    if state["attempts"] >= 3:
        print("\n[STOP] Maximum attempts reached.")
        return "done"

    print("\n[RETRY] Sending errors back to generator...")
    return "retry"


graph = StateGraph(State)

graph.add_node("plan", plan_node)
graph.add_node("generate", generate_node)
graph.add_node("write", write_node)
graph.add_node("verify", verify_node)

graph.add_edge(START, "plan")
graph.add_edge("plan", "generate")
graph.add_edge("generate", "write")
graph.add_edge("write", "verify")

graph.add_conditional_edges(
    "verify",
    route,
    {"retry": "generate", "done": END},
)

app = graph.compile()


if __name__ == "__main__":
    final = app.invoke({
        "spec": (
            "Asset maintenance mini-app: FastAPI CRUD backend "
            "over maintenance_assets.csv, plus a simple "
            "index.html that lists flagged assets."
        ),
        "plan": "",
        "files": {},
        "errors": [],
        "attempts": 0,
    })

    print("\nAttempts:", final["attempts"])
    print("Errors:", final["errors"])
    print("Generated files:", list(final["files"]))
