import tempfile 
import unittest
from pathlib import Path

from energy_evidence.ingestion.contracts import load_event_contract

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

if __name__ == "__main__":
    unittest.main()