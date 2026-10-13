// Device-controlled CUDA graph loop for the H200 conditional-program actor.

#include <cuda_runtime.h>

#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace {

void Check(cudaError_t status, const char* operation) {
  if (status != cudaSuccess) {
    throw std::runtime_error(std::string(operation) + ": " +
                             cudaGetErrorString(status));
  }
}

__global__ void ContinueWhile(cudaGraphConditionalHandle handle,
                              const int32_t* state, int rows,
                              int state_width) {
  __shared__ int live;
  if (threadIdx.x == 0) live = 0;
  __syncthreads();
  for (int row = static_cast<int>(threadIdx.x); row < rows;
       row += static_cast<int>(blockDim.x)) {
    if (state[static_cast<int64_t>(row) * state_width + 4] != 2) {
      atomicExch(&live, 1);
    }
  }
  __syncthreads();
  if (threadIdx.x == 0) cudaGraphSetConditional(handle, live);
}

__global__ void SelectBucket(cudaGraphConditionalHandle handle,
                             const int64_t* active_count,
                             int variant_count,
                             int initial_capacity) {
  if (threadIdx.x != 0) return;
  int64_t count = *active_count;
  unsigned int bucket = 0;
  int64_t capacity = initial_capacity;
  while (capacity < count && bucket + 1 < static_cast<unsigned int>(variant_count)) {
    capacity <<= 1;
    ++bucket;
  }
  cudaGraphSetConditional(handle, bucket);
}

__global__ void ContinueCount(cudaGraphConditionalHandle handle,
                              const int64_t* live_count) {
  if (threadIdx.x == 0) cudaGraphSetConditional(handle, *live_count > 0);
}

__global__ void SelectVariant(cudaGraphConditionalHandle handle,
                              const int64_t* variant,
                              int variant_count) {
  if (threadIdx.x != 0) return;
  int64_t selected = *variant;
  if (selected < 0) selected = 0;
  if (selected >= variant_count) selected = variant_count - 1;
  cudaGraphSetConditional(handle, static_cast<unsigned int>(selected));
}

class ConditionalWhileGraph {
 public:
  ConditionalWhileGraph(uintptr_t body_graph, uintptr_t state, int rows,
                        int state_width)
      : state_(reinterpret_cast<const int32_t*>(state)),
        rows_(rows),
        state_width_(state_width) {
    if (body_graph == 0 || state == 0 || rows < 1 || state_width < 5) {
      throw std::invalid_argument("conditional CUDA graph arguments are invalid");
    }
    Check(cudaGraphCreate(&graph_, 0), "cudaGraphCreate");
    try {
      Check(cudaGraphConditionalHandleCreate(
                &handle_, graph_, 1, cudaGraphCondAssignDefault),
            "cudaGraphConditionalHandleCreate");
      cudaGraphNodeParams conditional{};
      conditional.type = cudaGraphNodeTypeConditional;
      conditional.conditional.handle = handle_;
      conditional.conditional.type = cudaGraphCondTypeWhile;
      conditional.conditional.size = 1;
      Check(cudaGraphAddNode(&conditional_node_, graph_, nullptr, nullptr, 0,
                             &conditional),
            "cudaGraphAddNode(while)");
      cudaGraph_t while_body = conditional.conditional.phGraph_out[0];
      cudaGraphNode_t child_node{};
      Check(cudaGraphAddChildGraphNode(
                &child_node, while_body, nullptr, 0,
                reinterpret_cast<cudaGraph_t>(body_graph)),
            "cudaGraphAddChildGraphNode");

      void* arguments[] = {&handle_, &state_, &rows_, &state_width_};
      cudaKernelNodeParams kernel{};
      kernel.func = reinterpret_cast<void*>(ContinueWhile);
      kernel.gridDim = dim3(1);
      kernel.blockDim = dim3(256);
      kernel.sharedMemBytes = 0;
      kernel.kernelParams = arguments;
      cudaGraphNode_t continuation{};
      Check(cudaGraphAddKernelNode(&continuation, while_body, &child_node, 1,
                                   &kernel),
            "cudaGraphAddKernelNode(continuation)");
      Check(cudaGraphInstantiate(&executable_, graph_, 0),
            "cudaGraphInstantiate");
    } catch (...) {
      if (executable_ != nullptr) cudaGraphExecDestroy(executable_);
      cudaGraphDestroy(graph_);
      graph_ = nullptr;
      executable_ = nullptr;
      throw;
    }
  }

  ConditionalWhileGraph(const ConditionalWhileGraph&) = delete;
  ConditionalWhileGraph& operator=(const ConditionalWhileGraph&) = delete;

  ~ConditionalWhileGraph() {
    if (executable_ != nullptr) cudaGraphExecDestroy(executable_);
    if (graph_ != nullptr) cudaGraphDestroy(graph_);
  }

  void Launch(uintptr_t stream) {
    Check(cudaGraphLaunch(executable_, reinterpret_cast<cudaStream_t>(stream)),
          "cudaGraphLaunch");
  }

 private:
  cudaGraph_t graph_ = nullptr;
  cudaGraphExec_t executable_ = nullptr;
  cudaGraphNode_t conditional_node_ = nullptr;
  cudaGraphConditionalHandle handle_{};
  const int32_t* state_ = nullptr;
  int rows_ = 0;
  int state_width_ = 0;
};

class ConditionalSwitchWhileGraph {
 public:
  ConditionalSwitchWhileGraph(uintptr_t setup_graph,
                              const py::iterable& variant_graphs,
                              uintptr_t state, uintptr_t active_count,
                              int rows, int state_width)
      : state_(reinterpret_cast<const int32_t*>(state)),
        active_count_(reinterpret_cast<const int64_t*>(active_count)),
        rows_(rows),
        state_width_(state_width) {
    std::vector<cudaGraph_t> variants;
    for (const py::handle item : variant_graphs) {
      variants.push_back(reinterpret_cast<cudaGraph_t>(py::cast<uintptr_t>(item)));
    }
    if (setup_graph == 0 || variants.empty() || state == 0 ||
        active_count == 0 || rows < 1 || state_width < 5) {
      throw std::invalid_argument("switch CUDA graph arguments are invalid");
    }
    variant_count_ = static_cast<int>(variants.size());
    Check(cudaGraphCreate(&graph_, 0), "cudaGraphCreate");
    try {
      Check(cudaGraphConditionalHandleCreate(
                &while_handle_, graph_, 1, cudaGraphCondAssignDefault),
            "cudaGraphConditionalHandleCreate(while)");
      cudaGraphNodeParams while_params{};
      while_params.type = cudaGraphNodeTypeConditional;
      while_params.conditional.handle = while_handle_;
      while_params.conditional.type = cudaGraphCondTypeWhile;
      while_params.conditional.size = 1;
      Check(cudaGraphAddNode(&while_node_, graph_, nullptr, nullptr, 0,
                             &while_params),
            "cudaGraphAddNode(while)");
      cudaGraph_t while_body = while_params.conditional.phGraph_out[0];
      cudaGraphNode_t setup{};
      Check(cudaGraphAddChildGraphNode(
                &setup, while_body, nullptr, 0,
                reinterpret_cast<cudaGraph_t>(setup_graph)),
            "cudaGraphAddChildGraphNode(setup)");

      Check(cudaGraphConditionalHandleCreate(&switch_handle_, graph_, 0, 0),
            "cudaGraphConditionalHandleCreate(switch)");
      void* select_arguments[] = {
          &switch_handle_, &active_count_, &variant_count_,
          &initial_capacity_};
      cudaKernelNodeParams select_kernel{};
      select_kernel.func = reinterpret_cast<void*>(SelectBucket);
      select_kernel.gridDim = dim3(1);
      select_kernel.blockDim = dim3(1);
      select_kernel.kernelParams = select_arguments;
      cudaGraphNode_t select{};
      Check(cudaGraphAddKernelNode(&select, while_body, &setup, 1,
                                   &select_kernel),
            "cudaGraphAddKernelNode(select bucket)");

      cudaGraphNodeParams switch_params{};
      switch_params.type = cudaGraphNodeTypeConditional;
      switch_params.conditional.handle = switch_handle_;
      switch_params.conditional.type = cudaGraphCondTypeSwitch;
      switch_params.conditional.size = variants.size();
      Check(cudaGraphAddNode(&switch_node_, while_body, &select, nullptr, 1,
                             &switch_params),
            "cudaGraphAddNode(switch)");
      for (size_t index = 0; index < variants.size(); ++index) {
        cudaGraphNode_t child{};
        Check(cudaGraphAddChildGraphNode(
                  &child, switch_params.conditional.phGraph_out[index],
                  nullptr, 0, variants[index]),
              "cudaGraphAddChildGraphNode(variant)");
      }

      void* continuation_arguments[] = {
          &while_handle_, &state_, &rows_, &state_width_};
      cudaKernelNodeParams continuation_kernel{};
      continuation_kernel.func = reinterpret_cast<void*>(ContinueWhile);
      continuation_kernel.gridDim = dim3(1);
      continuation_kernel.blockDim = dim3(256);
      continuation_kernel.kernelParams = continuation_arguments;
      cudaGraphNode_t continuation{};
      Check(cudaGraphAddKernelNode(&continuation, while_body, &switch_node_, 1,
                                   &continuation_kernel),
            "cudaGraphAddKernelNode(continuation)");
      Check(cudaGraphInstantiate(&executable_, graph_, 0),
            "cudaGraphInstantiate");
    } catch (...) {
      if (executable_ != nullptr) cudaGraphExecDestroy(executable_);
      cudaGraphDestroy(graph_);
      graph_ = nullptr;
      executable_ = nullptr;
      throw;
    }
  }

  ConditionalSwitchWhileGraph(const ConditionalSwitchWhileGraph&) = delete;
  ConditionalSwitchWhileGraph& operator=(
      const ConditionalSwitchWhileGraph&) = delete;

  ~ConditionalSwitchWhileGraph() {
    if (executable_ != nullptr) cudaGraphExecDestroy(executable_);
    if (graph_ != nullptr) cudaGraphDestroy(graph_);
  }

  void Launch(uintptr_t stream) {
    Check(cudaGraphLaunch(executable_, reinterpret_cast<cudaStream_t>(stream)),
          "cudaGraphLaunch");
  }

 private:
  cudaGraph_t graph_ = nullptr;
  cudaGraphExec_t executable_ = nullptr;
  cudaGraphNode_t while_node_ = nullptr;
  cudaGraphNode_t switch_node_ = nullptr;
  cudaGraphConditionalHandle while_handle_{};
  cudaGraphConditionalHandle switch_handle_{};
  const int32_t* state_ = nullptr;
  const int64_t* active_count_ = nullptr;
  int rows_ = 0;
  int state_width_ = 0;
  int variant_count_ = 0;
  int initial_capacity_ = 1;
};

class ConditionalCountSwitchWhileGraph {
 public:
  ConditionalCountSwitchWhileGraph(const py::iterable& setup_graphs,
                                   uintptr_t setup_variant,
                                   const py::iterable& variant_graphs,
                                   uintptr_t live_count,
                                   uintptr_t continuation_count,
                                   int initial_capacity)
      : setup_variant_(reinterpret_cast<const int64_t*>(setup_variant)),
        live_count_(reinterpret_cast<const int64_t*>(live_count)),
        continuation_count_(
            reinterpret_cast<const int64_t*>(continuation_count)),
        initial_capacity_(initial_capacity) {
    std::vector<cudaGraph_t> setups;
    for (const py::handle item : setup_graphs) {
      setups.push_back(reinterpret_cast<cudaGraph_t>(py::cast<uintptr_t>(item)));
    }
    std::vector<cudaGraph_t> variants;
    for (const py::handle item : variant_graphs) {
      variants.push_back(reinterpret_cast<cudaGraph_t>(py::cast<uintptr_t>(item)));
    }
    if (setups.empty() || setup_variant == 0 || variants.empty() ||
        live_count == 0 || continuation_count == 0 || initial_capacity < 1) {
      throw std::invalid_argument(
          "count-switch CUDA graph arguments are invalid");
    }
    setup_count_ = static_cast<int>(setups.size());
    variant_count_ = static_cast<int>(variants.size());
    Check(cudaGraphCreate(&graph_, 0), "cudaGraphCreate");
    try {
      Check(cudaGraphConditionalHandleCreate(
                &while_handle_, graph_, 1, cudaGraphCondAssignDefault),
            "cudaGraphConditionalHandleCreate(while)");
      cudaGraphNodeParams while_params{};
      while_params.type = cudaGraphNodeTypeConditional;
      while_params.conditional.handle = while_handle_;
      while_params.conditional.type = cudaGraphCondTypeWhile;
      while_params.conditional.size = 1;
      Check(cudaGraphAddNode(&while_node_, graph_, nullptr, nullptr, 0,
                             &while_params),
            "cudaGraphAddNode(while)");
      cudaGraph_t while_body = while_params.conditional.phGraph_out[0];

      Check(cudaGraphConditionalHandleCreate(&setup_handle_, graph_, 0, 0),
            "cudaGraphConditionalHandleCreate(setup switch)");
      void* setup_select_arguments[] = {
          &setup_handle_, &setup_variant_, &setup_count_};
      cudaKernelNodeParams setup_select_kernel{};
      setup_select_kernel.func = reinterpret_cast<void*>(SelectVariant);
      setup_select_kernel.gridDim = dim3(1);
      setup_select_kernel.blockDim = dim3(1);
      setup_select_kernel.kernelParams = setup_select_arguments;
      cudaGraphNode_t setup_select{};
      Check(cudaGraphAddKernelNode(&setup_select, while_body, nullptr, 0,
                                   &setup_select_kernel),
            "cudaGraphAddKernelNode(select setup)");

      cudaGraphNodeParams setup_switch_params{};
      setup_switch_params.type = cudaGraphNodeTypeConditional;
      setup_switch_params.conditional.handle = setup_handle_;
      setup_switch_params.conditional.type = cudaGraphCondTypeSwitch;
      setup_switch_params.conditional.size = setups.size();
      Check(cudaGraphAddNode(&setup_switch_node_, while_body, &setup_select,
                             nullptr, 1, &setup_switch_params),
            "cudaGraphAddNode(setup switch)");
      for (size_t index = 0; index < setups.size(); ++index) {
        cudaGraphNode_t child{};
        Check(cudaGraphAddChildGraphNode(
                  &child, setup_switch_params.conditional.phGraph_out[index],
                  nullptr, 0, setups[index]),
              "cudaGraphAddChildGraphNode(setup variant)");
      }

      Check(cudaGraphConditionalHandleCreate(&switch_handle_, graph_, 0, 0),
            "cudaGraphConditionalHandleCreate(switch)");
      void* select_arguments[] = {
          &switch_handle_, &live_count_, &variant_count_,
          &initial_capacity_};
      cudaKernelNodeParams select_kernel{};
      select_kernel.func = reinterpret_cast<void*>(SelectBucket);
      select_kernel.gridDim = dim3(1);
      select_kernel.blockDim = dim3(1);
      select_kernel.kernelParams = select_arguments;
      cudaGraphNode_t select{};
      Check(cudaGraphAddKernelNode(&select, while_body, &setup_switch_node_, 1,
                                   &select_kernel),
            "cudaGraphAddKernelNode(select bucket)");

      cudaGraphNodeParams switch_params{};
      switch_params.type = cudaGraphNodeTypeConditional;
      switch_params.conditional.handle = switch_handle_;
      switch_params.conditional.type = cudaGraphCondTypeSwitch;
      switch_params.conditional.size = variants.size();
      Check(cudaGraphAddNode(&switch_node_, while_body, &select, nullptr, 1,
                             &switch_params),
            "cudaGraphAddNode(switch)");
      for (size_t index = 0; index < variants.size(); ++index) {
        cudaGraphNode_t child{};
        Check(cudaGraphAddChildGraphNode(
                  &child, switch_params.conditional.phGraph_out[index],
                  nullptr, 0, variants[index]),
              "cudaGraphAddChildGraphNode(variant)");
      }

      void* continuation_arguments[] = {&while_handle_, &continuation_count_};
      cudaKernelNodeParams continuation_kernel{};
      continuation_kernel.func = reinterpret_cast<void*>(ContinueCount);
      continuation_kernel.gridDim = dim3(1);
      continuation_kernel.blockDim = dim3(1);
      continuation_kernel.kernelParams = continuation_arguments;
      cudaGraphNode_t continuation{};
      Check(cudaGraphAddKernelNode(&continuation, while_body, &switch_node_, 1,
                                   &continuation_kernel),
            "cudaGraphAddKernelNode(continuation)");
      Check(cudaGraphInstantiate(&executable_, graph_, 0),
            "cudaGraphInstantiate");
    } catch (...) {
      if (executable_ != nullptr) cudaGraphExecDestroy(executable_);
      cudaGraphDestroy(graph_);
      graph_ = nullptr;
      executable_ = nullptr;
      throw;
    }
  }

  ConditionalCountSwitchWhileGraph(const ConditionalCountSwitchWhileGraph&) =
      delete;
  ConditionalCountSwitchWhileGraph& operator=(
      const ConditionalCountSwitchWhileGraph&) = delete;

  ~ConditionalCountSwitchWhileGraph() {
    if (executable_ != nullptr) cudaGraphExecDestroy(executable_);
    if (graph_ != nullptr) cudaGraphDestroy(graph_);
  }

  void Launch(uintptr_t stream) {
    Check(cudaGraphLaunch(executable_, reinterpret_cast<cudaStream_t>(stream)),
          "cudaGraphLaunch");
  }

 private:
  cudaGraph_t graph_ = nullptr;
  cudaGraphExec_t executable_ = nullptr;
  cudaGraphNode_t while_node_ = nullptr;
  cudaGraphNode_t setup_switch_node_ = nullptr;
  cudaGraphNode_t switch_node_ = nullptr;
  cudaGraphConditionalHandle while_handle_{};
  cudaGraphConditionalHandle setup_handle_{};
  cudaGraphConditionalHandle switch_handle_{};
  const int64_t* setup_variant_ = nullptr;
  const int64_t* live_count_ = nullptr;
  const int64_t* continuation_count_ = nullptr;
  int setup_count_ = 0;
  int variant_count_ = 0;
  int initial_capacity_ = 1;
};

}  // namespace

PYBIND11_MODULE(_program_cuda, module) {
  py::class_<ConditionalWhileGraph>(module, "ConditionalWhileGraph")
      .def(py::init<uintptr_t, uintptr_t, int, int>(), py::arg("body_graph"),
           py::arg("state"), py::arg("rows"), py::arg("state_width"))
      .def("launch", &ConditionalWhileGraph::Launch, py::arg("stream"));
  py::class_<ConditionalSwitchWhileGraph>(module,
                                          "ConditionalSwitchWhileGraph")
      .def(py::init<uintptr_t, const py::iterable&, uintptr_t, uintptr_t, int,
                    int>(),
           py::arg("setup_graph"), py::arg("variant_graphs"),
           py::arg("state"), py::arg("active_count"), py::arg("rows"),
           py::arg("state_width"))
      .def("launch", &ConditionalSwitchWhileGraph::Launch,
           py::arg("stream"));
  py::class_<ConditionalCountSwitchWhileGraph>(
      module, "ConditionalCountSwitchWhileGraph")
      .def(py::init<const py::iterable&, uintptr_t, const py::iterable&,
                    uintptr_t, uintptr_t, int>(),
           py::arg("setup_graphs"), py::arg("setup_variant"),
           py::arg("variant_graphs"), py::arg("live_count"),
           py::arg("continuation_count"),
           py::arg("initial_capacity"))
      .def("launch", &ConditionalCountSwitchWhileGraph::Launch,
           py::arg("stream"));
}
