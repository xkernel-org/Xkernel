// Assigned to a pointer that's not directly a parameter

#define MACRO 3600

struct S1 {
    int x;
    int y;
};

struct S2 {
    int *x;
    int *y;
};

int foo(struct S1 *s) {
    int *y = &(s->x); // POTENTIAL PARAMETER
    int *z = y;       // POTENTIAL PARAMETER
    *z = MACRO;       // FINDME // UPWARD-INTERPROC // FUNC=foo L=0
    return 0;         // DONT FINDME
}

int parent() {
    int a, b, c, d, e = 0; // DONT FINDME
    struct S1 s = {0, 0};  // DONT FINDME
    foo(&s);               // FINDME // NOT EXTERNAL // FUNC=parent L=1
    b = c;                 // DONT FINDME
    c = b + s.x;           // FINDME // NOT EXTERNAL // FUNC=parent L=1
    d = b + e;             // DONT FINDME
    e = c + b;             // FINDME // NOT EXTERNAL // FUNC=parent L=1
    return 0;              // DONT FINDME
}
