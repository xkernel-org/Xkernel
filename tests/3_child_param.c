// Passed as parameter to a child function

#define MACRO 3600

int bar(int x) { return -x; } // FINDME // UPWARD-INTERPROC // FUNC=bar L=-1

int foo() {
    int y = bar(MACRO);       // FINDME // INTERPROC // FUNC=foo L=0
    return 0;                 // DONT FINDME
}
