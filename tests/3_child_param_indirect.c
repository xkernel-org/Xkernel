// Passed as parameter to a child function through an intermediate variable

#define MACRO 3600

int bar(int x) { return -x; } // FINDME // UPWARD-INTERPROC

int foo() {
    int b = 100;        // DONT FINDME
    int a = MACRO + b;  // FINDME // NOT EXTERNAL
    bar(a);             // FINDME // INTERPROC
    return 0;
}
