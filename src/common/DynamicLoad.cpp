#include "common/DynamicLoad.hpp"

#if defined(WIN32)
  #include <windows.h>
  #define DynamicLoadLibrary(lib) \
    (void*)LoadLibraryEx(lib, NULL, LOAD_LIBRARY_SEARCH_DEFAULT_DIRS)
  #define DynamicLoadFunction(handle,fn) (void*)GetProcAddress((HMODULE)handle,fn)
#else
  #include <dlfcn.h>
  #define DynamicLoadLibrary(lib) dlopen(lib, RTLD_LAZY)
  #define DynamicLoadFunction(handle,fn) (void*)dlsym(handle,fn)
#endif

namespace ale {

bool DynamicLinkFunction(void** fn, const char* source, const char* library) {
  // Function already linked
  if (*fn != nullptr) {
    return true;
  }

  // Try loading library
  if (library != nullptr) {
    // We can repetitvely call dlopen, it gets refcounted
    // and will return the sample handle once the library is mmaped
    void* handle = DynamicLoadLibrary(library);
    if (handle != nullptr) {
      // Dynamically link function
      *fn = DynamicLoadFunction(handle, source);
      if (*fn != nullptr) {
        return true;
      }
    }
  }

  *fn = nullptr;
  return false;
}

} // namespace ale
