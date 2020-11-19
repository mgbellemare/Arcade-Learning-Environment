#ifndef DYNAMIC_LOAD_HPP
#define DYNAMIC_LOAD_HPP

namespace ale {

bool DynamicLinkFunction(void** fn, const char* source, const char* library);

} // namespace ale
#endif // DYNAMIC_LOAD_HPP
