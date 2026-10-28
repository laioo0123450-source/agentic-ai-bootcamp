import csv
import json
from pathlib import Path
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("maintenance")

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "maintenance_assets.csv"
MEMORY_FILE = BASE_DIR / "agent_memory.json"

with CSV_FILE.open(newline="", encoding="utf-8-sig") as f:
    ASSETS = list(csv.DictReader(f))


def _load_mem():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    return {}


@mcp.tool()
def search_assets(
    status: str = "",
    criticality: str = "",
    asset_type: str = "",
    location: str = ""
) -> list[dict]:
    """Search the plant asset maintenance records."""
    rows = ASSETS

    for key, value in [
        ("status", status),
        ("criticality", criticality),
        ("asset_type", asset_type),
        ("location", location)
    ]:
        if value:
            rows = [
                row for row in rows
                if value.lower() in row[key].lower()
            ]

    return rows[:20]


@mcp.tool()
def remember(key: str, note: str) -> str:
    """Store a note in persistent memory."""
    memory = _load_mem()
    memory[key] = note
    MEMORY_FILE.write_text(
        json.dumps(memory, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return f"stored under '{key}'"


@mcp.tool()
def recall(key: str = "") -> dict:
    """Recall a note or all stored notes."""
    memory = _load_mem()
    return memory if not key else {
        key: memory.get(key, "nothing stored")
    }


@mcp.resource("assets://flagged")
def flagged_assets() -> str:
    """Return assets flagged for inspection."""
    return json.dumps(
        [
            row for row in ASSETS
            if row["status"] == "Flagged for Inspection"
        ],
        indent=2
    )


@mcp.prompt()
def maintenance_briefing(unit: str) -> str:
    """Create a maintenance briefing prompt."""
    return (
        f"Summarize the maintenance posture of {unit}: "
        "flagged items, high-criticality equipment, "
        "overdue inspections. Cite asset_ids."
    )


if __name__ == "__main__":
    mcp.run()
