from pathlib import Path

import pandas as pd


def load_ad_file(path: str | Path) -> pd.DataFrame:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(file_path)

    if suffix in {".xlsx", ".xls"}:
        sheets = pd.read_excel(file_path, sheet_name=None)
        frames = []
        for sheet_name, frame in sheets.items():
            if frame.empty:
                continue
            copied = frame.copy()
            copied["source_sheet"] = sheet_name
            frames.append(copied)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")

