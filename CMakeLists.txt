cmake_minimum_required(VERSION 3.15)
project(TaintTracker)

# Find the installed LLVM
# You may need to provide a path: cmake .. -DLLVM_DIR=/path/to/llvm/lib/cmake/llvm
find_package(LLVM REQUIRED CONFIG)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)

# Add our pass source file
add_library(TaintTrackerPass MODULE
  TaintTrackerPass.cpp
)

# Link against the necessary LLVM components
llvm_use_linker(TaintTrackerPass)
llvm_add_to_library(TaintTrackerPass
  TaintTrackerPass.cpp
  PLUGIN_TOOL opt
)

# Include LLVM headers
target_include_directories(TaintTrackerPass PRIVATE
  ${LLVM_INCLUDE_DIRS}
)
