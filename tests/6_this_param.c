// Constant assigned to a pointer parameter

#define MACRO 3600

int foo(int *x) {
    *x = MACRO; // FINDME // EXTERNAL
    return 0;
}
