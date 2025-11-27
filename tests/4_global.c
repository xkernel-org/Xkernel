// Assignment to global variable

#define MACRO 3600

int g;

int foo() {
    int a = 100; // DONT FINDME
    g = MACRO;   // FINDME // EXTERNAL // FUNC=foo L=0
    return 0;    // DONT FINDME
}
