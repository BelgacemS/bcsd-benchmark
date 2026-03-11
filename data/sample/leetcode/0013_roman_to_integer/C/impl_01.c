#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <ctype.h>

int nums(char c) {
    switch (c) {
    case 'I': return 1;
    case 'V': return 5;
    case 'X': return 10;
    case 'L': return 50;
    case 'C': return 100;
    case 'D': return 500;
    case 'M': return 1000;
    default: return 0;
    }
}

int romanToInt(char* s) {
    int ans = nums(s[strlen(s) - 1]);
    for (int i = 0; i < (int) strlen(s) - 1; ++i) {
        int sign = nums(s[i]) < nums(s[i + 1]) ? -1 : 1;
        ans += sign * nums(s[i]);
    }
    return ans;
}


int main(void) { return 0; }
