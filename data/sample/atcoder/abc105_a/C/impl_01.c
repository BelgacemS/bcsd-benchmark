#include<stdio.h>
int main(){
	int n,k;
	scanf("%d %d",&n,&k);
	int medium=n%k;
	if(medium==0){
		printf("0");
	}else{
		printf("1");
	}
	
	return 0;
}