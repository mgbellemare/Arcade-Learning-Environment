from collections import defaultdict
from itertools import product

from gym.envs.registration import register
from .environment import GymALE
from .. import roms

# We don't export anything
__all__ = []

obs_types = ['rgb', 'ram']
frameskip = defaultdict(lambda: 4, [("SpaceInvaders", 3)])
full_action_space = False

versions = [
    ('v0', {'repeat_action_probability': 0.25}),
    ('v4', {'repeat_action_probability': 0.0})
]

configs = [
    ('', {'frameskip': (2, 5)}),
    ('Deterministic', lambda rom: {'frameskip': frameskip[rom]}),
    ('NoFrameskip', {'frameskip': 1})
]

for rom in roms.__all__:
    for obs_type in obs_types:
        name = rom
        if obs_type == 'ram':
            name = f"{name}-ram"

        nondeterministic = False
        max_episode_steps = 10000
        kwargs = {'game': rom, 'obs_type': obs_type, 'full_action_space': full_action_space}

        for (config_prefix, config_kwargs), (version_suffix, version_kwargs) in product(configs, versions):
            if callable(config_kwargs):
                config_kwargs = config_kwargs(rom)
            if callable(version_kwargs):
                version_kwargs = version_kwargs(rom)

            register(
                id=f"{name}{config_prefix}-{version_suffix}",
                entry_point=GymALE,
                kwargs=dict(**kwargs, **config_kwargs, **version_kwargs),
                max_episode_steps=max_episode_steps,
                nondeterministic=nondeterministic
            )
