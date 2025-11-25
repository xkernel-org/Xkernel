// Constant assigned to a pointer parameter through an intermediate variable

#define MACRO 3600

int foo(int *x) {
    int a = MACRO; // FINDME // NOT EXTERNAL
    *x = a;        // FINDME // UPWARD-INTERPROC
    return 0;
}
