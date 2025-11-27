// Deeper child function, with external effect in grandchild

#define MACRO 3600

int g;

void baz(int x) {
    g = x;    // FINDME // EXTERNAL // FUNC=baz L=-2
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
