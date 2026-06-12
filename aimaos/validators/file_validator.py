from pathlib import Path


SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


def validate_input_file(path: str | Path) -> Path:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {file_path}")
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"지원하지 않는 파일 형식입니다: {file_path.suffix}. 허용: {allowed}")
    return file_path


def ensure_output_dir(path: str | Path) -> Path:
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

