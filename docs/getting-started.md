# Installation

## Python Interface

The Python interface `ale-py` supports the follow 64 bit systems running Python 3.6 or newer:

* Windows 7+
* macOS 10.9+
* Linux Distros supporting [manylinux2014](https://www.python.org/dev/peps/pep-0571/)


To install the Python interface from PyPi simply run:

```bash
pip install https://github.com/mgbellemare/Arcade-Learning-Environment
```

Once installed you can import the native ALE interface as `ale_py`

```python
from ale_py import ALEInterface
ale = ALEInterface()
```

## C++ Interface

The C++ library requires:

* A C++17 compiler
* CMake 3.14+
* zlib
* (Optional) SDL 1.X for display/audio support 

SDL support allows for displaying the console's screen and enabling audio output. For example, *without* SDL support you'll still be able to train your agents, but you won't be able to visualize the resulting policy. It might be preferable to disable SDL support when compiled on a cluster but enable SDL locally. Note: SDL support defaults to **OFF**.

You can use any package manager to install these dependencies but we recommend using [`vcpkg`](https://github.com/microsoft/vcpkg). Here's a minimal example of installing these dependencies and building/installing the C++ library.

```sh
vcpkg install zlib sdl

mkdir build && cd build
cmake ../ -DCMAKE_BUILD_TYPE=Release
cmake --build . --target install # remove `--target install` for Windows builds
```

These steps will work on any platform, just make sure to specify the environment variable `VCPKG_INSTALLATION_ROOT` to point to your vcpkg installation so we can find the required dependencies. If you install any vcpkg dependencies using non-standard triplets you can specify the environment variable `VCPKG_TARGET_TRIPLET`. For more info check out the [vcpkg docs](https://vcpkg.readthedocs.io/en/latest/users/config-environment/) on how to configure your environment.

Once the ALE is installed you can link agaisnt the library in your C++ project as follows

```cmake
find_package(ale REQUIRED)
target_link_libraries(YourTarget ale::ale-lib)
```
