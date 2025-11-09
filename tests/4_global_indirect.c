// Assignment to global variable through an intermediate variable

#define MACRO 3600

int g;

int foo() {
    int a = MACRO; // FINDME // NOT EXTERNAL
    int b = a;     // FINDME // NOT EXTERNAL
    g = a;         // FINDME // EXTERNAL
    return 0;
}
