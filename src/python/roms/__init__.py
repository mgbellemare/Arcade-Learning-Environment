import os
from .. import ALEInterface
from .import_roms import main as import_roms

roms = dict()
here = os.path.abspath(os.path.dirname(__file__))

with os.scandir(here) as root:
    for entry in root:
        if not (entry.is_file() and entry.name.endswith('.bin')):
            continue

        path = entry.path
        rom = ALEInterface.isSupportedROM(path)

        if rom is None:
            raise ImportError(f"{entry.name} is not a supported ROM, did you import ROMS via ale-import-roms?")

        rom = rom.title().replace('_', '')
        roms[rom] = path

__all__ = list(roms.keys())

globals().update(roms)
