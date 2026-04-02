#include<stdio.h>
#include<stdlib.h>
int main(){
	int a,b,c;
	scanf("%d %d %d",&a,&b,&c);
	
	int cost1=abs(b-a)+abs(c-b);
	int cost2=abs(c-a)+abs(b-c);
	int cost3=abs(c-b)+abs(a-c);
	int cost4=abs(a-b)+abs(c-a);
	int cost5=abs(a-c)+abs(b-a);
	int cost6=abs(b-c)+abs(a-b);
	int minp=cost1;
	if(cost2<minp){
		minp=cost2;
	}if(cost3<minp){
		minp=cost3;
	}if(cost4<minp){
		minp=cost4;
	}if(cost5<minp){
		minp=cost5;
	}if(cost6<minp){
		minp=cost6;
	}
	
	printf("%d",minp);
	
	return 0;

	
}