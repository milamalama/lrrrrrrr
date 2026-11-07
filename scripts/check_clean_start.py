import os
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def run(*args, env):
    print("Выполняется:", " ".join(args))
    subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=BASE_DIR,
        env=env,
        check=True,
    )


with tempfile.TemporaryDirectory() as directory:
    env = os.environ.copy()

    env["DATABASE_URL"] = f"sqlite:///{Path(directory, 'test.sqlite3').as_posix()}"
    env["DJANGO_SECRET_KEY"] = "temporary-check-only-secret-key"
    env["DJANGO_DEBUG"] = "False"
    env["DJANGO_ALLOWED_HOSTS"] = "localhost,127.0.0.1"

    run("check", env=env)
    run("migrate", "--noinput", env=env)
    run("test", env=env)

print("Проверка чистого запуска завершена успешно.")
