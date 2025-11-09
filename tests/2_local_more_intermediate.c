// Multiple intermediate variables then used in comparison

#define MACRO 3600

int foo() {
    int a = 100;       // DONT FINDME
    int b = MACRO;     // FINDME // NOT EXTERNAL
    int c, d, e, f, g; // DONT FINDME

    c = b + a; // FINDME // NOT EXTERNAL
    d = c - b; // FINDME // NOT EXTERNAL
    e = d * a; // FINDME // NOT EXTERNAL
    f = e / b; // FINDME // NOT EXTERNAL
    g = f % c; // FINDME // NOT EXTERNAL

    if (a == g)       // FINDME // NOT EXTERNAL
        return 1;     // DONT FINDME
    return 0;         // DONT FINDME
}
