# CPU observation execution only. No CUDA, training engine, or script strategies.
cmake_minimum_required(VERSION 3.18)
project(revue_observation LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(PYBIND11_FINDPYTHON ON)
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
option(REVUE_STATIC_CXX_RUNTIME "Statically link the C++ and compiler runtimes" ON)

pybind11_add_module(
  _revue_observation
  bindings.cpp
  ../action_codec.cpp
  ../actor_encoding.cpp
  ../conversion/actions.cpp
  ../conversion/configuration.cpp
  ../conversion/observations.cpp
  ../conversion/values.cpp
  ../market.cpp
  ../derived/encode.cpp
  ../derived/execution.cpp
  ../derived/forecast.cpp
  ../derived/globals.cpp
  ../derived/interventions.cpp
  ../derived/investment.cpp
  ../derived/market.cpp
  ../derived/products.cpp
  ../parallel/deployment.cpp
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
  ../parallel/work.cpp
  ../unit_phase.cpp)
target_include_directories(_revue_observation PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_compile_options(_revue_observation PRIVATE -Wall -Wextra -ffp-contract=off)
if(REVUE_STATIC_CXX_RUNTIME)
  target_link_options(_revue_observation PRIVATE -static-libstdc++ -static-libgcc
                      -Wl,--exclude-libs,ALL)
endif()
