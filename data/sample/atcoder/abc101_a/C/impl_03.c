#include<stdio.h>
int main()
{
int i;
char S[5];
int count=0;
scanf("%s",S);
for(i=0;i<4;i++)
{
if(S[i]=='+')

count++;

else

count--;

}
printf("%d\n",count);
return 0;
}
