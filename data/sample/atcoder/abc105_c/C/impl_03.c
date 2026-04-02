#include <stdio.h>
#include <stdlib.h>
#include <string.h>


void base_neg2(int N) {

    if (N == 0) {
        printf("0\n");
        return;
    }

    char result[1000];
    int index = 0;

    while (N != 0) {
        int remainder = N % -2;
        N /= -2;

        if (remainder < 0) {
            remainder += 2;
            N += 1;
        }

        result[index++] = remainder + '0';
    }


    for (int i = index - 1; i >= 0; i--) {
        putchar(result[i]);
    }
    putchar('\n');
}

int main() {
    int N;


    scanf("%d", &N);


    base_neg2(N);

    return 0;
}

