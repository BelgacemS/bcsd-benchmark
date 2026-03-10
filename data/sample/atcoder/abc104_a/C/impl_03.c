#include<stdio.h>
int main(){
	int rate;
	scanf("%d",&rate);
	
	if(rate<1200){
		printf("ABC");
	} else if(rate<2800){
		printf("ARC");
	}else{
		printf("AGC");
	}
	
	return 0;
}