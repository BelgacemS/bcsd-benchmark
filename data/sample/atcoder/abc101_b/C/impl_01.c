#include<stdio.h>
int main(){
	int n;
	scanf("%d",&n);
	int medium=n;
	if(medium<0){
		medium=-medium;
	}
	int digit=0;
	while(medium>0){
		 digit+=medium%10;
		medium/=10;
		
	}if(n%digit==0){
		printf("Yes\n");
	}else{
		printf("No\n");
	}
	
	return 0;
}