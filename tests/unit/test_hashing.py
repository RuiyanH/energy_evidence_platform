import unittest
from energy_evidence.ingestion.hashing import sha256_bytes

class HashingTestss(unittest.TestCase):
    def test_same_byes_have_same_hash(self):
        content = b"test content"
        hash1 = sha256_bytes(content)
        hash2 = sha256_bytes(content)
        self.assertEqual(hash1, hash2)

    def test_different_bytes_have_different_hashes(self):
        content1 = b"test content 1"
        content2 = b"test content 2"
        hash1 = sha256_bytes(content1)
        hash2 = sha256_bytes(content2)
        self.assertNotEqual(hash1, hash2)

if __name__ == "__main__":
    unittest.main()

