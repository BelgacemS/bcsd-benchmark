#include<stdio.h>
int n;
int main(){
	scanf("%d",&n);
	long long sum=0;
	for(int i=0;i<n;i++){
		int a;
		scanf("%d",&a);
		a--;
		sum+=a;
	}
	printf("%lld",sum);
	return 0;
}