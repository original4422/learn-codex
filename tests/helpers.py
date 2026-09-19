"""Keep all test writes under the project, including temporary artifacts."""

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples/taskboard"))
CACHE = ROOT / ".cache/tmp"
CACHE.mkdir(parents=True, exist_ok=True)


def temporary_directory():
    return tempfile.TemporaryDirectory(prefix="test-", dir=CACHE)
