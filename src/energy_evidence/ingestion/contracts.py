import json
from pathlib import Path

def load_event_contract(event_path: Path) -> dict: 
    path = Path(event_path)
    return json.loads(path.read_text())