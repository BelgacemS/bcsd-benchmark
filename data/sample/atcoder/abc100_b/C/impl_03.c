#include <stdio.h>
#include <math.h>
int main()
{
	long long D,N,x; 
	scanf("%lld %lld",&D,&N);
	if(N==100){
		N++;
	} 
	x=pow(100,D)*N;
	printf("%lld",x);
	return 0;
}
