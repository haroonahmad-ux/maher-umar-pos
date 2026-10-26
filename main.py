
import importlib.util
from pathlib import Path

APP_FILE = Path(__file__).resolve().with_name(
    "Maher_Umar_POS_UI_Fixed_v2-1.py"
)

spec = importlib.util.spec_from_file_location(
    "maher_umar_pos_main", APP_FILE
)

if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load app module: {APP_FILE}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

MaherUmarPOSApp = module.MaherUmarPOSApp

if __name__ == "__main__":
    MaherUmarPOSApp().run()
