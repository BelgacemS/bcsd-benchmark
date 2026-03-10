#include <stdio.h>
#include <stdlib.h>

int cmp_int(const void *a, const void *b){
	int x = *(const int *)a ;
	int y = *(const int *)b ;
	return (x > y) - (x < y);
}

int main(){
	int first[5];
	int temp = 0, result = 0;
	
	for(int i = 0; i < 3; i++){
		scanf("%d", &first[i]);
	}
	
	qsort(first, 3, sizeof(int), cmp_int);
	
	for(int i = 0; i < 2; i++){
		temp = abs(first[i + 1] - first[i]);
		result += temp;
	}
	
	printf("%d\n", result);
	return 0;
	
}