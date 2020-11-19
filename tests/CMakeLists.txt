if(TARGET ${PROJECT_NAME}PythonInterface)
  find_package(
    Python3
    COMPONENTS Interpreter
    REQUIRED)

  add_test(NAME python-tests COMMAND Python3::Interpreter -m pytest --verbose)
  set_tests_properties(
    python-tests PROPERTIES WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    ENVIRONMENT "PYTHONPATH=$<TARGET_FILE_DIR:${PROJECT_NAME}PythonInterface>")
endif()
