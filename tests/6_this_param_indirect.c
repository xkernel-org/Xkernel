// Constant assigned to a pointer parameter through an intermediate variable

#define MACRO 3600

int foo(int *x) {
    int a = MACRO; // FINDME // NOT EXTERNAL // FUNC=foo L=0
    *x = a;        // FINDME // UPWARD-INTERPROC // FUNC=foo L=0
    return 0;
}
