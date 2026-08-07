import argparse
import json
from pathlib import Path

def main(): 
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest = "command", required = True)

    read_contract = subparsers.add_parser("read-contract")
    read_contract.add_argument("--event", required = True)

    args = parser.parse_args()

    if args.command == "read-contract":
        event_path = Path(args.event)
        event = json.loads(event_path.read_text())

        print(f"Event: {event['event_key']}")
        print(f"Description: {event['description']}")

        for artifact in event["artifacts"]:
            print("")
            print(f"Title: {artifact['title']}")
            print(f"System: {artifact['source_system']}")
            print(f"URL: {artifact['source_url']}")

if __name__ == "__main__":
    main()
    