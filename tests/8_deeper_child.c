// Deeper child function

#define MACRO 3600

int g;

void baz(int x) {
    int y = x;    // FINDME // NOT EXTERNAL // FUNC=baz L=-2
    if (y > 3000) // FINDME // NOT EXTERNAL // FUNC=baz L=-2
        g = 1;    // DONT FINDME
    else          // DONT FINDME
        g = 0;    // DONT FINDME
}

void bar(int x) {
    int y = 3000; // DONT FINDME
    baz(y);       // DONT FINDME
    baz(x);       // FINDME // INTERPROC // FUNC=bar L=-1
}

int foo() {
    bar(MACRO); // FINDME // INTERPROC // FUNC=foo L=0
    return 0;   // DONT FINDME
}
