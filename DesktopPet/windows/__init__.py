"""DesktopPet Windows Module (All UI windows and dialogs)."""
import sys
from pathlib import Path

# Fallback path bootstrap if imported directly
try:
    import paths
except ImportError:
    parent = Path(__file__).resolve().parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    import paths
