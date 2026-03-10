#include<stdio.h>
#include<string.h>
int main(){
	char s[105];
	fgets(s,sizeof(s),stdin);
	int len=strlen(s);
	int sign=1;
	
	if(len>0&&s[len-1]=='\n'){
		s[len-1]='\0';
		len--;
	}
	
	 int count=0;
	 
	if(s[0]!='A'){
		sign=0;
	}
	 
	 for(int i=2;i<len-1;i++){
	 	if(s[i]=='C'){
	 		count++;
		 }
	 }if(count!=1){
	 	sign=0;
	 } 
	 
	  for(int i=0;i<len;i++){
        if(i==0){  
            if(s[i]!='A') sign=0;
        }
        else if(i>=2&&i<=len-2){  
            if(s[i]=='C') continue;  
            else if(s[i]<'a'||s[i]>'z') sign=0;  
        }
        else{  
            if(s[i]<'a'||s[i]>'z') sign=0;  
        }
    }
	   
if(sign){
	 	printf("AC\n");
	 }else{
	 	printf("WA\n");
	 }
	 
	 return 0;
	 
}