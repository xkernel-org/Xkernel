// The function pointer can be assigned to a few different functions
// and we conservatively track all of them.

#define MACRO 3600

int g;

void baz2(int x) {
    int y = x;    // FINDME // NOT EXTERNAL
    if (y > 3000) // FINDME // NOT EXTERNAL
        g = 1;    // DONT FINDME
    else          // DONT FINDME
        g = 0;    // DONT FINDME
}

void baz1(int x) {
    int y = x;    // FINDME // NOT EXTERNAL
    if (y > 3000) // FINDME // NOT EXTERNAL
        g = 1;    // DONT FINDME
    else          // DONT FINDME
        g = 0;    // DONT FINDME
}

void bar(int x) {
    void (*baz)(int); // DONT FINDME
    baz = baz1;       // DONT FINDME
    baz = baz2;       // DONT FINDME
    int y = 3000;     // DONT FINDME
    baz(y);           // DONT FINDME
    baz(x);           // FINDME // INTERPROC
}

int foo() {
    bar(MACRO); // FINDME // INTERPROC
    return 0;   // DONT FINDME
}
