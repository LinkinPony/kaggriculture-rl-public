// Exact IEEE binary16 packing with portable runtime dispatch.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>

#if defined(__x86_64__) && defined(__GNUC__)
#include <immintrin.h>
#endif

namespace kagg::half {

template <typename Input>
inline void Scalar(const Input* input, size_t count, uint16_t* output) {
  auto* values = reinterpret_cast<_Float16*>(output);
  for (size_t i = 0; i < count; ++i) values[i] = static_cast<_Float16>(input[i]);
}

#if defined(__x86_64__) && defined(__GNUC__)
__attribute__((target("avx,f16c")))
inline void VectorFloat(const float* input, size_t count, uint16_t* output) {
  size_t i = 0;
  for (; i + 8 <= count; i += 8) {
    const auto packed = _mm256_cvtps_ph(_mm256_loadu_ps(input + i), _MM_FROUND_TO_NEAREST_INT);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(output + i), packed);
  }
  Scalar(input + i, count - i, output + i);
}

__attribute__((target("avx512fp16")))
inline void VectorDouble(const double* input, size_t count, uint16_t* output) {
  size_t i = 0;
  for (; i + 8 <= count; i += 8) {
    // Direct double -> half avoids the double rounding of double -> float -> half.
    const auto packed = _mm512_cvt_roundpd_ph(_mm512_loadu_pd(input + i),
        _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
    std::memcpy(output + i, &packed, sizeof(packed));
  }
  Scalar(input + i, count - i, output + i);
}
#endif

inline void Pack(const float* input, size_t count, uint16_t* output) {
#if defined(__x86_64__) && defined(__GNUC__)
  static const auto convert = __builtin_cpu_supports("f16c") ? VectorFloat : Scalar<float>;
  convert(input, count, output);
#else
  Scalar(input, count, output);
#endif
}

inline void Pack(const double* input, size_t count, uint16_t* output) {
#if defined(__x86_64__) && defined(__GNUC__)
  static const auto convert = __builtin_cpu_supports("avx512fp16") ? VectorDouble : Scalar<double>;
  convert(input, count, output);
#else
  Scalar(input, count, output);
#endif
}

}  // namespace kagg::half
