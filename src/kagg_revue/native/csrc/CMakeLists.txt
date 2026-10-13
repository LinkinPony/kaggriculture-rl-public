# Native official-rules engine extension. Build via `python -m kagg_revue.native.build`.
cmake_minimum_required(VERSION 3.18)
project(revue_native LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PYBIND11_FINDPYTHON ON)
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(CUDAToolkit REQUIRED)
option(REVUE_ENABLE_OPENMP "Enable native batch parallelism" ON)
option(REVUE_STATIC_CXX_RUNTIME "Statically link the C++ and compiler runtimes" OFF)
if(REVUE_ENABLE_OPENMP)
  find_package(OpenMP)
endif()

pybind11_add_module(
  _revue_native
  action_codec.cpp
  action_control.cpp
  actor_bindings.cpp
  actor_encoding.cpp
  bindings.cpp
  core/engine.cpp
  conversion/actions.cpp
  conversion/configuration.cpp
  conversion/observations.cpp
  conversion/values.cpp
  boatlee/bindings.cpp
  boatlee/market.cpp
  boatlee/moon.cpp
  boatlee/replay.cpp
  boatlee/runtime.cpp
  boatlee/strategy.cpp
  boatlee/support.cpp
  capability.cpp
  capability_candidates.cpp
  capability_features.cpp
  fact_common.cpp
  fact_decision.cpp
  fact_turn.cpp
  engine.cpp
  derived/encode.cpp
  derived/execution.cpp
  derived/forecast.cpp
  derived/globals.cpp
  derived/interventions.cpp
  derived/investment.cpp
  derived/market.cpp
  derived/products.cpp
  effects/candidates.cpp
  effects/compiler.cpp
  effects/session.cpp
  intents/candidates.cpp
  intents/scheduler.cpp
  intents/session.cpp
  kaito_v48.cpp
  kaito_v48_bindings.cpp
  kaito_v48_support.cpp
  kaito_v39/bindings.cpp
  kaito_v39/market.cpp
  kaito_v39/policy.cpp
  kaito_v39/portfolio.cpp
  kaito_v39/runtime.cpp
  kaito_v39/strategy.cpp
  market.cpp
  mugundh/bindings.cpp
  mugundh/market.cpp
  mugundh/runtime.cpp
  mugundh/strategy.cpp
  mugundh/support.cpp
  opponents/batch.cpp
  opponents/bindings.cpp
  opponents/boatlee.cpp
  opponents/farming.cpp
  opponents/farming_budget.cpp
  opponents/kaito.cpp
  opponents/kaito_control.cpp
  opponents/kaito_preemption.cpp
  opponents/portfolio.cpp
  opponents/router.cpp
  opponents/runtime.cpp
  opponents/shop.cpp
  opponents/shop_reactive.cpp
  parallel/batch.cpp
  parallel/legacy.cpp
  parallel/fork.cpp
  parallel/replay.cpp
  parallel/bindings.cpp
  parallel/deployment.cpp
  parallel/encoding.cpp
  parallel/production.cpp
  parallel/work.cpp
  parallel/observation.cpp
  parallel/context.cpp
  production/rules.cpp
  production/features.cpp
  production/products.cpp
  production/geometry.cpp
  production/pricing.cpp
  production/ledger.cpp
  production/placement.cpp
  production/encode.cpp
  planner.cpp
  planner_bindings.cpp
  planner_scheduler.cpp
  planner_strategy.cpp
  planner_tasks.cpp
  plans/executor.cpp
  plans/session.cpp
  programs/compiler.cpp
  programs/masks.cpp
  programs/session.cpp
  tasks/candidates.cpp
  tasks/catalog.cpp
  tasks/compiler.cpp
  tasks/session.cpp
  policy_bindings.cpp
  policy_session.cpp
  rules_bindings.cpp
  turn_bindings.cpp
  unit_phase.cpp)
target_include_directories(_revue_native PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
file(GLOB PUBLIC_POLICY_SOURCES CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/opponents/compiled/*.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/opponents/compiled/generated/*.cpp")
target_sources(_revue_native PRIVATE ${PUBLIC_POLICY_SOURCES})
# Keep generated container control flow tractable to optimize; all policy branches
# remain ahead-of-time C++ instructions and use the target's strict FP options.
set_source_files_properties(${PUBLIC_POLICY_SOURCES} PROPERTIES COMPILE_OPTIONS "-O2")
# -ffp-contract=off: no FMA fusing, so double arithmetic matches CPython's
# unfused libm-based evaluation bit-for-bit. Do NOT add -ffast-math.
target_compile_options(_revue_native PRIVATE -Wall -Wextra -ffp-contract=off)
if(OpenMP_CXX_FOUND)
  target_link_libraries(_revue_native PRIVATE OpenMP::OpenMP_CXX)
endif()
if(REVUE_STATIC_CXX_RUNTIME)
  target_link_options(_revue_native PRIVATE -static-libstdc++ -static-libgcc
                      -Wl,--exclude-libs,ALL)
endif()

# Hopper-only training hot path.  It accepts raw CUDA graph/tensor addresses,
# so the main rules engine remains independent of the PyTorch C++ ABI.
pybind11_add_module(_program_cuda programs/gpu_graph.cu)
target_link_libraries(_program_cuda PRIVATE CUDA::cudart)
target_compile_options(
  _program_cuda PRIVATE
  $<$<COMPILE_LANGUAGE:CUDA>:--generate-code=arch=compute_90,code=sm_90>)
set_target_properties(
  _program_cuda PROPERTIES
  CUDA_STANDARD 20
  CUDA_STANDARD_REQUIRED ON
  CUDA_SEPARABLE_COMPILATION ON)

# Device-resident canonical intent construction and transition.  Like the
# graph helper, this uses raw addresses so the extension does not depend on the
# PyTorch C++ ABI.
pybind11_add_module(
  _intent_cuda
  intents/gpu_bindings.cu
  intents/gpu_candidates.cu
  intents/gpu_transition.cu)
target_include_directories(_intent_cuda PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(_intent_cuda PRIVATE CUDA::cudart)
target_compile_options(
  _intent_cuda PRIVATE
  $<$<COMPILE_LANGUAGE:CUDA>:--generate-code=arch=compute_90,code=sm_90>)
set_target_properties(
  _intent_cuda PROPERTIES
  CUDA_STANDARD 20
  CUDA_STANDARD_REQUIRED ON
  CUDA_SEPARABLE_COMPILATION ON)
