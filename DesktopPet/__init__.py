"""DesktopPet package initialization."""
import sys
from pathlib import Path

# Ensure paths bootstrap is loaded
try:
    from . import paths
except ImportError:
    pass
