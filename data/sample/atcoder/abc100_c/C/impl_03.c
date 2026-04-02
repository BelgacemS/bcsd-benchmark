#include <stdio.h>

int main(){

	int n, result = 0;

	scanf("%d", &n);
	
	long long bil[n];
	
	for (int i = 0; i < n; i++){
		scanf("%lld", &bil[i]);
	}
	
	for (int i = 0; i < n; i++){
		while(bil[i] % 2 == 0){
			bil[i] = bil[i] / 2;
			result++;
		}
	}
	
	printf("%d\n", result);
	
	return 0;
}