// Passed as parameter to an extern function

#define MACRO 3600

extern void external_func(int x); // DONT FINDME // FIXME L=1 for now

int foo() {
    external_func(MACRO); // FINDME // EXTERNAL
    return 0;
}
