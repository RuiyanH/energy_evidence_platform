import unittest
from pathlib import Path
import tempfile 

from energy_evidence.ingestion.storage import save_raw_bytes

class StorageTests(unittest.TestCase):
    def test_save_raw_bytes_writes_file_named_by_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir: 
            output_path = save_raw_bytes(
                data_root=tmpdir,
                content_hash="abc123",
                content=b"test content",
                file_extension=".txt"
            )

    def test_save_raw_bytes_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir: 
            output_path = save_raw_bytes(
                data_root=tmpdir,
                content_hash="abc123",
                content=b"test content",
                file_extension=".txt"
            )

            # Call save_raw_bytes again with the same hash
            output_path2 = save_raw_bytes(
                data_root=tmpdir,
                content_hash="abc123",
                content=b"new content",
                file_extension=".txt"
            )

            # Ensure the file was not overwritten
            self.assertEqual(output_path, output_path2)
            self.assertEqual(output_path.read_bytes(), b"test content")

if __name__ == "__main__":
    unittest.main()