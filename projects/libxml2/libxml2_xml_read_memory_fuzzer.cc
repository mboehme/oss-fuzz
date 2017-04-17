// Copyright 2015 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include <cassert>
#include <cstddef>
#include <cstdint>

#include <functional>
#include <limits>
#include <string>

#include "libxml/parser.h"
#include "libxml/xmlsave.h"

void ignore (void* ctx, const char* msg, ...) {
  // Error handler to avoid spam of error messages from libxml parser.
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
  xmlSetGenericErrorFunc(NULL, &ignore);
  int random_option_value = 0;
  if (size > 4) {
    random_option_value = (int) *(uint32_t *) data;
    if (random_option_value < 0) random_option_value *= -1;
//    random_option_value &= ~XML_PARSE_RECOVER;
  }

  if (random_option_value & XML_PARSE_RECOVER) fprintf(stderr, "XML_PARSE_RECOVER ");
if (random_option_value & XML_PARSE_NOENT) fprintf(stderr, "XML_PARSE_NOENT ");
if (random_option_value & XML_PARSE_DTDLOAD) fprintf(stderr, "XML_PARSE_DTDLOAD ");
if (random_option_value & XML_PARSE_DTDATTR) fprintf(stderr, "XML_PARSE_DTDATTR ");
if (random_option_value & XML_PARSE_DTDVALID) fprintf(stderr, "XML_PARSE_DTDVALID ");
if (random_option_value & XML_PARSE_NOERROR) fprintf(stderr, "XML_PARSE_NOERROR ");
if (random_option_value & XML_PARSE_NOWARNING) fprintf(stderr, "XML_PARSE_NOWARNING ");
if (random_option_value & XML_PARSE_PEDANTIC) fprintf(stderr, "XML_PARSE_PEDANTIC ");
if (random_option_value & XML_PARSE_NOBLANKS) fprintf(stderr, "XML_PARSE_NOBLANKS ");
if (random_option_value & XML_PARSE_SAX1) fprintf(stderr, "XML_PARSE_SAX1 ");
if (random_option_value & XML_PARSE_XINCLUDE) fprintf(stderr, "XML_PARSE_XINCLUDE ");
if (random_option_value & XML_PARSE_NONET) fprintf(stderr, "XML_PARSE_NONET ");
if (random_option_value & XML_PARSE_NODICT) fprintf(stderr, "XML_PARSE_NODICT ");
if (random_option_value & XML_PARSE_NSCLEAN) fprintf(stderr, "XML_PARSE_NSCLEAN ");
if (random_option_value & XML_PARSE_NOCDATA) fprintf(stderr, "XML_PARSE_NOCDATA ");
if (random_option_value & XML_PARSE_NOXINCNODE) fprintf(stderr, "XML_PARSE_NOXINCNODE ");
if (random_option_value & XML_PARSE_COMPACT) fprintf(stderr, "XML_PARSE_COMPACT ");
  if (random_option_value & XML_PARSE_OLD10) fprintf(stderr, "XML_PARSE_OLD10 ");
  if (random_option_value & XML_PARSE_NOBASEFIX) fprintf(stderr, "XML_PARSE_NOBASEFIX ");
  if (random_option_value & XML_PARSE_HUGE) fprintf(stderr, "XML_PARSE_HUGE ");
  if (random_option_value & XML_PARSE_OLDSAX) fprintf(stderr, "XML_PARSE_OLDSAX");
  if (random_option_value & XML_PARSE_IGNORE_ENC) fprintf(stderr, "XML_PARSE_IGNORE_ENC ");
  if (random_option_value & XML_PARSE_BIG_LINES) fprintf(stderr, "XML_PARSE_BIG_LINES ");
  if (random_option_value & XML_PARSE_NOXXE) fprintf(stderr, "XML_PARSE_NOXXE ");

  // Test default empty options value and some random combination.
  std::string data_string(reinterpret_cast<const char*>(data + (size > 4 ? 4 : 0)), size - (size > 4 ? 4 : 0));
  int options[] = {0, XML_PARSE_COMPACT | XML_PARSE_BIG_LINES, random_option_value};

  for (const auto option_value : options) {
    if (auto doc = xmlReadMemory(data_string.c_str(), data_string.length(),
                                 "noname.xml", NULL, option_value)) {
      auto buf = xmlBufferCreate();
      assert(buf);
      auto ctxt = xmlSaveToBuffer(buf, NULL, 0);
      xmlSaveDoc(ctxt, doc);
      xmlSaveClose(ctxt);
      xmlFreeDoc(doc);
      xmlBufferFree(buf);
    }
  }

  return 0;
}
