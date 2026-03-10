#include<stdio.h>
int main(){
	int a;
	scanf("%d",&a);
	if(a<1200){
		printf("ABC");
	}else if(a>=1200&&a<2800){
		printf("ARC");
	}else if(a>=2800){
		printf("AGC");
	}
	return 0;
} 