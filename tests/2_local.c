#define MACRO 3600

int foo() {
    int a = 100;
    int b = MACRO;
    if (a == b)
        return 1;
    return 0;
}
