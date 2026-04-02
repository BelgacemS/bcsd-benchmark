#include <stdio.h>

int main() {
    int N;
    scanf("%d", &N);
    long long total = 0;
    for (int i = 0; i < N; i++) {
        long long a;
        scanf("%lld", &a);
        int cnt = 0;
        while (a % 2 == 0) {
            cnt++;
            a /= 2;
        }
        total += cnt;
    }
    printf("%lld\n", total);
    return 0;
}