#define INNER (( \
    1024+1, 3^7 \
))
#define OUTER (INNER ? 5 : 7)

#define M3 (M2)
#define M2 (M1)
#define M1 42

#define S "hello"

#define Ma 0x55
#define Mb -5
#define Mc (5)

int g;
char *gs;

int main(void) {
    int l1 = OUTER, l2 = 0;

    g = OUTER; // not recognized by "integer literal" mode
    g = M3;
    g = Ma;
    g = Mb; // Previously not recognized by "integer literal" mode because
            // negative values involve unary operator (-).
    g = Mc;

    // not recognized by "constant macro" mode
    // or "integer literal" mode

    g = sizeof(int);
    g = (OUTER);
    g = OUTER + 1;

    gs = S;
}
