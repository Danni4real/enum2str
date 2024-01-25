# enum2str
a enum to string converting code(c++) generator

features:
1. can scan all src files/dirs recursively to find enum definition, and gen enum2str code(.cpp+.h) of them;
2. can exclude files/dirs you don not want to scan;

limitations:
1. can not gen namespace prefix if a enum is in namespace or class or struct, you have to add prefix manually;
2. can not gen code of a enum if it is a "typedef enum {...} enum_name" style;

dependency:
1. python3;
2. pyparsing >= 3.1.0;
