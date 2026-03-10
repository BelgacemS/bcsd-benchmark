#include <stdio.h>
#include <string.h>

int main() {
    char S[5];
    scanf("%s", S);
    int ans = 0;
    for (int i = 0; i < 4; i++) {
        if (S[i] == '+') {
            ans++;
        } else { // S[i] == '-'
            ans--;
        }
    }
    printf("%d\n", ans);
    return 0;
}