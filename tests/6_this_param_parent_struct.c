// Caller passes a pointer parameter to a child function, and this
// parameter is a struct

#define MACRO 3600

struct S {
    int x;
    int y;
};

int foo(struct S *s) {
    s->x = MACRO; // FINDME // UPWARD-INTERPROC
    return 0;     // DONT FINDME
}

int parent() {
    int a, b, c, d, e = 0; // DONT FINDME
    struct S s = {0, 0};   // DONT FINDME

    foo(&s);               // FINDME // NOT EXTERNAL
    b = c;                 // DONT FINDME
    c = b + s.x;           // FINDME // NOT EXTERNAL
    d = b + e;             // DONT FINDME
    e = c + b;             // FINDME // NOT EXTERNAL

    return 0;              // DONT FINDME
}
