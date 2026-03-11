#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <ctype.h>

int lengthOfLongestSubstring(char* s) {
    int freq[256] = {0};
    int l = 0, r = 0;
    int ans = 0;
    int len = strlen(s);

    for (r = 0; r < len; r++) {
        char c = s[r];
        freq[(unsigned char) c]++;

        while (freq[(unsigned char) c] > 1) {
            freq[(unsigned char) s[l]]--;
            l++;
        }

        if (ans < r - l + 1) {
            ans = r - l + 1;
        }
    }

    return ans;
}


int main(void) { return 0; }
