# enum2str
a enum to string converter code(c++) generator

features:
1. walk through all src files to find enum definition, and gen enum2str code(.cpp+.h) of them;

limitations:
1. can not gen namespace prefix if enum is in a namespace;
2. can not gen code of a enum if it is a "typedef enum {...} enum_name" style;

dependency:
1. python3;
2. pyparsing >= 3.1.0;
