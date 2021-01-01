from .. import ALEInterface
from .import_roms import main as import_roms

from typing import Dict

try:
    import importlib.resources as resources
except ImportError:
    import importlib_resources as resources

from pkg_resources import iter_entry_points


def find_internal_roms(package: str) -> Dict[str, str]:
    roms = {}
    # Iterate over ROMs in `packages`'s resources
    for resource in filter(
        lambda file: file.endswith(".bin"), resources.contents(package)
    ):
        with resources.path(package, resource) as path:
            path = str(path.resolve())
            rom = ALEInterface.isSupportedROM(path)
            if rom is None:
                raise ImportError(
                    f"ROM {path} is not supported, did you import via ale-import-roms?"
                )

            # ROM names are snake case in ALE, convert to camel case.
            romid = rom.title().replace("_", "")
            roms[romid] = path
    return roms


def find_external_roms(group: str) -> Dict[str, str]:
    roms = {}
    # Iterate over all entrypoints in this group
    for external in iter_entry_points(group):
        # We load the external load ROM function and
        # update the ROM dict with the result
        try:
            external_find_roms = external.load()
            roms.update(external_find_roms())
        except Exception:
            print(f"Failed to load ROMs from external {external}")

    return roms


all = {}
all.update(find_internal_roms(__package__))
all.update(find_external_roms(__package__))

globals().update(all)
__all__ = list(all.keys())
