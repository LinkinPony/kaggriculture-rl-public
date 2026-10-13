# Official rules and neural self-play, without script strategies or CUDA tools.
cmake_minimum_required(VERSION 3.18)
project(revue_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(PYBIND11_FINDPYTHON ON)
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
option(REVUE_ENABLE_OPENMP "Enable native self-play parallelism" ON)
if(REVUE_ENABLE_OPENMP)
  find_package(OpenMP REQUIRED)
endif()

pybind11_add_module(
  _revue_core
  bindings.cpp
  engine.cpp
  ../action_codec.cpp
  ../actor_encoding.cpp
  ../conversion/actions.cpp
  ../conversion/configuration.cpp
  ../conversion/observations.cpp
  ../conversion/values.cpp
  ../engine.cpp
  ../derived/encode.cpp
  ../derived/execution.cpp
  ../derived/forecast.cpp
  ../derived/globals.cpp
  ../derived/interventions.cpp
  ../derived/investment.cpp
  ../derived/market.cpp
  ../derived/products.cpp
  ../market.cpp
  ../parallel/batch.cpp
  ../parallel/deployment.cpp
  ../parallel/encoding.cpp
  ../parallel/fork.cpp
  ../parallel/observation.cpp
  ../parallel/context.cpp
  ../production/rules.cpp
  ../production/features.cpp
  ../production/products.cpp
  ../production/geometry.cpp
  ../production/pricing.cpp
  ../production/ledger.cpp
  ../production/placement.cpp
  ../production/encode.cpp
  ../parallel/production.cpp
  ../parallel/replay.cpp
  ../parallel/work.cpp
  ../unit_phase.cpp)
target_include_directories(_revue_core PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_compile_options(_revue_core PRIVATE -Wall -Wextra -ffp-contract=off)
if(REVUE_ENABLE_OPENMP)
  target_link_libraries(_revue_core PRIVATE OpenMP::OpenMP_CXX)
endif()
