"""Find CSV rows with 'Pending' in date-like columns."""
import csv
from pathlib import Path

csv_path = Path(__file__).parent.parent.parent / "Data" / "Store" / "schedules.csv"
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    print(f"Headers: {headers}")
    print()
    count = 0
    for row in reader:
        for col in ["date", "match_date", "match_time"]:
            val = row.get(col, "")
            if val and "Pending" in str(val):
                print(f"  fixture_id={row.get('fixture_id','?')} | {col}={val}")
                count += 1
                break
    print(f"\nTotal rows with 'Pending': {count}")
