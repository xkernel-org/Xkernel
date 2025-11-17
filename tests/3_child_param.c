// Passed as parameter to a child function

#define MACRO 3600

int bar(int x) { return -x; } // FINDME // EXTERNAL

int foo() {
    int y = bar(MACRO);       // FINDME // INTERPROC
    return 0;                 // DONT FINDME
}
