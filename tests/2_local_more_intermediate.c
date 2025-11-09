// Multiple intermediate variables then used in comparison

#define MACRO 3600

int foo() {
    int a = 100;       // DONT FINDME
    int b = MACRO;     // FINDME
    int c, d, e, f, g; // DONT FINDME

    c = b + a; // FINDME
    d = c - b; // FINDME
    e = d * a; // FINDME
    f = e / b; // FINDME
    g = f % c; // FINDME

    if (a == g)       // FINDME
        return 1;     // DONT FINDME
    return 0;         // DONT FINDME
}
