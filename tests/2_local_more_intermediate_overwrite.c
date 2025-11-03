#define MACRO 3600

int foo() {
    int a = 100;
    int b = MACRO;
    int c, d, e, f, g;
    int z;

    z = b; // FINDME

    b = 42; // DONT FINDME

    c = b + a; // DONT FINDME
    d = c - b; // DONT FINDME
    e = d * a; // DONT FINDME
    f = e / b; // DONT FINDME
    g = f % c; // DONT FINDME

    if (a == g) // DONT FINDME
        return 1;
    return 0;
}
