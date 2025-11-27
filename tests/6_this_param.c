// Constant assigned to a pointer parameter

#define MACRO 3600

int foo(int *x) {
    *x = MACRO; // FINDME // UPWARD-INTERPROC // FUNC=foo L=0
    return 0;
}
