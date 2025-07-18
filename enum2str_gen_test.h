#ifndef ENUM2STR_GEN_TEST_H
#define ENUM2STR_GEN_TEST_H

#include <string>
#include <chrono>

enum ForwardDeclarationEnum: int;
class ForwardDeclarationClass;
struct ForwardDeclarationStruct;

template <class T> T max(T x, T y) {
  return (x > y) ? x : y;
}

typedef struct {
  enum EnumAnonyTypeDefStructWithAlias {EnumAnonyTypeDefStructWithAliasValue_1,EnumAnonyTypeDefStructWithAliasValue_2,};
}AnonyTypeDefStructWithAliasAlias;

typedef struct TypeDefStruct{
  enum EnumInTypeDefStruct {EnumInTypeDefStructValue_1,EnumInTypeDefStructValue_2,};
};

typedef struct TypeDefStructWithAlias{
  enum EnumInTypeDefStructWithAlias {EnumInTypeDefStructWithAliasAliasValue_1,EnumInTypeDefStructWithAliasAliasValue_2,};
}TypeDefStructWithAliasAlias;

typedef enum {AnonyTypeDefEnumValue_1,AnonyTypeDefEnumValue_2};
typedef enum {AnonyTypeDefEnumWithAliasValue_1,AnonyTypeDefEnumWithAliasValue_2}AnonyTypeDefEnumWithAliasAlias;
typedef enum TypeDefEnum{TypeDefEnumValue_1,TypeDefEnumValue_2};
typedef enum TypeDefEnumWithAlias{TypeDefEnumWithAliasValue_1,TypeDefEnumWithAliasValue_2}TypeDefEnumWithAliasAlias;

enum EnumEmpty {};
// using enum EnumEmpty;  //c++ 20

using namespace std;
using namespace std:: chrono;
using namespace std ::chrono;
using namespace std :: chrono;

class Class_1 : public std::string { // test comments {{
  enum{AnonyEnumValue_1,AnonyEnumValue_2};

 protected:
   enum :int{AnonyEnumIntValue_1=-1, AnonyEnumIntValue_2 =2,};

 private:
   enum : unsigned int {AnonyEnumUintValue_1= 1,AnonyEnumUintValue_2, AnonyEnumUintValue_3 = 3};

  public:
   class {}anony_class;
   struct {}anony_struct;
   enum Enum{EnumValue_1,EnumValue_2};

   enum Enum function_delaration_with_enum_ret();
   enum Enum function_definition_with_enum_ret() {return EnumValue_1;}
   
   void function_delaration_with_enum_arg(enum Enum e);
   void function_definition_with_enum_arg(enum Enum e) {}

   struct Struct_1{
     enum EnumInt :int{EnumIntValue_1=-1, EnumIntValue_2 =2,};  // test comments {{

    private:
     enum EnumUint : unsigned int {EnumUintValue_1= 1,EnumUintValue_2, EnumUintValue_3 = 3};

    public:
     enum class EnumClass{EnumClassValue_1,EnumClassValue_2};
   };
};
namespace Name_2 {
enum class EnumClassInt :int{EnumClassIntValue_1=-1,EnumClassIntValue_2 =2,};
namespace Name_3 {
enum class EnumClassUint : unsigned int{EnumClassUintValue_1=1,EnumClassUintValue_2, EnumClassUintValue_3 = 3};
}
}

class Class_1 function_delaration_with_ret_class_keyword();
inline class Class_1 function_definition_with_ret_class_keyword() {return Class_1{};}

void function_delaration_with_arg_class_keyword(class Class_1 c);
inline void function_definition_with_arg_class_keyword(class Class_1 c) {}

enum struct EnumStruct{EnumStructValue_1,EnumStructValue_2};
enum struct EnumStructInt :int{EnumStructIntValue_1=-1,EnumStructIntValue_2 =2,};
enum struct EnumStructUint : unsigned int{
  EnumStructUintValue_1 __attribute__((__deprecated__))= 0x0001,
  EnumStructUintValue_2 __attribute__ ( ( __deprecated__))= 1 << 1, /* test comments {{ */
  EnumStructUintValue_3 __attribute__ ((__deprecated__ ) )= 1 + 2,
  EnumStructUintValue_4 __attribute__(( __deprecated__ )) = 0XFFFF};
/* test comments {{
   * {{
   */
#endif //ENUM2STR_GEN_TEST_H






