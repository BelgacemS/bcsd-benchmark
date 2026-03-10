#include <stdio.h>
#include <string.h>

int main() {
	char s[101],t[101];
    scanf("%s",s);
    scanf("%s",t);
    int len=strlen(s);
    for(int i=0;i<len;i++){
    	int m=t[len-1];
		for(int i=len-1;i>=1;i--){
			t[i]=t[i-1];
		}
		t[0]=m;
		if(strcmp(t,s)==0){
			printf("Yes");
			return 0;
		}
	}
	printf("No");
    return 0;
}