#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main() {
    long long  N=0;
    scanf("%d",&N);
    if (N%2==0)
    {
        printf("%lld",N);
    }
    else if (N%2!=0)
    {
        printf("%lld",2*N);
    }
}