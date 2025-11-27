// Caller passes a pointer parameter to a child function

#define MACRO 3600

int foo(int *x) {
    *x = MACRO; // FINDME // UPWARD-INTERPROC // FUNC=foo L=0
    return 0;   // DONT FINDME
}

int parent() {
    int a, b, c, d, e = 0; // DONT FINDME
    foo(&a);               // FINDME // NOT EXTERNAL // FUNC=parent L=1
    b = c;                 // DONT FINDME
    c = b + a;             // FINDME // NOT EXTERNAL // FUNC=parent L=1
    d = b + e;             // DONT FINDME
    e = c + b;             // FINDME // NOT EXTERNAL // FUNC=parent L=1
    return 0;              // DONT FINDME
}
