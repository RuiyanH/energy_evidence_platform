"""
Command line interface for the ingestion module.
"""
import argparse
from energy_evidence.ingestion.contracts import load_event_contract
from energy_evidence.ingestion.download import download_url

def main(): 
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest = "command", required = True)

    read_contract = subparsers.add_parser("read-contract")
    read_contract.add_argument("--event", required = True)

    download = subparsers.add_parser("download")
    download.add_argument("--url", required = True)

    args = parser.parse_args()

    if args.command == "read-contract":
        event = load_event_contract(args.event)

        print(f"Event: {event['event_key']}")
        print(f"Description: {event['description']}")

        for artifact in event["artifacts"]:
            print("")
            print(f"Title: {artifact['title']}")
            print(f"System: {artifact['source_system']}")
            print(f"URL: {artifact['source_url']}")

    if args.command == "download":
        body = download_url(args.url)
        print(f"Downloaded {len(body)} bytes")

if __name__ == "__main__":
    main()
