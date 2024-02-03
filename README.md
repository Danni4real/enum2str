# enum2str
A script can generate c++ code that can convert enum to string 

Features:
1. can scan src files recursively to detect enum definitions in headers, and gen enum2str code(.cpp .h) of them;
2. can exclude files/dirs you don't want to scan;

Limitations:
1. unknown behavior when encounter some preprocessor related code;

Dependency:
1. python3;
2. pyparsing >= 3.1.0;
