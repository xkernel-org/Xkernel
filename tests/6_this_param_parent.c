// Caller passes a pointer parameter to a child function

#define MACRO 3600

int foo(int *x) {
    *x = MACRO; // FINDME // UPWARD-INTERPROC
    return 0;   // DONT FINDME
}

int parent() {
    int a, b, c, d, e = 0; // DONT FINDME
    foo(&a);               // FINDME // NOT EXTERNAL
    b = c;                 // DONT FINDME
    c = b + a;             // FINDME // NOT EXTERNAL
    d = b + e;             // DONT FINDME
    e = c + b;             // FINDME // NOT EXTERNAL
    return 0;              // DONT FINDME
}
