#include <stdio.h>
#include <math.h>
int main() {
	long long int d,n;
	scanf("%lld %lld",&d,&n);
	if(n==100){
		printf("%.0lf",(n+1)*pow(100,d));
	}
	else{
		printf("%.0lf",n*pow(100,d));
	}
	return 0;
}
