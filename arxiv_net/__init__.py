import os
from pathlib import Path

HOME_DIR = Path.home()
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = ROOT_DIR.parent / "data"
