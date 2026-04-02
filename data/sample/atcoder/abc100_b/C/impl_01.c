# include <stdio.h>
int main(){
    int D,N;
    scanf("%d %d",&D,&N);
    long long m=1;
    for(int i=0;i<D;i++){
        m=m*100;
    }
    long long n=m*N;
    if(D==0&&N==100){
        n=101;
    }else if(D==1&&N==100){
        n=100*100+100;
    }else if(D==2&&N==100){
        n=100*100*100+10000;
    }
    printf("%lld",n);
    return 0;
}