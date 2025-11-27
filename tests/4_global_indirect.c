// Assignment to global variable through an intermediate variable

#define MACRO 3600

int g;

int foo() {
    int a = MACRO; // FINDME // NOT EXTERNAL // FUNC=foo L=0
    int b = a;     // FINDME // NOT EXTERNAL // FUNC=foo L=0
    g = a;         // FINDME // EXTERNAL // FUNC=foo L=0
    return 0;      // DONT FINDME
}
