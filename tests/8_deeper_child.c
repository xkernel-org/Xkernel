// Deeper child function

#define MACRO 3600

int g;

void baz(int x) {
    int y = x;    // FINDME // NOT EXTERNAL
    if (y > 3000) // FINDME // NOT EXTERNAL
        g = 1;    // DONT FINDME
    else          // DONT FINDME
        g = 0;    // DONT FINDME
}

void bar(int x) {
    int y = 3000; // DONT FINDME
    baz(y);       // DONT FINDME
    baz(x);       // FINDME // INTERPROC
}

int foo() {
    bar(MACRO); // FINDME // INTERPROC
    return 0;   // DONT FINDME
}
