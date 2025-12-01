// Under the mode with downward interprocerdural analysis disabled, we
// should probably still assume other pointer parameters are affected.

#define MACRO 3600

int bar(int x, int *y, int *z) { return -x; } // DONT FINDME

int foo() {
    int b = 100;                           // DONT FINDME
    int a = MACRO + b;                     // FINDME // NOT EXTERNAL // FUNC=foo L=0
    int c = 0, d = 0, e = 0, f = 0, g = 0; // DONT FINDME
    bar(a, &c, &d);                        // FINDME // INTERPROC // FUNC=foo L=0

    e = b;                                 // DONT FINDME
    f = c;                                 // FINDME // NOT EXTERNAL // FUNC=foo L=0
    e = 12345;                             // DONT FINDME
    g = d + e;                             // FINDME // NOT EXTERNAL // FUNC=foo L=0

    return 0;
}
