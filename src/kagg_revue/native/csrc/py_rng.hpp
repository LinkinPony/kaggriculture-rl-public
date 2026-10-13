// CPython-compatible Mersenne Twister (`random.Random`).
//
// Reproduces bit-exactly the subset of CPython's `_random.Random` the
// official farming engine consumes: integer seeding via init_by_array over the
// seed's 32-bit little-endian limbs, `random()` (genrand_res53),
// `getrandbits(k)` for k <= 32, and `_randbelow(n)` (the getrandbits
// rejection loop used by `choice`).
#pragma once

#include <cstddef>
#include <cstdint>

namespace kagg {

using uint128 = unsigned __int128;

class PyRandom {
 public:
  // Equivalent to `random.Random(seed)` for a non-negative integer seed.
  explicit PyRandom(uint128 seed) { SeedInt(seed); }

  // `random.random()`: 53-bit uniform double in [0, 1).
  double Random() {
    const uint32_t a = NextUint32() >> 5;
    const uint32_t b = NextUint32() >> 6;
    return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
  }

  // `random.getrandbits(k)` for 0 < k <= 32.
  uint32_t GetRandBits(int k) { return NextUint32() >> (32 - k); }

  // `random._randbelow(n)` for n >= 1 (the getrandbits path used by choice()).
  uint32_t RandBelow(uint32_t n) {
    if (n == 0) return 0;
    int k = 0;
    for (uint32_t v = n; v != 0; v >>= 1) ++k;
    uint32_t r = GetRandBits(k);
    while (r >= n) r = GetRandBits(k);
    return r;
  }

 private:
  static constexpr int kN = 624;
  static constexpr int kM = 397;
  static constexpr uint32_t kMatrixA = 0x9908b0dfU;
  static constexpr uint32_t kUpperMask = 0x80000000U;
  static constexpr uint32_t kLowerMask = 0x7fffffffU;

  void InitGenrand(uint32_t s) {
    mt_[0] = s;
    for (mti_ = 1; mti_ < kN; ++mti_) {
      mt_[mti_] =
          1812433253U * (mt_[mti_ - 1] ^ (mt_[mti_ - 1] >> 30)) + static_cast<uint32_t>(mti_);
    }
  }

  void InitByArray(const uint32_t* init_key, size_t key_length) {
    InitGenrand(19650218U);
    size_t i = 1;
    size_t j = 0;
    size_t k = (static_cast<size_t>(kN) > key_length) ? static_cast<size_t>(kN) : key_length;
    for (; k; --k) {
      mt_[i] = (mt_[i] ^ ((mt_[i - 1] ^ (mt_[i - 1] >> 30)) * 1664525U)) + init_key[j] +
               static_cast<uint32_t>(j);
      ++i;
      ++j;
      if (i >= static_cast<size_t>(kN)) {
        mt_[0] = mt_[kN - 1];
        i = 1;
      }
      if (j >= key_length) j = 0;
    }
    for (k = kN - 1; k; --k) {
      mt_[i] = (mt_[i] ^ ((mt_[i - 1] ^ (mt_[i - 1] >> 30)) * 1566083941U)) -
               static_cast<uint32_t>(i);
      ++i;
      if (i >= static_cast<size_t>(kN)) {
        mt_[0] = mt_[kN - 1];
        i = 1;
      }
    }
    mt_[0] = 0x80000000U;
  }

  // CPython random_seed(): split |n| into 32-bit chunks from the right and
  // feed them to init_by_array (n == 0 uses the single chunk [0]).
  void SeedInt(uint128 n) {
    uint32_t key[4] = {0, 0, 0, 0};
    size_t used = 0;
    if (n == 0) {
      used = 1;
    } else {
      while (n != 0) {
        key[used++] = static_cast<uint32_t>(n & 0xffffffffU);
        n >>= 32;
      }
    }
    InitByArray(key, used);
  }

  uint32_t NextUint32() {
    uint32_t y;
    if (mti_ >= kN) {
      int kk;
      for (kk = 0; kk < kN - kM; ++kk) {
        y = (mt_[kk] & kUpperMask) | (mt_[kk + 1] & kLowerMask);
        mt_[kk] = mt_[kk + kM] ^ (y >> 1) ^ ((y & 0x1U) ? kMatrixA : 0U);
      }
      for (; kk < kN - 1; ++kk) {
        y = (mt_[kk] & kUpperMask) | (mt_[kk + 1] & kLowerMask);
        mt_[kk] = mt_[kk + (kM - kN)] ^ (y >> 1) ^ ((y & 0x1U) ? kMatrixA : 0U);
      }
      y = (mt_[kN - 1] & kUpperMask) | (mt_[0] & kLowerMask);
      mt_[kN - 1] = mt_[kM - 1] ^ (y >> 1) ^ ((y & 0x1U) ? kMatrixA : 0U);
      mti_ = 0;
    }
    y = mt_[mti_++];
    y ^= (y >> 11);
    y ^= (y << 7) & 0x9d2c5680U;
    y ^= (y << 15) & 0xefc60000U;
    y ^= (y >> 18);
    return y;
  }

  uint32_t mt_[kN];
  int mti_ = kN + 1;
};

}  // namespace kagg
