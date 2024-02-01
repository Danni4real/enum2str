# tool used to gen enum2str source code
# needed : pyparsing version >= 3.1.0

import os
import io
import re
import pyparsing as pp

SRC_DIR = '../'
EXCLUDE_DIRS = {'tests', 'gal'}
EXCLUDE_FILES = {'AutoLog.h'}
OUTPUT_CPP_FILE = 'enum2str.cpp'
OUTPUT_HEAD_FILE = 'enum2str.h'

KEYWORD_USING = 'using'
KEYWORD_TYPEDEF = 'typedef'
KEYWORD_NAMESPACE = 'namespace'
KEYWORD_ENUM = 'enum'
KEYWORD_CLASS = 'class'
KEYWORD_STRUCT = 'struct'
KEYWORD_PRIVATE = 'private'
KEYWORD_PUBLIC = 'public'
KEYWORD_PROTECTED = 'protected'


def scan_dir(base_dir):
    for root, dirs, files in os.walk(base_dir, topdown=True):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith('.h') and file not in EXCLUDE_FILES:
                yield os.path.join(root, file)  # relative path of file


def rm_comments(src):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " "  # note: a space and not an empty string
        else:
            return s

    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, src)


# remove potential '{' and '}' in string literal
def rm_string_literal(src):
    return re.sub("\".*?\"", "\"\"", src)


def rm_macro(src):
    return re.sub("#elif .*?#endif", "#endif", re.sub("#else .*?#endif", "#endif", src))


def rm_all_spaces(src):
    return src.replace(' ', '')


def will_encounter_semicolon_before_lbrace(lst, start):
    semicolon_index = start
    lbrace_index = start

    while semicolon_index < len(lst) and lst[semicolon_index] != ';':
        semicolon_index += 1
    while lbrace_index < len(lst) and lst[lbrace_index] != '{':
        lbrace_index += 1

    return semicolon_index < lbrace_index


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
    return ret_str


#  for parse purpose
def add_extra_space(text):
    return (
        text.replace(';', ' ; ').replace(':', ' : ').replace(' :  : ', '::').replace('{', ' { ').replace('}', ' } ').
        replace('\t', ' ').replace('\n', ' ').replace('\r', ' '))


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
        return merged
    else:
        return sink_namespace(merged)


def to_list(text):
    return text.split()


def trim_abnormal_enum(lst):
    ret_lst = []
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue

        if lst[i] == KEYWORD_ENUM and lst[i + 1] == '{':  # anonymous enum
            ret_lst.append("anonymous_enum")
        elif lst[i] == KEYWORD_ENUM and lst[i + 1] == ':':  # anonymous enum with type
            ret_lst.append("anonymous_enum")
            skip = 2
        elif lst[i] == KEYWORD_ENUM and lst[i + 1] == KEYWORD_CLASS and lst[i + 3] == ':':  # enum class with type
            ret_lst.append(lst[i])
            ret_lst.append(lst[i + 2])
            skip = 4
        elif lst[i] == KEYWORD_ENUM and lst[i + 1] == KEYWORD_CLASS:  # enum class
            ret_lst.append(lst[i])
            ret_lst.append(lst[i + 2])
            skip = 2
        elif lst[i] == KEYWORD_ENUM and lst[i + 2] == ':':  # enum with type
            ret_lst.append(lst[i])
            ret_lst.append(lst[i + 1])
            skip = 3
        else:
            ret_lst.append(lst[i])

    return ret_lst


# remove forward declaration , typedef struct define or other not class/struct define situation
def rm_not_class_define(lst):
    ret_lst = []
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue

        if lst[i] == KEYWORD_CLASS and will_encounter_semicolon_before_lbrace(lst, i):
            ret_lst.append("invalid_class")
        elif lst[i] == KEYWORD_STRUCT and will_encounter_semicolon_before_lbrace(lst, i):
            ret_lst.append("invalid_struct")
        elif lst[i] == KEYWORD_TYPEDEF and lst[i + 1] == KEYWORD_STRUCT:
            ret_lst.append(KEYWORD_TYPEDEF)
            ret_lst.append("invalid_struct")
            skip = 1
        else:
            ret_lst.append(lst[i])
    return ret_lst


def rm_using_namespace(lst):
    ret_lst = []
    skip = 0
    for i in range(len(lst)):
        if skip > 0:
            skip -= 1
            continue
        if lst[i] == KEYWORD_USING and lst[i + 1] == KEYWORD_NAMESPACE:
            ret_lst.append("using_namespace")
            skip = 1
        else:
            ret_lst.append(lst[i])
    return ret_lst


def rm_not_public_part(lst):
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
            ret_lst.extend(rm_not_public_part(rm_class_inheritance(lst[i:i + class_size])))
            skip = class_size
        else:
            ret_lst.append(lst[i])
    return ret_lst


def process(text):
    return sink_namespace(
        rm_all_spaces(
            rm_other_irrelevant(
                rm_irrelevant_in_class(
                    trim_abnormal_enum(
                        rm_not_class_define(
                            rm_using_namespace(
                                to_list(
                                    rm_macro(
                                        add_extra_space(
                                            rm_string_literal(
                                                rm_comments(text))))))))))))


# main starts
if os.path.exists(OUTPUT_CPP_FILE):
    os.remove(OUTPUT_CPP_FILE)
if os.path.exists(OUTPUT_HEAD_FILE):
    os.remove(OUTPUT_HEAD_FILE)

output_cpp_file = open(OUTPUT_CPP_FILE, 'a')
output_head_file = open(OUTPUT_HEAD_FILE, 'a')

output_head_file.write("// auto generated by enum2str_gen.py, modify it if needed\n"
                       "#ifndef ENUM_2_STR_H__\n"
                       "#define ENUM_2_STR_H__\n"
                       "#define ENUM2STR(...) enum2str(__VA_ARGS__).data()\n\n"
                       "#include <string>\n")

output_cpp_file.write("// auto generated by enum2str_gen.py, modify it if needed\n"
                      "#include <string>\n")

INT = pp.Word(pp.nums + "-")
LBRACE, RBRACE, EQ, COMMA = pp.Suppress.using_each("{}=,")
ENUM_VALUE = pp.Word(pp.alphas + "_", pp.alphanums + "_" + "::")
ENUM_VALUE_COMBO = pp.Group(ENUM_VALUE("value") + pp.Optional(EQ + INT))
ENUM_VALUE_COMBO_LIST = pp.Group(ENUM_VALUE_COMBO + (COMMA + ENUM_VALUE_COMBO)[...] + pp.Optional(COMMA))
ENUM_BLOCK = LBRACE + ENUM_VALUE_COMBO_LIST("value_list") + RBRACE

# find instances of enums ignoring other syntax
for input_file_path in scan_dir(SRC_DIR):
    input_file = open(input_file_path, 'r')
    cpp_cache = io.StringIO()
    head_cache = io.StringIO()

    for enum, start, stop in ENUM_BLOCK.scan_string(process(input_file.read())):
        first_item = True
        for item in enum.value_list:
            if first_item:
                first_item = False
                head_cache.write("std::string enum2str(%s e);\n" % '::'.join(item.value.split('::')[0:-1]))
                cpp_cache.write("std::string enum2str(%s e) {\n" % '::'.join(item.value.split('::')[0:-1]))
                cpp_cache.write("  switch (e) {\n")

            cpp_cache.write("    case %s: return \"%s\";\n" % (item.value, item.value.split('::')[-1]))
        cpp_cache.write("    default: return \"\";\n  }\n}\n")

    if len(cpp_cache.getvalue()) != 0:
        output_cpp_file.write("#include \"%s\"\n" % input_file_path)
        output_head_file.write("#include \"%s\"\n" % input_file_path)
        output_cpp_file.write(cpp_cache.getvalue())
        output_head_file.write(head_cache.getvalue())

output_head_file.write("#endif  // ENUM_2_STR_H__\n")
