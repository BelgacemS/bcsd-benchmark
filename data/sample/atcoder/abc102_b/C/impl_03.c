#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main() {
    int  N=0;
    scanf("%d",&N);
    long long *arr=(long long*)malloc(N*sizeof(long long));
    for (int i = 0; i < N; i++)
    {
        scanf("%lld",&arr[i]);
    }
    long long max=arr[0];
    long long min=arr[1];
    for (int i = 0; i < N; i++)
    {
        if (arr[i]>max)
        {
           max=arr[i];
        }
        
    }
    for (int  i = 0; i < N; i++)
    {
       if (arr[i]<min)
       {
        min=arr[i];
       }
       
    }
    printf("%lld",max-min);
}