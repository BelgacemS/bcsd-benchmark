#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>
int main(){
	int r;
	scanf("%d", &r);
	if (r < 1200) printf("ABC");
	else if (r < 2800) printf("ARC");
	else printf("AGC");
	return 0;
}