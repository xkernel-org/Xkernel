#include <stdio.h>

int main() {
    int a = 5;
    #define MACRO 13
    int b = a * 13;
    printf("%d\n", b);
}