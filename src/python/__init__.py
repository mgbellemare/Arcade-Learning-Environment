import platform
import sys
import os
from importlib.util import find_spec

if platform.system() == "Windows":
    if sys.version_info.major == 3 and sys.version_info.minor >= 8:
        # Loading DLLs on Windows is kind of a disaster
        # The best approach seems to be using LoadLibraryEx
        # with user defined search paths. This kind of acts like
        # $ORIGIN or @loader_path on Unix / macOS.
        # This way we guarantee we load OUR DLLs.
        packagedir = os.path.abspath(os.path.dirname(__file__))
        os.add_dll_directory(packagedir)

    try:
        import ctypes
        ctypes.CDLL('vcruntime140.dll')
        ctypes.CDLL('msvcp140.dll')
    except OSError:
        raise OSError("""Microsoft Visual C++ Redistribution Pack is not installed.
It can be downloaded from https://aka.ms/vs/16/release/vc_redist.x64.exe.""")

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

# Gym registration
if find_spec("gym") is not None:
    from . import gym
