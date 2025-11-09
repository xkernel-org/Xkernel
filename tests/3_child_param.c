// Passed as parameter to a child function

#define MACRO 3600

int bar(int x) { return -x; } // DONT FINDME // FIXME L=1 for now

int foo() {
    int y = bar(MACRO);       // FINDME // EXTERNAL
    return 0;                 // DONT FINDME
}
