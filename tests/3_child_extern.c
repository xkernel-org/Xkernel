// Passed as parameter to an extern function

#define MACRO 3600

extern void external_func(int x);

int foo() {
    external_func(MACRO); // FINDME // INTERPROC
    return 0;
}
