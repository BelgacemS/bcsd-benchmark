#include <stdio.h>
#include <stdlib.h>

typedef struct {
    long long x, y, z;
} Cake;

int compare(const Cake *a, const Cake *b) {
    long long sum_a = a->x + a->y + a->z;
    long long sum_b = b->x + b->y + b->z;
    return (sum_a < sum_b) ? 1 : ((sum_a == sum_b) ? 0 : -1);
}

int main(void) {
    int N, M;
    scanf("%d %d", &N, &M);
    Cake cakes[1000];
    for (int i = 0; i < N; i++) {
        scanf("%lld %lld %lld", &cakes[i].x, &cakes[i].y, &cakes[i].z);
    }

    long long max = 0;
    for (int i = 0; i < 8; i++) {
        Cake temp_cakes[1000];
        for (int j = 0; j < N; j++) {
            temp_cakes[j] = cakes[j];
            if (i & 1) temp_cakes[j].x = -temp_cakes[j].x;
            if (i & 2) temp_cakes[j].y = -temp_cakes[j].y;
            if (i & 4) temp_cakes[j].z = -temp_cakes[j].z;
        }
        qsort(temp_cakes, N, sizeof(Cake), (int (*)(const void *, const void *))compare);
        long long sum_x = 0, sum_y = 0, sum_z = 0;
        for (int j = 0; j < M; j++) {
            sum_x += temp_cakes[j].x;
            sum_y += temp_cakes[j].y;
            sum_z += temp_cakes[j].z;
        }
        long long total = llabs(sum_x) + llabs(sum_y) + llabs(sum_z);
        if (total > max) max = total;
    }
    printf("%lld\n", max);
    return 0;
}