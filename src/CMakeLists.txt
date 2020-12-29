option(BUILD_PYTHON_LIB "Build Python Interface" ON)
option(BUILD_CPP_LIB "Build C++ Interface" ON)
option(SDL_SUPPORT "Enable SDL support" ON)

# Include src/ and cmake binary directory (for version.hpp)
include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}
                    ${CMAKE_CURRENT_BINARY_DIR})

# Project specific target properties
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED TRUE)
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)

# Compiler options
add_compile_options(
  "$<$<CONFIG:RELEASE>:-O3>" "$<$<CONFIG:DEBUG>:-O0>"
  "$<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall>"
  "$<$<CXX_COMPILER_ID:MSVC>:/W4>")

# ale object containing source files
add_library(${PROJECT_NAME} OBJECT)

# Dependencies
find_package(ZLIB REQUIRED)
find_package(Threads REQUIRED)
target_link_libraries(${PROJECT_NAME} PRIVATE ZLIB::ZLIB Threads::Threads)

if(SDL_SUPPORT)
  option(SDL_DYNLOAD "Dynamically load SDL" OFF)
  find_package(SDL2 CONFIG REQUIRED)

  # VCPKG doesn't include SDL2_INCLUDE_DIRS
  if(VCPKG_TOOLCHAIN)
    find_path(SDL2_INCLUDE_DIRS SDL.h PATH_SUFFIXES SDL2)
  endif()

  target_compile_definitions(
    ${PROJECT_NAME}
    PUBLIC SDL_SUPPORT
    PRIVATE $<$<BOOL:${SDL_DYNLOAD}>:SDL_DYNLOAD>)
  target_link_libraries(${PROJECT_NAME} PRIVATE $<$<NOT:$<BOOL:${SDL_DYNLOAD}>>:SDL2::SDL2>)
  target_include_directories(${PROJECT_NAME} PRIVATE ${SDL2_INCLUDE_DIRS})
endif()

# Add submodules
add_subdirectory(common)
add_subdirectory(emucore)
add_subdirectory(os_dependent)
add_subdirectory(environment)
add_subdirectory(games)

configure_file("version.hpp.in" "version.hpp")

# C++ Library
if(BUILD_CPP_LIB)
  add_library(${PROJECT_NAME}Interface ale_interface.cpp)
  set_target_properties(${PROJECT_NAME}Interface PROPERTIES OUTPUT_NAME $<LOWER_CASE:${PROJECT_NAME}>)
  target_link_libraries(${PROJECT_NAME}Interface PUBLIC ${PROJECT_NAME})
endif()

# Python Interface
if(BUILD_PYTHON_LIB)
  find_package(
    Python3
    COMPONENTS Interpreter Development.Module
    REQUIRED)

  include(FetchContent)
  FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11
    GIT_TAG v2.6.1)
  FetchContent_MakeAvailable(pybind11)

  add_library(${PROJECT_NAME}PythonInterface MODULE ale_interface.cpp ale_python_interface.cpp)
  target_link_libraries(${PROJECT_NAME}PythonInterface PUBLIC ${PROJECT_NAME})
  target_link_libraries(${PROJECT_NAME}PythonInterface PRIVATE pybind11::module)
  set_target_properties(
    ${PROJECT_NAME}PythonInterface
    PROPERTIES OUTPUT_NAME _$<LOWER_CASE:${PROJECT_NAME}>_py
               PREFIX "${PYTHON_MODULE_PREFIX}"
               SUFFIX "${PYTHON_MODULE_EXTENSION}")
  # If we're dynamically loading SDL with Python we'll be build a wheel
  # so we should prepare SDL for distribution. Add rpath and copy over
  # the dynamic library. auditwheel will take care of ensuring
  # corss-platform compatability on macOS and Linux.
  if(SDL_SUPPORT AND SDL_DYNLOAD)
    set_target_properties(
      ${PROJECT_NAME}PythonInterface
      PROPERTIES
        INSTALL_RPATH_USE_ORIGIN TRUE
        BUILD_WITH_INSTALL_RPATH TRUE
        SKIP_BUILD_RPATH FALSE
        INSTALL_RPATH_USE_LINK_PATH FALSE
        MACOSX_RPATH TRUE
        INSTALL_RPATH
        "$<$<PLATFORM_ID:Darwin>:@loader_path>$<$<PLATFORM_ID:Linux>:\$ORIGIN>")

    target_compile_definitions(
      ${PROJECT_NAME} PRIVATE SDL2_LIBRARY_NAME="$<TARGET_FILE_NAME:SDL2::SDL2>")
    add_custom_command(
      TARGET ${PROJECT_NAME}PythonInterface
      POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:SDL2::SDL2>
      $<TARGET_FILE_DIR:${PROJECT_NAME}PythonInterface>)
  endif()
endif()

# Install cpp-lib and CMake config & pkg-config
if(UNIX AND BUILD_CPP_LIB)
  include(GNUInstallDirs)
  include(CMakePackageConfigHelpers)

  string(TOLOWER ${PROJECT_NAME} INSTALL_DIR)

  install(
    TARGETS ${PROJECT_NAME} ${PROJECT_NAME}Interface
    EXPORT ${PROJECT_NAME}Config
    INCLUDES
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/${INSTALL_DIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})

  # Install Header files
  install(
    DIRECTORY ${CMAKE_CURRENT_LIST_DIR}/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/${INSTALL_DIR}
    FILES_MATCHING
    REGEX "\.h((pp)?|(xx?))$"
    REGEX "os_dependent\/.*(Win32)\.(h|h(xx)?|h(pp)?|c(xx)?|c(pp)?)$" EXCLUDE)

  # Install configured version file
  install(FILES ${CMAKE_CURRENT_BINARY_DIR}/version.hpp
          DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/${INSTALL_DIR})

  # Export cmake targets
  install(
    EXPORT ${PROJECT_NAME}Config
    FILE ${PROJECT_NAME}Targets.cmake
    NAMESPACE ${PROJECT_NAME}::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${INSTALL_DIR})

  # Write config version
  write_basic_package_version_file(
    ${PROJECT_NAME}ConfigVersion.cmake
    VERSION ${PACKAGE_VERSION}
    COMPATIBILITY AnyNewerVersion)

  # Configure installable cmake config
  configure_package_config_file(
    ${CMAKE_MODULE_PATH}/${PROJECT_NAME}Config.cmake.in
    ${PROJECT_NAME}Config.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${INSTALL_DIR})

  # Install config version and config
  install(FILES "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
                "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
          DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${INSTALL_DIR})
endif()
