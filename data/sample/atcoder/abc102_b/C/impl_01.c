#include<stdio.h>
#include<stdlib.h>
int main(){
	int n;
	scanf("%d",&n);
	int num;
	scanf("%d",&num);
	int maxn=num;
	int minn=num;
	
	for(int i=1;i<n;i++){
		scanf("%d",&num);
		if(minn>num){
			minn=num;
		}
		if(maxn<num){
			maxn=num;
		}
	}
	int absolute=abs(maxn-minn);
	
	printf("%d\n",absolute);
	
	return 0;
}