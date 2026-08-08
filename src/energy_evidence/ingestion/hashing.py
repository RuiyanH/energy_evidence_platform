"""
Hashing utilities for computing SHA256 hashes.
"""

import hashlib

def sha256_bytes(content: bytes) -> str:
    """
    Computes the SHA256 hash of the given bytes and returns it as a hexadecimal string.
    """
    return hashlib.sha256(content).hexdigest()