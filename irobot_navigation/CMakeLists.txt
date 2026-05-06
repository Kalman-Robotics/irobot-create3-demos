cmake_minimum_required(VERSION 3.5)
project(irobot_navigation)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

install(
  DIRECTORY config launch maps rviz behavior_tree
  DESTINATION share/${PROJECT_NAME}
)

ament_python_install_package(${PROJECT_NAME})
ament_python_install_module(${PROJECT_NAME}/irobot_navigator.py)

install(PROGRAMS
  irobot_navigation/robot_status_overlay.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME robot_status_overlay
)

install(PROGRAMS
  scripts/battery_monitor.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME battery_monitor
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
