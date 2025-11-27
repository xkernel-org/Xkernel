// Return a constant value indirectly

#define MACRO 3600

int foo() {
    int a = MACRO; // FINDME // NOT EXTERNAL // FUNC=foo L=0
    return a;      // FINDME // UPWARD-INTERPROC // FUNC=foo L=0
}
