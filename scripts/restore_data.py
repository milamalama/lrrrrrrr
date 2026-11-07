
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"

if len(sys.argv) != 2:
    print("Использование: python scripts/restore_data.py backups/backup.json")
    sys.exit(1)

backup_path = Path(sys.argv[1]).resolve()

if not backup_path.is_file():
    print("Файл резервной копии не найден.")
    sys.exit(1)

if BACKUP_DIR.resolve() not in backup_path.parents:
    print("Восстановление разрешено только из папки backups.")
    sys.exit(1)

print("ВНИМАНИЕ: восстановление предназначено для учебной базы данных.")
answer = input("Введите RESTORE для подтверждения: ")

if answer != "RESTORE":
    print("Операция отменена.")
    sys.exit(0)

subprocess.run(
    [sys.executable, "manage.py", "loaddata", str(backup_path)],
    cwd=BASE_DIR,
    check=True,
)

print("Данные загружены.")
