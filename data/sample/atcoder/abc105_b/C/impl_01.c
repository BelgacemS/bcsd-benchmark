#include<stdio.h>
int main(){
	int n;
	scanf("%d",&n);
	
	
	int cake=n/4;
	int found=0;
	for(int i=0;i<=cake;i++){
		int medium=n-4*i;
		if(medium>=0&&medium%7==0){
			found=1;
			break;
		}
	}
	if(found){
		printf("Yes\n");
	}else{
		printf("No\n");
	}
	
	return 0;
}