#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <ctype.h>

static const char* cs[] = {
    "M", "CM", "D", "CD", "C", "XC",
    "L", "XL", "X", "IX", "V", "IV", "I"};

static const int vs[] = {
    1000, 900, 500, 400, 100, 90,
    50, 40, 10, 9, 5, 4, 1};

char* intToRoman(int num) {
    static char ans[20];
    ans[0] = '\0';
    for (int i = 0; i < 13; ++i) {
        while (num >= vs[i]) {
            num -= vs[i];
            strcat(ans, cs[i]);
        }
    }
    return ans;
}


int main(void) { return 0; }
