// Assigned to a local variable then used in comparison

#define MACRO 3600

int foo() {
    int a = 100;    // DONT FINDME
    int b = MACRO;  // FINDME
    if (a == b)     // FINDME
        return 1;   // DONT FINDME
    return 0;       // DONT FINDME
}
