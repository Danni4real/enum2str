// auto generated by enum2str_gen.py, modify it if needed
#include <string>
#include "./example/a.h"
std::string enum2str(A e) {
  switch ((int)e) {
    case A_1: return "A_1";
    case A_2: return "A_2";
    case A_3: return "A_3";
    default: return std::to_string(e);
  }
}
#include "./example/b.h"
std::string enum2str(B e) {
  switch ((int)e) {
    case B_1: return "B_1";
    case B_2: return "B_2";
    case B_3: return "B_3";
    default: return std::to_string(e);
  }
}
#include "./example/e/ee.h"
std::string enum2str(EE e) {
  switch ((int)e) {
    case EE_1: return "EE_1";
    case EE_2: return "EE_2";
    case EE_3: return "EE_3";
    default: return std::to_string(e);
  }
}