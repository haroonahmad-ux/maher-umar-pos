"""Maher Umar POS Android entry point with startup crash logging.

Place this file in the repository root as main.py.
It dynamically loads Maher_Umar_POS_UI_Fixed_v2-1.py and records startup
exceptions to the app's writable private directory as crash_log.txt.
"""
import importlib.util
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

APP_FILENAME = "Maher_Umar_POS_UI_Fixed_v2-1.py"


def write_crash_log(message: str, app=None) -> str:
    """Write diagnostics to a writable Android app directory when possible."""
    candidates = []

    if app is not None:
        try:
            if app.user_data_dir:
                candidates.append(Path(app.user_data_dir))
        except Exception:
            pass

    # Kivy/Android may set this to the app's private writable directory.
    for env_name in ("ANDROID_PRIVATE", "ANDROID_APP_PATH"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(Path(value))

    # Last resort for desktop/testing; the APK's source directory may be read-only.
    candidates.append(Path.home() / ".maher_umar_pos")

    last_error = None
    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            log_path = directory / "crash_log.txt"
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(f"\n\n===== {datetime.now().isoformat(timespec='seconds')} =====\n")
                stream.write(message.rstrip() + "\n")
            return str(log_path)
        except Exception as exc:
            last_error = exc

    print(f"Could not write crash log: {last_error}", file=sys.stderr)
    return ""


def main():
    app = None
    phase = "starting main.py"
    try:
        app_path = Path(__file__).resolve().parent / APP_FILENAME
        phase = f"checking app file: {app_path}"
        if not app_path.is_file():
            raise FileNotFoundError(
                f"Required app file is missing: {app_path}. "
                f"Ensure {APP_FILENAME} is in the repository root and included in the APK."
            )

        phase = "loading Kivy application module"
        spec = importlib.util.spec_from_file_location("maher_umar_pos_main", app_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create a module loader for: {app_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        phase = "checking MaherUmarPOSApp class"
        app_class = getattr(module, "MaherUmarPOSApp", None)
        if app_class is None:
            raise AttributeError(
                f"{APP_FILENAME} does not define MaherUmarPOSApp"
            )

        phase = "creating Kivy application"
        app = app_class()

        phase = "running Kivy application (build/KV/database startup)"
        app.run()

    except Exception:
        details = (
            f"STARTUP PHASE: {phase}\n"
            f"APP FILE: {APP_FILENAME}\n\n"
            f"{traceback.format_exc()}"
        )
        log_path = write_crash_log(details, app=app)
        print(details, file=sys.stderr)
        if log_path:
            print(f"Crash details saved to: {log_path}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
