#!/bin/bash

f=$1
header=$SRC/libjpeg-turbo/turbojpeg.h

if ! [ -f $header ]; then
  exit 1
fi

echo "
/*
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
*/

#include <stdint.h>
#include <stdlib.h>

#include <memory>

#include <turbojpeg.h>


extern \"C\" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    tjhandle jpegDecompressor = tjInitDecompress();

    int width, height, subsamp, colorspace;
" > $f

if grep "tjDecompressHeader3" $header >/dev/null; then
  echo "    int res = tjDecompressHeader3(
        jpegDecompressor, data, size, &width, &height, &subsamp, &colorspace);" >> $f
elif grep "tjDecompressHeader2" $header >/dev/null; then
  echo "    int res = tjDecompressHeader2(
        jpegDecompressor, (unsigned char*) data, size, &width, &height, &subsamp);" >> $f
else
  echo "    int res = tjDecompressHeader(
        jpegDecompressor, (unsigned char*) data, size, &width, &height);" >> $f
fi

echo "    // Bail out if decompressing the headers failed, the width or height is 0,
    // or the image is too large (avoids slowing down too much). Cast to size_t to
    // avoid overflows on the multiplication
    if (res != 0 || width == 0 || height == 0 || ((size_t)width * height > (1024 * 1024))) {
        tjDestroy(jpegDecompressor);
        return 0;
    }

    std::unique_ptr<unsigned char[]> buf(new unsigned char[width * height * 3]);" >> $f
if grep "tjDecompress2" $header >/dev/null; then
  echo "    tjDecompress2(
        jpegDecompressor, (unsigned char*) data, size, buf.get(), width, 0, height, TJPF_RGB, 0);" >> $f
else
  echo "    tjDecompress2(
        jpegDecompressor, (unsigned char*) data, size, buf.get(), width, 0, height, TJPF_RGB, 0);" >> $f
fi
echo "    tjDestroy(jpegDecompressor);

    return 0;
}" >> $f 
