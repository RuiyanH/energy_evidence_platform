import tempfile 
import unittest
from pathlib import Path

from energy_evidence.ingestion.contracts import load_event_contract, validate_event_contract

class ContractTests(unittest.TestCase): 
    def test_load_event_contract_reads_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir: 
            contract_path = Path(tmpdir) / "event.json"
            contract_path.write_text(
                """
                {
                    "event_key": "test_event",
                    "description": "A test event,",
                    "artifacts": []
                }
                """
            )

            event = load_event_contract(str(contract_path))

            self.assertEqual(event["event_key"], "test_event") 
            self.assertEqual(event["artifacts"], [])

    def test_validate_event_contract_rejects_missing_event_key(self):
        event = {
            "description": "A test event",
            "artifacts": []
        }

        with self.assertRaises(ValueError):
            validate_event_contract(event)

    def test_validate_event_contract_rejects_missing_artifact_url(self):
        event = {
            "event_key": "test_event",
            "description": "A test event.",
            "artifacts": [
                {
                    "source_system": "ercot",
                    "source_dataset": "event_documents",
                    "artifact_type": "regulatory_order_pdf",
                    "canonical_source_key": "test_doc",
                    "title": "Test document"
                }
            ]
        }

        with self.assertRaises(ValueError):
            validate_event_contract(event)

if __name__ == "__main__":
    unittest.main()