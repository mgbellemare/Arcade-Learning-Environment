import os
import argparse

from shutil import copyfile
from importlib.util import find_spec

from sys import exit

from .. import __version__, ALEInterface


def scantree(dir, recurse=True):
    with os.scandir(dir) as root:
        for entry in root:
            if recurse and entry.is_dir(follow_symlinks=False):
                yield from scantree(entry.path)
            elif entry.is_file():
                yield entry


def import_roms(romdir, datadir):
    # Log stats
    imported, seen = 0, 0
    invalids = []

    for entry in scantree(romdir):
        seen += 1
        path = entry.path
        rom = ALEInterface.isSupportedROM(path)
        if rom is not None:
            imported += 1
            rom = rom.title().replace('_', '')
            copyfile(path, os.path.join(datadir, f"{rom}.bin"))
            print(f"{'[SUPPORTED]': <15} {f'{path} : {rom}': >15}")
        else:
            invalids += [path]
            print(f"{'[NOT SUPPORTED]': <15} {path: >15}")

    print(f"\nImported {imported} / {seen} ROMs")
    if len(invalids) > 0:
        invalids = '\n\t'.join(invalids)
        print(f"Failed to verify:{invalids}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action='version', version=__version__)
    parser.add_argument("romdir", help="Directory containing ROMs")
    args = parser.parse_args()

    romdir = args.romdir
    rom_spec = find_spec(".roms", package=__package__)

    if rom_spec is None:
        print("Failed to retrieve ale-py ROM path, are you using the pip package?")
        exit(1)
    datadir = rom_spec.submodule_search_locations[0]

    import_roms(romdir, datadir)


if __name__ == '__main__':
    main()
