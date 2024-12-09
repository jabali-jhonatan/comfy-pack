import sys
import pathlib


SRC_DIR = pathlib.Path(__file__).parent.parent / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
