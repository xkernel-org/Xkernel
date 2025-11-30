// Higher L values

#define MACRO 3600

int foo(int *x) {
    *x = MACRO; // FINDME // UPWARD-INTERPROC // FUNC=foo L=0
    return 0;   // DONT FINDME
}

int parent(int *x) {
    int a, b, c, d, e = 0; // DONT FINDME
    foo(&a);               // FINDME // NOT EXTERNAL // FUNC=parent L=1
    b = c;                 // DONT FINDME
    c = b + a;             // FINDME // NOT EXTERNAL // FUNC=parent L=1
    d = b + e;             // DONT FINDME
    *x = c + b;            // FINDME // UPWARD-INTERPROC // FUNC=parent L=1
    return 0;              // DONT FINDME
}

int grandparent(int *x) {
    parent(x);             // FINDME // UPWARD-INTERPROC // FUNC=grandparent L=2
    return 0;              // DONT FINDME
}

int greatgrandparent(int *x) {
    int a = 0;             // DONT FINDME
    grandparent(&a);       // FINDME // NOT EXTERNAL // FUNC=greatgrandparent L=3
    *x = a + 1;            // FINDME // UPWARD-INTERPROC // FUNC=greatgrandparent L=3
    return 0;              // DONT FINDME
}
