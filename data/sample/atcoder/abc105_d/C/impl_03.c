#include<stdio.h>

int main(){
  
  int N,M,A[100100],i,j;
  
  scanf("%d%d",&N,&M);
  for(i=0;i<N;i++){
    scanf("%d",&j);
    A[i]=j%M;
  }
  
  long int count=0,sum=0;
  long int amari[100100][2]={0},k,flag;
  
  for(i=0;i<N;i++){
      flag=0;
      sum+=A[i];
      sum%=M;
      for(k=0;k<count;k++){
        if(amari[k][0]==sum){
          amari[k][1]++;
          flag=1;
          break;
        }
      }
      if(flag==0){
        amari[count][0]=sum;
        amari[count][1]++;
        count++;
      }
    }
  
  
 
  
  long int sum1=0;
  for(i=0;i<count;i++){
    if(amari[i][0]==0){
      sum1+=((amari[i][1]*(amari[i][1]+1))/2);
    }else{
    sum1+=((amari[i][1]*(amari[i][1]-1))/2);
    }
   // printf("%ld\n",sum1);
  }
  
  printf("%ld\n",sum1);
  return 0;
}
    
  
  
  
 
      
      
      
      
  