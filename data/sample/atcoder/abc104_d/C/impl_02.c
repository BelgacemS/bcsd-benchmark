// LUOGU_RID: 176783844
#include<stdio.h>
long long a,b,c,d=1,i;int main(){i=getchar();while(i+1){if(i==65)a=(a+d)%1000000007;if(i==66)b=(b+a)%1000000007;if(i==67)c=(c+b)%1000000007;if(i==63){c=(3*c+b)%1000000007;b=(3*b+a)%1000000007;a=(3*a+d)%1000000007;d=(d*3)%1000000007;}i=getchar();}printf("%lld",c);}