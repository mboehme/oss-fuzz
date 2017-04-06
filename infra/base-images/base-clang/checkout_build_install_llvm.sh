#!/bin/bash -eux
# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

LLVM_DEP_PACKAGES="build-essential make cmake ninja-build git python2.7 binutils-gold binutils-dev"
apt-get install -y $LLVM_DEP_PACKAGES

# Checkout
cd $SRC && git clone --depth 1 http://llvm.org/git/llvm.git
cd $SRC/llvm/tools && git clone --depth 1 http://llvm.org/git/clang.git
cd $SRC/llvm/projects && git clone --depth 1 http://llvm.org/git/compiler-rt.git
cd $SRC/llvm/projects && git clone --depth 1 http://llvm.org/git/libcxx.git
cd $SRC/llvm/projects && git clone --depth 1 http://llvm.org/git/libcxxabi.git

# Build & install
mkdir -p $WORK/llvm
cd $WORK/llvm
cmake -G "Ninja" \
      -DLIBCXX_ENABLE_SHARED=OFF -DLIBCXX_ENABLE_STATIC_ABI_LIBRARY=ON \
      -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="X86" \
      -DLLVM_BINUTILS_INCDIR=/usr/include $SRC/llvm
ninja
ninja install
rm -rf $WORK/llvm

mkdir -p $WORK/msan
cd $WORK/msan
cmake -G "Ninja" \
      -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
      -DLLVM_USE_SANITIZER=Memory -DCMAKE_INSTALL_PREFIX=/usr/msan/ \
      -DLIBCXX_ENABLE_SHARED=OFF -DLIBCXX_ENABLE_STATIC_ABI_LIBRARY=ON \
      -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="X86" \
      $SRC/llvm
ninja cxx
ninja install-cxx
rm -rf $WORK/msan

# Copy libfuzzer sources
mkdir $SRC/libfuzzer
cp -r $SRC/llvm/lib/Fuzzer/* $SRC/libfuzzer/

cp $SRC/llvm/tools/sancov/coverage-report-server.py /usr/local/bin/

# Install LLVMgold into bfd-plugins
mkdir /usr/lib/bfd-plugins
cp /usr/local/lib/libLTO.so /usr/lib/bfd-plugins
cp /usr/local/lib/LLVMgold.so /usr/lib/bfd-plugins

# Cleanup
rm -rf $SRC/llvm
apt-get remove --purge -y $LLVM_DEP_PACKAGES
apt-get autoremove -y
