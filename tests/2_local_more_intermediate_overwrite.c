// Intermediate variable overwritten then used in comparison

#define MACRO 3600

int foo() {
    int a = 100;       // DONT FINDME
    int b = MACRO;     // FINDME // NOT EXTERNAL
    int c, d, e, f, g; // DONT FINDME
    int z;             // DONT FINDME

    z = b;     // FINDME // NOT EXTERNAL

    b = 42;    // DONT FINDME

    c = b + a; // DONT FINDME
    d = c - b; // DONT FINDME
    e = d * a; // DONT FINDME
    f = e / b; // DONT FINDME
    g = f % c; // DONT FINDME

    if (a == g)   // DONT FINDME
        return 1; // DONT FINDME
    return 0;     // DONT FINDME
}
