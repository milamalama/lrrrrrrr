
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

filename = f"backup_{datetime.now():%Y%m%d_%H%M%S}.json"
backup_path = BACKUP_DIR / filename

with backup_path.open("w", encoding="utf-8") as file:
    subprocess.run(
        [
            sys.executable,
            "manage.py",
            "dumpdata",
            "--natural-foreign",
            "--natural-primary",
            "--indent",
            "2",
        ],
        cwd=BASE_DIR,
        stdout=file,
        check=True,
    )

print(f"Резервная копия создана: {backup_path}")
