# Expose the core class from the internal module for easy access
from .fpml_semantic_model import FpMLBaseModel

# Define the package version (matching setup.py)
__version__ = "0.2.3"

__all__ = [
    "FpMLBaseModel"
]