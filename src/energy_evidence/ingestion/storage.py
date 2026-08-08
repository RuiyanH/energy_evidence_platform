from pathlib import Path 

def save_raw_bytes(data_root: str, content_hash: str, content: bytes, file_extension: str) -> Path: 
    raw_dir = Path(data_root) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_path = raw_dir / f"{content_hash}{file_extension}"

    if not output_path.exists():
        output_path.write_bytes(content)

    return output_path