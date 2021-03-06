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

FROM gcr.io/oss-fuzz-base/base-clang
MAINTAINER mike.aizatsky@gmail.com
RUN apt-get install -y git subversion jq python3 zip make gawk python3-pip vim && \
    pip3 install --upgrade pip && \
    pip3 install networkx && \
    pip3 install pydotplus && \
    ln -s $(which python3) /usr/bin/python 

# Default build flags for various sanitizers.
ENV SANITIZER_FLAGS_address "-fsanitize=address -fsanitize-address-use-after-scope"
ENV SANITIZER_FLAGS_undefined "-fsanitize=bool,function,signed-integer-overflow,shift,vla-bound,vptr -fno-sanitize-recover=undefined"
ENV SANITIZER_FLAGS_memory "-fsanitize=memory -fsanitize-memory-track-origins"

# Default build flags for coverage.
ENV COVERAGE_FLAGS="-fsanitize-coverage=trace-pc-guard,trace-cmp"

# Workaround ASAN false positive: https://github.com/google/sanitizers/issues/647
ENV ASAN_OPTIONS="detect_odr_violation=0"

# Default sanitizer and fuzzing engine to use.
ENV SANITIZER="address"
ENV FUZZING_ENGINE="aflgo"

# Path to fuzzing engine library.
ENV LIB_FUZZING_ENGINE="/usr/lib/libFuzzingEngine.a"

# TODO: remove after tpm2 catchup.
ENV FUZZER_LDFLAGS ""

WORKDIR $SRC

ADD http://lcamtuf.coredump.cx/afl/releases/afl-latest.tgz $SRC/
RUN mkdir afl && \
    cd afl && \
    tar -xzv --strip-components=1 -f $SRC/afl-latest.tgz && \
    rm -rf $SRC/afl-latest.tgz

ADD https://raw.githubusercontent.com/jay/showlinenum/develop/showlinenum.awk $SRC/

COPY compile compile_afl compile_aflgo compile_libfuzzer coverage_report srcmap /usr/local/bin/
COPY afl.patch $SRC/

CMD ["compile"]

