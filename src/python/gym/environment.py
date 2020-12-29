import numpy as np
import gym
from gym import error, spaces
from gym import utils
from gym.utils import seeding

from typing import Optional, Union, Tuple, Dict, Any

from .. import roms, ALEInterface, Action, LoggerMode


class GymALE(ALEInterface, gym.Env, utils.EzPickle):
    """
    Arcade Learning Environment (ALE) Gym Wrapper.
    """
    # No render modes
    metadata = {'render.modes': []}

    def __init__(
            self,
            game: str = 'Pong',
            mode: Optional[int] = None,
            difficulty: Optional[int] = None,
            obs_type: str = 'rgb',
            frameskip: Union[Tuple[int, int], int] = 5,
            repeat_action_probability: float = 0.25,
            full_action_space: bool = True,
            render_mode: str = None) -> None:
        """
        Initialize the ALE for Gym.
        Default parameters are taken from Machado et al., 2018.

        Args:
          game: str => Game to initialize env with.
          mode: Optional[int] => Game mode, see Machado et al., 2018
          difficulty: Optional[int] => Game difficulty,see Machado et al., 2018
          obs_type: str => Observation type in { 'rgb', 'grayscale', 'ram' }
          frameskip: Union[Tuple[int, int], int] =>
              Stochastic frameskip as tuple or fixed.
          repeat_action_probability: int =>
              Probability to repeat actions, see Machado et al., 2018
          full_action_space: bool => Use full action space?
          render_mode: str => One of { 'human', 'rgb_array' }.
              If `human` we'll interactively display the screen and enable
              game sounds. This will lock emulation to the ROMs specified FPS
              If `rgb_array` we'll return the `rgb` key in step metadata with
              the current environment RGB frame.

        Note:
          - The game must be installed, see ale-import-roms, or ale-py-roms.
          - Frameskip values of (low, high) will enable stochastic frame skip
            which will sample a random frameskip uniformly each action.
          - It is recommended to enable full action space.
            See Machado et al., 2018 for more details.

        References:
            `Revisiting the Arcade Learning Environment: Evaluation Protocols
            and Open Problems for General Agents`, Machado et al., 2018, JAIR
            URL: https://jair.org/index.php/jair/article/view/11182
        """
        if obs_type not in {'rgb', 'grayscale', 'ram'}:
            raise error.Error(f"Invalid observation type: {obs_type}. Expecting: rgb, grayscale, ram.")
        if not (isinstance(frameskip, int) or (isinstance(frameskip, tuple) and len(frameskip) == 2)):
            raise error.Error(f"Invalid frameskip type: {frameskip}")
        if not hasattr(roms, game):
            raise error.Error(f"Unable to find {game}, did you import {game} with ale-import-roms?")
        if render_mode is not None and render_mode not in {'rgb_array', 'human'}:
            raise error.Error(f"Render mode {render_mode} not supported (rgb_array, human).")

        ALEInterface.__init__(self)
        utils.EzPickle.__init__(
                self,
                game,
                mode,
                difficulty,
                obs_type,
                frameskip,
                repeat_action_probability,
                full_action_space,
                render_mode)

        self._game = game
        self._game_mode = mode
        self._game_difficulty = difficulty

        self._frameskip = frameskip
        self._obs_type = obs_type
        self._render_mode = render_mode

        # Set logger mode to error only
        self.setLoggerMode(LoggerMode.Error)
        # Config sticky action prob.
        self.setFloat("repeat_action_probability", repeat_action_probability)

        # If render mode is human we can display screen and sound
        if render_mode == 'human':
            self.setBool("display_screen", True)
            self.setBool("sound", True)

        # Seed + Load
        self.seed()

        self._action_set = self.getLegalActionSet() if full_action_space else self.getMinimalActionSet()

        # Initialize observation type
        if self._obs_type == 'ram':
            self._obs = np.empty((self.getRAMSize(),), dtype=np.uint8)
        elif self._obs_type == 'rgb' or self._obs_type == 'grayscale':
            (screen_height, screen_width) = self.getScreenDims()
            image_channels = 3 if self._obs_type == 'rgb' else 1
            image_shape = (screen_height, screen_width, image_channels,)
            self._obs = np.empty(image_shape, dtype=np.uint8)
        else:
            raise error.Error(f"Unrecognized observation type: {self._obs_type}")

    def seed(self, seed: Optional[int] = None) -> Tuple[int, int]:
        """
        Seeds both the internal numpy rng for stochastic frame skip
        as well as the ALE RNG.

        This function must also initialize the ROM and set the corresponding
        mode and difficulty. `seed` may be called to initialize the environment
        during deserialization by Gym so these side-effects must reside here.

        Args:
            seed: int => Manually set the seed for RNG.
        Returns:
            tuple[int, int] => (np seed, ALE seed)
        """
        self.np_random, seed1 = seeding.np_random(seed)
        seed2 = seeding.hash_seed(seed1 + 1) % 2**31

        self.setInt("random_seed", seed2)
        self.loadROM(getattr(roms, self._game))

        if self._game_mode is not None:
            self.setMode(self._game_mode)
        if self._game_difficulty is not None:
            self.setDifficulty(self._game_difficulty)

        return (seed1, seed2,)

    def step(self, action_ind: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Perform one agent step, i.e., repeats `action` frameskip # of steps.

        Args:
            action_ind: int => Action index to execute

        Returns:
            Tuple[np.ndarray, float, bool, Dict[str, Any]] =>
                observation, reward, terminal, metadata 

        Note: `metadata` contains the keys "lives" and "rgb" if
              render_mode == 'rgb_array'.
        """
        # Get action enum, terminal bool, metadata
        action = self._action_set[action_ind]
        terminal = self.game_over()
        metadata = {'lives': self.lives()}

        # If frameskip is a length 2 tuple then it's stochastic
        # frameskip between [frameskip[0], frameskip[1]] uniformly.
        if isinstance(self._frameskip, int):
            frameskip = self._frameskip
        elif isinstance(self._frameskip, tuple):
            frameskip = self.np_random.randint(*self._frameskip)
        else:
            raise error.Error(f"Invalid frameskip type: {self._frameskip}")

        # Frameskip
        reward = 0.0
        for _ in range(frameskip):
            reward += self.act(action)

        # Copy over current observation
        self._get_obs()

        # Render rgb array, can't use self._obs as this isn't
        # guaranteed to be RGB.
        if self._render_mode == 'rgb_array':
            metadata['rgb'] = self.getScreenRGB()

        return self._obs, reward, terminal, metadata

    def reset(self) -> np.ndarray:
        """
        Resets environment and returns initial observation.
        """
        self.reset_game()
        self._get_obs()
        return self._obs

    def render(self, mode: str = 'human') -> None:
        """
        Render is not supported by ALE. We use a paradigm similar to
        Gym3 which allows you to specify `render_mode` during construction.

        For example,
            gym.make("ale-py:Pong-v0", render_mode="human")
        will display the ALE and maintain the proper interval to match the
        FPS target set by the ROM.
        """
        raise error.Error("""render() is unsupported by ALE.
            Please specify `render_mode` during environment initialization.""")

    def close(self) -> None:
        """
        Cleanup any leftovers by the environment
        """
        pass

    def _get_obs(self) -> np.ndarray:
        """
        Retreives the current observation using `self._obs` buffer.
        This is dependent on `self._obs_type`.
        """
        if self._obs_type == 'ram':
            self.getRAM(self._obs)
        elif self._obs_type == 'rgb':
            self.getScreenRGB(self._obs)
        elif self._obs_type == 'grayscale':
            self.getScreenGrayscale(self._obs)
        else:
            raise error.Error(f"Unrecognized observation type: {self._obs_type}")

    def get_keys_to_action(self) -> Dict[int, int]:
        """
        Return keymapping -> actions for human play.
        """
        return {
            ord('w'): Action.UP,
            ord('s'): Action.DOWN,
            ord('a'): Action.LEFT,
            ord('d'): Action.RIGHT,
            ord(' '): Action.FIRE
        }

    @property
    def action_space(self) -> spaces.Discrete:
        """
        Return Gym's action space.
        """
        return spaces.Discrete(len(self._action_set))

    @property
    def observation_space(self) -> spaces.Box:
        """
        Return Gym's observation space.
        """
        if self._obs_type == 'ram':
            return spaces.Box(low=0, high=255, dtype=np.uint8, shape=(self.getRAMSize(),))
        elif self._obs_type == 'rgb' or self._obs_type == 'grayscale':
            (screen_height, screen_width) = self.getScreenDims()
            image_channels = 3 if self._obs_type == 'rgb' else 1
            image_shape = (screen_height, screen_width, image_channels,)
            return spaces.Box(low=0, high=255, dtype=np.uint8, shape=image_shape)
        else:
            raise error.Error(f"Unrecognized observation type: {self._obs_type}")
