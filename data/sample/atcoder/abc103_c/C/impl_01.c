#include <stdio.h>

int main() {
	int n,sum=0,a;
	scanf("%d",&n);
	for(int i=0;i<n;i++){
		scanf("%d",&a);
		sum+=a-1;
	}
	printf("%d",sum);
	return 0;
}
