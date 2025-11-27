// Function pointer stored in a struct field

#define MACRO 3600

int g;

void baz1(int x) {
    int y = x;    // FINDME // NOT EXTERNAL // FUNC=baz1 L=-2
    if (y > 3000) // FINDME // NOT EXTERNAL // FUNC=baz1 L=-2
        g = 1;    // DONT FINDME
    else          // DONT FINDME
        g = 0;    // DONT FINDME
}

void baz2(int x) {
    int y = x;    // DONT FINDME
    if (y > 3000) // DONT FINDME
        g = 1;    // DONT FINDME
    else          // DONT FINDME
        g = 0;    // DONT FINDME
}

struct ops {
    void (*callback)(int);
};

void bar(struct ops *op, int x) {
    op->callback(x); // FINDME // INTERPROC // FUNC=bar L=-1
}

int foo() {
    struct ops my_ops;      // DONT FINDME
    my_ops.callback = baz1; // DONT FINDME
    bar(&my_ops, MACRO);    // FINDME // INTERPROC // FUNC=foo L=0
    return 0;               // DONT FINDME
}
