#include <stdio.h>
#include <string.h>

int main() {
	char s[11];
	scanf("%10s",s);
	int len=strlen(s),found=1;
	if(s[0]!='A'){
		found=0;
	}
	int count=0,cnt=0;
	for(int i=0;i<len;i++){
		if(s[i]=='C'&&(i>=2&&i<=len-2)){
			count++;
		}
		if(s[i]>'z'||s[i]<'a'){
			cnt++;
		}
	}
	if(count!=1||cnt!=2){
		found=0;
	}
	if(found){
		printf("AC");
	}
	else{
		printf("WA");
	}
    return 0;
}