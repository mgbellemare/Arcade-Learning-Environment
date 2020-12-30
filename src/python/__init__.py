# TODO Py38: Once 3.7 is deprecated use importlib.metadata to parse
# version string from package.
try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata
try:
    __version__ = importlib_metadata.version(__package__)
except importlib_metadata.PackageNotFoundError:
    __version__ = "unknown"

# Import native shared library
from ._ale_py import *

# Exported symbols
__all__ = ["ALEInterface", "ALEState", "Action", "LoggerMode", "__version__"]
