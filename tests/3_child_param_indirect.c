// Passed as parameter to a child function through an intermediate variable

#define MACRO 3600

int bar(int x) { return -x; } // FINDME // UPWARD-INTERPROC // FUNC=bar L=-1

int foo() {
    int b = 100;        // DONT FINDME
    int a = MACRO + b;  // FINDME // NOT EXTERNAL // FUNC=foo L=0
    bar(a);             // FINDME // INTERPROC // FUNC=foo L=0
    return 0;
}
