#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <ctype.h>

bool isPalindrome(int x) {
    if (x < 0 || (x != 0 && x % 10 == 0)) {
        return false;
    }

    int y = 0;
    while (y < x) {
        y = y * 10 + x % 10;
        x /= 10;
    }

    return (x == y || x == y / 10);
}


int main(void) { return 0; }
