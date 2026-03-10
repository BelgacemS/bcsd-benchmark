#include <stdio.h>
#include <stdlib.h>

void baseNeg2(int n) {
    if (n == 0) {
        printf("0\n");
        return;
    }

    char result[35];
    int i = 0;

    while (n != 0) {
        int remainder = n % (-2);
        n = n / (-2);


        if (remainder < 0) {
            remainder += 2;
            n += 1;
        }


        if (remainder == 0) {
            result[i++] = '0';
        } else {
            result[i++] = '1';
        }
    }


    result[i] = '\0';


    int len = i;
    for (int j = 0; j < len / 2; j++) {
        char temp = result[j];
        result[j] = result[len - j - 1];
        result[len - j - 1] = temp;
    }


    printf("%s\n", result);
}

int main() {
    int n;
    scanf("%d", &n);

    baseNeg2(n);

    return 0;
}
