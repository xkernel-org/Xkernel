// Deeper child function

#define MACRO 3600

int g;

void baz(int x) {
    g = x;    // FINDME // EXTERNAL
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
