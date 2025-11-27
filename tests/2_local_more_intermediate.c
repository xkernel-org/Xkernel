// Multiple intermediate variables then used in comparison

#define MACRO 3600

int foo() {
    int a = 100;       // DONT FINDME
    int b = MACRO;     // FINDME // NOT EXTERNAL // FUNC=foo L=0
    int c, d, e, f, g; // DONT FINDME

    c = b + a; // FINDME // NOT EXTERNAL // FUNC=foo L=0
    d = c - b; // FINDME // NOT EXTERNAL // FUNC=foo L=0
    e = d * a; // FINDME // NOT EXTERNAL // FUNC=foo L=0
    f = e / b; // FINDME // NOT EXTERNAL // FUNC=foo L=0
    g = f % c; // FINDME // NOT EXTERNAL // FUNC=foo L=0

    if (a == g)       // FINDME // NOT EXTERNAL // FUNC=foo L=0
        return 1;     // DONT FINDME
    return 0;         // DONT FINDME
}
