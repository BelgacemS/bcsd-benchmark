#include <stdio.h>

int f(int n);
int main() {
	int n,count=0;
	scanf("%d",&n);
	int a[n];
	for(int i=0;i<n;i++){
		scanf("%d",&a[i]);
	}
	for(int i=0;i<n;i++){
		count+=f(a[i]);
	}
	printf("%d",count);
	return 0;
}
int f(int n){
	int count=0;
	while(1){
		if(n%2!=0){
			break;
		}
		count++;
		n/=2;
	}
	return count;
}