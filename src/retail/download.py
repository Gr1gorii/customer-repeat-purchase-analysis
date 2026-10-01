"""Download only from the original UCI dataset host."""

import hashlib
import json
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

URL = "https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip"
ROOT = Path(__file__).resolve().parents[2]


def download():
    folder = ROOT / "data/raw"
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / "online-retail.zip"
    if not archive.exists():
        urlretrieve(URL, archive)
    # Read this exact member rather than trusting arbitrary ZIP paths.
    with ZipFile(archive) as package:
        workbook = package.read("Online Retail.xlsx")
    (folder / "Online Retail.xlsx").write_bytes(workbook)
    manifest = {
        "source": URL,
        "citation": "Chen, D. (2015). Online Retail. UCI. DOI: 10.24432/C5BW33",
        "license": "CC BY 4.0",
        "zip_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "xlsx_sha256": hashlib.sha256(workbook).hexdigest(),
        "xlsx_bytes": len(workbook),
    }
    (ROOT / "docs/source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return folder / "Online Retail.xlsx"


if __name__ == "__main__":
    print(download())
