#include<stdio.h>
#include<string.h>
int p[102],c[102];
int cnt=1e9;

void func(int P,long long s,int d,int g,int C,int r){
    
    if(r==d){
        if(C<cnt && s>=g){
            cnt=C;
        }
        return;
    }
    
    if(s>=g){
        if(C<cnt)cnt=C;
        return;
    }
    
  
    if( ((g-s) + (100.0 *(1+P)) - 1)/(100.0 *(1+P))<= p[P]){
        int k= ((g-s) + (100.0 *(1+P)) - 1)/(100.0 *(1+P));
        if(C+k < cnt)cnt=C+k;
    }
   
  
    func((P+1)%d,s,d,g,C,r+1);
    func((P+1)%d,s+(long long)p[P]*((1+P)*100)+c[P],d,g,C+p[P],r+1);
    
    
}

int main(void){
    // Your code here!
    int d,g;
    scanf("%d%d",&d,&g);
    for(int i=0;i<d;i++)scanf("%d%d",&p[i],&c[i]);
   
    for(int i=0;i<d;i++)func(i,0,d,g,0,0);
    printf("%d",cnt);
    return 0;
}