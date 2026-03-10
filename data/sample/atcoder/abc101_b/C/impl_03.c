#include <stdio.h>

int main(){
	long long N;
	
	scanf("%lld", &N);
	long long temp = N;
	long long sn = 0;
	
	while(temp > 0){
		sn = sn + temp % 10;
		temp = temp / 10;
	} 
	
	printf("%s", (N % sn == 0)? "Yes\n" : "No\n");
	
	
	return 0;
}