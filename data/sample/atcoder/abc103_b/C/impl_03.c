#include<stdio.h>
#include<string.h>

int main(){
    char s[105], t[105], temp[210];  
    
    fgets(s, sizeof(s), stdin);
    fgets(t, sizeof(t), stdin);
    int len1=strlen(s);
	int len2=strlen(t); 
    if(len1>0&&s[len1-1]=='\n'){
		s[len1-1]='\0';
		len1--;
	}if(len2>0&&t[len2-1]=='\n'){
		t[len2-1]='\0';
		len2--;
	}
    strcpy(temp, s);
    strcat(temp, s);
    if(strstr(temp, t) != NULL) {
    printf("Yes\n");
} else {
    printf("No\n");
}
    
    return 0;
}