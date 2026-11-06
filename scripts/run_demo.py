import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a synthetic CausaTrace incident.")
    parser.add_argument(
        "incident_id",
        nargs="?",
        choices=("demo-001", "demo-002"),
        default="demo-001",
        help="Incident to inspect (default: demo-001)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    fixture_path = project_root / "data" / "demo" / f"{args.incident_id}.json"
    incident = json.loads(fixture_path.read_text(encoding="utf-8"))

    print(f"Incident: {incident['incident_id']} (synthetic)")
    for observation in incident["observations"]:
        print(
            f"{observation['id']} | {observation['timestamp']} | "
            f"{observation['service']} | "
            f"{observation['signal']} = {observation['value']}"
        )


if __name__ == "__main__":
    main()
