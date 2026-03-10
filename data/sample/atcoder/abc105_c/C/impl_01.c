#include<stdio.h>
int main(){
  int N,i;
  int ans[35]={0};
  int bin[35];
  int minusFlag=0;
  scanf("%d\n",&N);
  if(N<0){
    N*=-2;
    minusFlag=1;
  }
  if(N==0){
    printf("0\n");
    return 0;
  }
  for(i=0;(N>>i) > 0;i++){
    bin[i]=(N>>i)%2;
  }
  for(i=0;i<=34;i++){
    if(i%2==0){
      ans[i]+=bin[i];
    }else{
      if(bin[i]==1){
        ans[i+1]++;
        ans[i]++;
      }
    }
  }
  for(i=0;i<=34;i++){
    if(ans[i]>=2){
      ans[i+2]+=(ans[i]/2);
      ans[i+1]+=(ans[i]/2);
      ans[i]-=(ans[i]/2)*2;
    }
  }
  for(i=34;ans[i]==0;i--){
    
  }
  for(;i>=1;i--){
    printf("%d",ans[i]);
  }
  if(minusFlag==0){
    printf("%d",ans[0]);
  }
  printf("\n");
  return 0;
}