# tool used to gen enum2str source code
# needed : pyparsing version >= 3.1.0
# gcc setting : set -save-temps to generate preprocessed files
# usage: 1.compile project; 2.run this script; 3.use generated code(.h + .cpp);

import os
import io
import re
import pyparsing as pp

# DEBUG_MODE = True
DEBUG_MODE = False

# TEST_MODE = True
TEST_MODE = False

# Recommend: for porting convenience, use relative path as SRC_DIR, BUILD_DIR
SRC_DIR = '.'  # project src directory
BUILD_DIR = '.'  # project build directory, which includes all preprocessed files(.ii)
OUTPUT_CPP_FILE = 'enum2str.cpp'  # generated src file
OUTPUT_HEAD_FILE = 'enum2str.h'  # generated header file
TEST_HEAD_FILE = "enum2str_gen_test.h"  # for test purpose

KEYWORD_USING = 'using'
KEYWORD_TYPEDEF = 'typedef'
KEYWORD_NAMESPACE = 'namespace'
KEYWORD_ENUM = 'enum'
KEYWORD_CLASS = 'class'
KEYWORD_STRUCT = 'struct'
KEYWORD_PRIVATE = 'private'
KEYWORD_PUBLIC = 'public'
KEYWORD_PROTECTED = 'protected'
KEYWORD_ATTRIBUTE = '__attribute__'


def abs_path(path):
    return os.path.abspath(path)


def scan_dir(base_dir):
    for root, dirs, files in os.walk(abs_path(base_dir), topdown=True):
        for file in files:
            if file.endswith('.ii'):  # in gcc, preprocessed files end with .ii
                yield os.path.join(root, file)


# remove potential '{' and '}' in string literal
def rm_string_literal(src):
    ret = re.sub("\".*?\"", "\"\"", src)

    if DEBUG_MODE:
        print("\n\nAfter rm_string_literal:\n%s" % ret)
    return ret


#  rm gcc __attribute__ related items
def rm__attribute__(lst):
    ret_lst = []
    skip = 0

    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue
        if ((lst[i] == KEYWORD_ATTRIBUTE and lst[i + 1].startswith('(')) or
                lst[i].startswith(KEYWORD_ATTRIBUTE + '(')):
            ii = i
            lbrace_num = 0
            rbrace_num = 0
            while True:
                lbrace_num += lst[ii].count('(')
                rbrace_num += lst[ii].count(')')
                if lbrace_num == rbrace_num and lbrace_num != 0:  # __attribute__ XXX ends
                    break
                ii += 1
            skip = ii - i
        else:
            ret_lst.append(lst[i])

    if DEBUG_MODE:
        print("\n\nAfter rm__attribute__:\n%s" % " ".join(ret_lst))
    return ret_lst


def will_encounter_semicolon_before_lbrace(lst, start):
    semicolon_index = start
    lbrace_index = start

    while semicolon_index < len(lst) and lst[semicolon_index] != ';':
        semicolon_index += 1
    while lbrace_index < len(lst) and lst[lbrace_index] != '{':
        lbrace_index += 1

    return semicolon_index < lbrace_index


#  when class used in templates  .e.g template <class T> ...
def will_encounter_angle_bracket_before_lbrace(lst, start):
    bracket_index = start
    lbrace_index = start

    while bracket_index < len(lst) and lst[bracket_index] != '>':
        bracket_index += 1
    while lbrace_index < len(lst) and lst[lbrace_index] != '{':
        lbrace_index += 1

    return bracket_index < lbrace_index


def extract_enum_block(lst, start):
    block = ""
    i = start + 1
    while lst[i] != '}':  # save enum block(include '{' not include '}')
        block += lst[i]
        i += 1
    block += '}'  # save '}' here
    return block, i - start


def rm_other_irrelevant(lst):
    ret_str = ""
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue

        if lst[i] == KEYWORD_CLASS or lst[i] == KEYWORD_STRUCT or lst[i] == KEYWORD_NAMESPACE:
            ret_str += lst[i + 1]  # skip keyword only save namespace/class/struct names
            skip = 1
        elif lst[i] == KEYWORD_ENUM:
            block, skip = extract_enum_block(lst, i)
            ret_str += block
        elif lst[i] == '{' or lst[i] == '}':  # save all '{' and '}' for parse purpose
            ret_str += lst[i]
        else:
            pass

    if DEBUG_MODE:
        print("\n\nAfter rm_other_irrelevant:\n%s" % ret_str)
    return ret_str


#  for parse purpose
def add_extra_space(src):
    ret = (
        src.replace(';', ' ; ').replace(':', ' : ').replace(' :  : ', '::').replace('{', ' { ').replace('}', ' } ').
        replace(',', ' , ').replace('=', ' = ').replace('<', ' < ').replace('>', ' > ').
        replace('\t', ' ').replace('\n', ' ').replace('\r', ' '))

    if DEBUG_MODE:
        print("\n\nAfter add_extra_space:\n%s" % ret)
    return ret


#  sink a block's top namespace/class/struct/enum to next layer
def sink_namespace_into_block(lst, start):
    prefix = lst[start]  # namespace/class/struct/enum name
    i = start + 1
    block = '{'  # save first '{' here
    brace_deep = 1
    while brace_deep > 0:  # save this block (from first'{' to last'}' except first '{')
        i += 1
        if lst[i] == '{':
            brace_deep += 1
            block += lst[i]
        elif lst[i] == '}':
            brace_deep -= 1
            block += lst[i]
        elif lst[i] == ',':
            block += lst[i]
        else:  # namespace/class/struct/enum/enum-value name
            if brace_deep == 1:  # only sink into next layer
                block += prefix + '::' + lst[i]
            else:
                block += lst[i]
    return block, i - start


#  sink all namespace like(namespace/class/struct/enum) layer by layer into enum values as prefixes
def sink_namespace(src):
    lst = src.replace('{', ' { ').replace('}', ' } ').replace(',', ' , ').split()
    merged = ""
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue
        if (lst[i] != '{' and lst[i] != '}' and lst[i] != ','
                and i + 1 < len(lst) and lst[i + 1] == '{'):
            block, skip = sink_namespace_into_block(lst, i)
            merged += block
        else:
            merged += lst[i]

    if merged == src:
        if DEBUG_MODE:
            print("\n\nAfter sink_namespace:\n%s" % merged)
        return merged
    else:
        return sink_namespace(merged)


def to_list(src):
    ret = src.split()

    if DEBUG_MODE:
        print("\n\nAfter to_list:\n%s" % ' '.join(ret))
    return ret


def next_lbrace_index(lst, start):
    i = start
    while lst[i] != '{':
        i += 1
    return i


def trim_abnormal_class(lst):
    ret_lst = []
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue

        # typedef anonymous struct
        if lst[i] == KEYWORD_TYPEDEF and lst[i + 1] == KEYWORD_STRUCT and lst[i + 2] == '{':
            size = block_size(lst, i)
            if lst[i + size] != ';':  # anonymous struct with alias
                ret_lst.append(lst[i + 1])
                ret_lst.append(lst[i + size])  # move alias name from tail to head
                for ii in range(i + 2, i + size):
                    ret_lst.append(lst[ii])
                skip = size
        elif lst[i] == KEYWORD_CLASS and lst[i + 1] == '{':  # anonymous class
            ret_lst.append("anonymous_class")
        elif lst[i] == KEYWORD_STRUCT and lst[i + 1] == '{':  # anonymous struct
            ret_lst.append("anonymous_struct")
        else:
            ret_lst.append(lst[i])

    if DEBUG_MODE:
        print("\n\nAfter trim_abnormal_class:\n%s" % " ".join(ret_lst))
    return ret_lst


def trim_abnormal_enum(lst):
    ret_lst = []
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue

        # typedef anonymous enum
        if lst[i] == KEYWORD_TYPEDEF and lst[i + 1] == KEYWORD_ENUM and lst[i + 2] == '{':
            size = block_size(lst, i)
            if lst[i + size] != ';':  # anonymous enum with alias
                ret_lst.append(lst[i + 1])
                ret_lst.append(lst[i + size])  # move alias name from tail to head
                for ii in range(i + 2, i + size):
                    ret_lst.append(lst[ii])
                skip = size
        elif lst[i] == KEYWORD_ENUM and lst[i + 1] == '{':  # anonymous enum
            ret_lst.append("anonymous_enum")
        elif lst[i] == KEYWORD_ENUM and lst[i + 1] == ':':  # anonymous enum with type
            ret_lst.append("anonymous_enum")
        elif (lst[i] == KEYWORD_ENUM and  # enum class/struct with type
              (lst[i + 1] == KEYWORD_CLASS or lst[i + 1] == KEYWORD_STRUCT) and lst[i + 3] == ':'):
            ret_lst.append(lst[i])
            ret_lst.append(lst[i + 2])
            skip = next_lbrace_index(lst, i) - i - 1
        elif (lst[i] == KEYWORD_ENUM and
              (lst[i + 1] == KEYWORD_CLASS or lst[i + 1] == KEYWORD_STRUCT)):  # enum class/struct
            ret_lst.append(lst[i])
            ret_lst.append(lst[i + 2])
            skip = 2
        elif lst[i] == KEYWORD_ENUM and lst[i + 2] == ':':  # enum with type
            ret_lst.append(lst[i])
            ret_lst.append(lst[i + 1])
            skip = next_lbrace_index(lst, i) - i - 1
        else:
            ret_lst.append(lst[i])

    if DEBUG_MODE:
        print("\n\nAfter trim_abnormal_enum:\n%s" % " ".join(ret_lst))
    return ret_lst


# remove forward declaration , typedef struct define or other not class/struct define situation
def rm_not_class_define(lst):
    ret_lst = []
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue

        if (lst[i] == KEYWORD_CLASS and
                (will_encounter_semicolon_before_lbrace(lst, i) or will_encounter_angle_bracket_before_lbrace(lst, i))):
            ret_lst.append("invalid_class")
        elif (lst[i] == KEYWORD_STRUCT and
              (will_encounter_semicolon_before_lbrace(lst, i) or will_encounter_angle_bracket_before_lbrace(lst, i))):
            ret_lst.append("invalid_struct")
        else:
            ret_lst.append(lst[i])

    if DEBUG_MODE:
        print("\n\nAfter rm_not_class_define:\n%s" % " ".join(ret_lst))
    return ret_lst


def rm_using_statement(lst):
    ret_lst = []
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue

        if lst[i] == KEYWORD_USING and lst[i + 1] == KEYWORD_NAMESPACE:
            ret_lst.append("using_namespace")
            skip = 1
        elif lst[i] == KEYWORD_USING and lst[i + 1] == KEYWORD_ENUM:
            ret_lst.append("using_enum")
            skip = 1
        else:
            ret_lst.append(lst[i])

    if DEBUG_MODE:
        print("\n\nAfter rm_using_statement:\n%s" % " ".join(ret_lst))
    return ret_lst


def rm_not_public_part_in_class(lst):
    ret_lst = []
    public_access_stack = []  # is/isn't public access control of each brace layer
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue

        if lst[i] == '{':
            public_access_stack.append(public_access_stack[-1])  # inherit permission of last layer
            ret_lst.append(lst[i])
        elif lst[i] == '}':
            public_access_stack.pop()
            ret_lst.append(lst[i])
        elif lst[i] == KEYWORD_CLASS or lst[i] == KEYWORD_STRUCT:
            public_access_stack.append(True if lst[i] == KEYWORD_STRUCT else False)
            ret_lst.append(lst[i])
            ret_lst.append(lst[i + 1])
            ret_lst.append(lst[i + 2])
            skip = 2  # skip class/struct name and '{'
        elif lst[i] == KEYWORD_PRIVATE or lst[i] == KEYWORD_PROTECTED or lst[i] == KEYWORD_PUBLIC:
            public_access_stack[-1] = True if lst[i] == KEYWORD_PUBLIC else False
            skip = 1  # skip ':'
        else:
            if False not in public_access_stack:
                ret_lst.append(lst[i])
    return ret_lst


def rm_class_inheritance(lst):
    ret_lst = lst[:2]  # insert class/struct keyword and name
    for i in range(len(lst)):
        if lst[i] == '{':
            ret_lst.extend(lst[i:])
            break
    return ret_lst


def block_size(lst, start):
    end = start
    while lst[end] != '{':
        end += 1
    brace_deep = 1
    while brace_deep > 0:
        end += 1
        if lst[end] == '{':
            brace_deep += 1
        elif lst[end] == '}':
            brace_deep -= 1
    return end - start + 1


def rm_irrelevant_in_class(lst):
    ret_lst = []
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue
        if lst[i] == KEYWORD_ENUM and lst[i + 1] == KEYWORD_CLASS:  # enum class is not class
            ret_lst.append(lst[i])
            ret_lst.append(lst[i + 1])
            skip = 1
        elif lst[i] == KEYWORD_CLASS or lst[i] == KEYWORD_STRUCT:
            class_size = block_size(lst, i)
            ret_lst.extend(rm_not_public_part_in_class(rm_class_inheritance(lst[i:i + class_size])))
            skip = class_size
        else:
            ret_lst.append(lst[i])

    if DEBUG_MODE:
        print("\n\nAfter rm_irrelevant_in_class:\n%s" % " ".join(ret_lst))
    return ret_lst


def project_contains(path):
    if TEST_MODE:
        if path.endswith(TEST_HEAD_FILE):
            return True
        else:
            return False
    else:
        if path.startswith(abs_path(SRC_DIR)) and not path.endswith(TEST_HEAD_FILE):
            return True
        else:
            return False


def print_dict(d):
    for k in d:
        print('\n')
        print(k)
        print(" ".join(d[k].split()))


processed_header_list = [""]


def extract_header_contents(src):
    global processed_header_list
    header_content_dict = {}  # header abs path as key, header content as value
    header_key = ""
    ignore_below_lines = True
    for line in src.splitlines():
        item_list = line.split()
        if len(item_list) >= 3 and item_list[0] == '#' and item_list[1].isnumeric() and item_list[2].startswith('"'):
            potential_header_path = item_list[2][1:-1]
            if potential_header_path.endswith('.h'):
                header = abs_path(potential_header_path)
                if project_contains(header) and header not in processed_header_list:
                    ignore_below_lines = False
                    header_key = header
                else:
                    ignore_below_lines = True
            else:
                ignore_below_lines = True
        else:
            if not ignore_below_lines:
                if header_content_dict.get(header_key) is None:
                    header_content_dict[header_key] = line
                else:
                    header_content_dict[header_key] = header_content_dict[header_key] + ' ' + line

    processed_header_list.extend(header_content_dict.keys())
    processed_header_list = list(set(processed_header_list))
    return header_content_dict


def process(src):
    return sink_namespace(
        rm_other_irrelevant(
            rm_irrelevant_in_class(
                trim_abnormal_enum(
                    trim_abnormal_class(
                        rm_not_class_define(
                            rm_using_statement(
                                rm__attribute__(
                                    to_list(
                                        add_extra_space(
                                            rm_string_literal(src)))))))))))


# main starts
if os.path.exists(OUTPUT_CPP_FILE):
    os.remove(OUTPUT_CPP_FILE)
if os.path.exists(OUTPUT_HEAD_FILE):
    os.remove(OUTPUT_HEAD_FILE)

output_cpp_file = open(OUTPUT_CPP_FILE, 'a')
output_head_file = open(OUTPUT_HEAD_FILE, 'a')

output_head_file.write("// auto generated by enum2str_gen.py, modify it if needed\n"
                       "#ifndef ENUM_2_STR_H__\n"
                       "#define ENUM_2_STR_H__\n\n"
                       "#define ENUM2STR(...) enum2str(__VA_ARGS__).data()\n\n"
                       "#include <string>\n")

output_cpp_file.write("// auto generated by enum2str_gen.py, modify it if needed\n"
                      "#include \"enum2str.h\"\n"
                      "#include <string>\n\n")

INT = pp.Word(pp.nums + "-")
LBRACE, RBRACE, EQ, COMMA = pp.Suppress.using_each("{}=,")
ENUM_VALUE = pp.Word(pp.alphas + "_", pp.alphanums + "_" + "::")
ENUM_VALUE_COMBO = pp.Group(ENUM_VALUE("value") + pp.Optional(EQ + INT))
ENUM_VALUE_COMBO_LIST = pp.Group(ENUM_VALUE_COMBO + (COMMA + ENUM_VALUE_COMBO)[...] + pp.Optional(COMMA))
ENUM_BLOCK = LBRACE + ENUM_VALUE_COMBO_LIST("value_list") + RBRACE

cpp_cache = io.StringIO()
head_cache = io.StringIO()

for ii_file_path in scan_dir(BUILD_DIR):
    print("scanning %s" % ii_file_path)

    header_content_dict = extract_header_contents(open(ii_file_path, 'r').read())
    for header_path in header_content_dict:
        header_content = header_content_dict[header_path]
        header_name = header_path.split('/')[-1]
        header_included = False
        for enum, start, stop in ENUM_BLOCK.scan_string(process(header_content)):
            if not header_included:
                header_included = True
                output_head_file.write("#include \"%s\"\n" % header_name)

            func_head_inserted = False
            for item in enum.value_list:
                if not func_head_inserted:
                    func_head_inserted = True
                    head_cache.write("std::string enum2str(%s e);\n" % '::'.join(item.value.split('::')[0:-1]))
                    cpp_cache.write("std::string enum2str(%s e) {\n" % '::'.join(item.value.split('::')[0:-1]))
                    cpp_cache.write("  switch (e) {\n")

                cpp_cache.write("    case %s: return \"%s\";\n" % (item.value, item.value.split('::')[-1]))
            cpp_cache.write("    default: return \"\";\n  }\n}\n\n")

output_cpp_file.write(cpp_cache.getvalue())
output_head_file.write("\n")
output_head_file.write(head_cache.getvalue())
output_head_file.write("\n#endif  // ENUM_2_STR_H__\n")
