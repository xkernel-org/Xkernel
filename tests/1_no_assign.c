// Immediately used in comparison

#define MACRO 3600

int foo() {
    int a = 100;      // DONT FINDME
    if (a == MACRO)   // FINDME
        return 1;     // DONT FINDME
    return 0;         // DONT FINDME
}
