cmake_minimum_required(VERSION 3.15)
project(TaintTracker)
set(CMAKE_CXX_STANDARD 17)

# Find LLVM and request components.
# This should define the LLVM_LIBRARIES and LLVM_INCLUDE_DIRS variables.
find_package(LLVM 20.1.8 REQUIRED CONFIG
  COMPONENTS
    Core
    IR
    Support
    PassPlugin
)

# Debug messages to see what find_package found
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")
message(STATUS "LLVM Includes: ${LLVM_INCLUDE_DIRS}")
message(STATUS "LLVM Libraries: ${LLVM_LIBRARIES}")

# Add our pass as a plugin
add_library(TaintTrackerPass MODULE
  TaintTrackerPass.cpp
)

# Use the old-style variables for includes and defines
target_include_directories(TaintTrackerPass PRIVATE
  ${LLVM_INCLUDE_DIRS}
)
target_compile_definitions(TaintTrackerPass PRIVATE
  ${LLVM_DEFINITIONS}
)

# Link against the old-style LLVM_LIBRARIES variable.
# The find_package call should populate this variable for us.
target_link_libraries(TaintTrackerPass PRIVATE
  ${LLVM_LIBRARIES}
)

# Match LLVM's CXX flags
set_target_properties(TaintTrackerPass PROPERTIES
  COMPILE_FLAGS "${LLVM_CXX_FLAGS}"
)
