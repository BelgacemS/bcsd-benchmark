#include<stdio.h>
#include<string.h>

int main() {
	int N = 0;
	int num = 0;

	scanf("%d",&N);

	for (int num = 1;1 ; num++) {
		if (num % 2 == 0 && num % N == 0) {
			printf("%d", num);
			break;
		}
	}

	return 0;
}