#!/bin/bash

set -ex

cd tool

# FIXME the library list seems unstable. Maybe we need to build the tool
# in LLVM tree with a fixed version.
bear -- clang++ constant_analysis.cpp -o constant_analysis \
    -lclangTooling \
    -lclangFrontend \
    -lclangSerialization \
    -lclangDriver \
    -lclangParse \
    -lclangSema \
    -lclangEdit \
    -lclangAnalysis \
    -lclangASTMatchers \
    -lclangAST \
    -lclangLex \
    -lclangBasic \
    -lclangAPINotes \
    -lclangCrossTU \
    -lclangStaticAnalyzerFrontend \
    -lclangSupport \
    -lclangCodeGen \
    -lclangBasic \
    `llvm-config --cxxflags --ldflags --system-libs --libs all`
