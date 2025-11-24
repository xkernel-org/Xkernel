// Return to the parent

#define MACRO 3600

int foo() {
    return MACRO; // FINDME // UPWARD-INTERPROC
}

int dummy;

int parent() {
    int a = 0, b = 0, c = 0, d = 0; // DONT FINDME
    dummy++;                        // DONT FINDME
    a = foo();                      // FINDME // NOT EXTERNAL
    b = dummy;                      // DONT FINDME
    c = a + b;                      // FINDME // NOT EXTERNAL
    d = 3 * b;                      // DONT FINDME
    return 0;
}
