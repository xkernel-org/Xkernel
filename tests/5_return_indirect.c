// Return a constant value indirectly

#define MACRO 3600

int foo() {
    int a = MACRO; // FINDME // NOT EXTERNAL
    return a;      // FINDME // UPWARD-INTERPROC
}
