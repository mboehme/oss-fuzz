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

FROM gcr.io/oss-fuzz-base/base-builder
MAINTAINER ochang@chromium.org
RUN apt-get install -y make autoconf automake libtool pkg-config

RUN git clone --depth 1 git://git.gnome.org/libxml2
WORKDIR libxml2

COPY patch.diff $SRC/
COPY build.sh $SRC/
COPY libxml2_xml_read_memory_fuzzer.* \
     libxml2_xml_regexp_compile_fuzzer.* \
     xml.dict $SRC/
