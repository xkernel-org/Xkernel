#define MACRO 3600

int bar(int x) { return -x; }

int foo() {
    int y = bar(MACRO);
    return 0;
}

