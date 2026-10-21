"""Stage saved NLS extracts and cache the official BLS CPI series from FRED."""
from pathlib import Path
import argparse
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--children", type=Path, help="Child income CSV or original NLS ZIP")
    parser.add_argument("--mothers", type=Path, help="NLSY79 main CSV or original NLS ZIP")
    parser.add_argument("--dates", type=Path, help="Child interview-year CSV or NLS ZIP")
    parser.add_argument("--refresh-cpi", action="store_true")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    for source, stem in [(args.children,"children"),(args.mothers,"mothers"),(args.dates,"child_dates")]:
        if source is None:
            if not (RAW/f"{stem}.csv").exists():
                parser.error(f"Missing {stem}.csv: provide the corresponding input option.")
            continue
        if source.suffix.lower()==".zip":
            with zipfile.ZipFile(source) as z:
                for extension,target in [(".csv",f"{stem}.csv"),(".cdb",f"{stem}_codebook.txt")]:
                    name=next(n for n in z.namelist() if n.endswith(extension))
                    (RAW/target).write_bytes(z.read(name))
        else:
            shutil.copy2(source,RAW/f"{stem}.csv")
            codebook=source.with_suffix(".cdb")
            if codebook.exists():shutil.copy2(codebook,RAW/f"{stem}_codebook.txt")
    target = ROOT / "data" / "cpi_monthly.csv"
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS&cosd=1978-01-01&coed=2020-12-31"
    if args.refresh_cpi or not target.exists():
        with urllib.request.urlopen(url, timeout=60) as response:
            target.write_bytes(response.read())
    print("Saved NLS extracts and CPI cache.")


if __name__ == "__main__":
    main()
