#!/usr/bin/env bash
# Fetch and build the two fuzzing proxies with sanitizer coverage.
#
# SiliFuzz fuzzes software proxies with libFuzzer (paper section 2.4).  The
# prebuilt Python wheels ship usable libraries but without coverage
# instrumentation, so the libraries are built here from pinned sources.
set -euo pipefail
cd "$(dirname "$0")/.."

CAPSTONE_TAG=${CAPSTONE_TAG:-5.0.7}
UNICORN_TAG=${UNICORN_TAG:-2.1.4}
CLANG=${CLANG:-clang}
CLANGXX=${CLANGXX:-clang++}
JOBS=${JOBS:-$(nproc)}

mkdir -p third_party

clone() {
  local url=$1 tag=$2 dir=$3
  if [ -d "$dir/.git" ]; then
    return
  fi
  echo "cloning $url @ $tag"
  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null \
    git clone --depth 1 --branch "$tag" "$url" "$dir"
}

clone https://github.com/capstone-engine/capstone.git "$CAPSTONE_TAG" third_party/capstone
clone https://github.com/unicorn-engine/unicorn.git "$UNICORN_TAG" third_party/unicorn

if [ ! -f third_party/capstone-build/libcapstone.a ]; then
  cmake -S third_party/capstone -B third_party/capstone-build -G Ninja \
    -DCMAKE_C_COMPILER="$CLANG" -DCMAKE_CXX_COMPILER="$CLANGXX" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCAPSTONE_BUILD_SHARED=OFF -DCAPSTONE_BUILD_STATIC=ON \
    -DCAPSTONE_BUILD_TESTS=OFF -DCAPSTONE_ARCHITECTURE_DEFAULT=OFF \
    -DCAPSTONE_ARM64_SUPPORT=ON \
    -DCMAKE_C_FLAGS="-O1 -g -fsanitize=fuzzer-no-link"
  ninja -C third_party/capstone-build -j"$JOBS"
fi

if [ ! -f third_party/unicorn-build/libunicorn.a ]; then
  cmake -S third_party/unicorn -B third_party/unicorn-build -G Ninja \
    -DCMAKE_C_COMPILER="$CLANG" -DCMAKE_CXX_COMPILER="$CLANGXX" \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
    -DUNICORN_ARCH=aarch64 -DUNICORN_BUILD_TESTS=OFF -DUNICORN_INSTALL=OFF \
    -DCMAKE_C_FLAGS="-O1 -g -fsanitize=fuzzer-no-link"
  ninja -C third_party/unicorn-build -j"$JOBS"
fi

echo "deps: third_party/capstone-build/libcapstone.a third_party/unicorn-build/libunicorn.a"
