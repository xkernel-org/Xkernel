// Caller passes a pointer parameter to a child function, and this
// parameter is a struct

#define MACRO 3600

struct S {
    int x;
    int y;
};

int foo(struct S *s) {
    s->x = MACRO; // FINDME // UPWARD-INTERPROC // FUNC=foo L=0
    return 0;     // DONT FINDME
}

int parent() {
    int a, b, c, d, e = 0; // DONT FINDME
    struct S s = {0, 0};   // DONT FINDME

    foo(&s);               // FINDME // NOT EXTERNAL // FUNC=parent L=1
    b = c;                 // DONT FINDME
    c = b + s.x;           // FINDME // NOT EXTERNAL // FUNC=parent L=1
    d = b + e;             // DONT FINDME
    e = c + b;             // FINDME // NOT EXTERNAL // FUNC=parent L=1

    return 0;              // DONT FINDME
}
