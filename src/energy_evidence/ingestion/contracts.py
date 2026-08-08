"""
Reads and validates event contracts from JSON files.
"""


import json
from pathlib import Path

REQUIRED_EVENT_KEYS = ["event_key", "description", "artifacts"]

REQUIRED_ARTIFACT_KEYS = [
    "source_system",
    "source_dataset",
    "artifact_type",
    "canonical_source_key",
    "title",
    "source_url",
]

def load_event_contract(event_path: str) -> dict: 
    path = Path(event_path)
    event = json.loads(path.read_text())
    validate_event_contract(event)
    return event

def validate_event_contract(event: dict) -> None:
    for key in REQUIRED_EVENT_KEYS:
        if key not in event:
            raise ValueError(f"Missing required event key: {key}")

    if not isinstance(event["artifacts"], list): 
        raise ValueError("Event 'artifacts' must be a list")

    for artifact in event["artifacts"]:
        for artifact_key in REQUIRED_ARTIFACT_KEYS:
            if artifact_key not in artifact:
                raise ValueError(f"Missing required artifact key: {artifact_key}")
