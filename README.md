# enum2str
A enum to string converting code(c++) generator

Features:
1. can scan src files recursively to detect enum definitions in headers, and gen enum2str code(.cpp+.h) of them;
2. can exclude files/dirs you don't want to scan;
3. can detect enum definitions in namespace;
4. can detect enum definitions in public part of class/struct;

Limitations:
1. can not detect enum definition which is a "typedef enum {...} enum_name";
2. can not detect enum definition which is in a "typedef struct {...} struct_name";

Dependency:
1. python3;
2. pyparsing >= 3.1.0;
