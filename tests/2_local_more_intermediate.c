#define MACRO 3600

int foo() {
    int a = 100;
    int b = MACRO;
    int c, d, e, f, g;

    c = b + a;
    d = c - b;
    e = d * a;
    f = e / b;
    g = f % c;

    if (a == g) // FINDME
        return 1;
    return 0;
}
