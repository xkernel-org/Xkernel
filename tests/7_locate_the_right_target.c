// Multiple <op> <constant value> in one function, we need a way of
// specifying the exact starting instruction

#define MACRO 3600

int foo() {
    int a = 3600;                   // DONT FINDME
    int b = MACRO;                  // FINDME // NOT EXTERNAL
    int c, d, e, f, g, h, i;        // DONT FINDME

    c = a + 1; // DONT FINDME
    d = a / 3; // DONT FINDME
    e = c * d; // DONT FINDME

    f = b + d; // FINDME // NOT EXTERNAL
    h = f % e; // FINDME // NOT EXTERNAL
    i = h++;   // FINDME // NOT EXTERNAL

    return 0; // DONT FINDME
}
