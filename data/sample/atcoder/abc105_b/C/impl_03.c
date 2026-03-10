#include <stdio.h>

int main(){
  int N;
  scanf("%d",&N);
  for (int i = 0; i * 4 <= N; i++){
    int z = N - (i * 4);
    if (z % 7 == 0){
      printf("Yes");
      return 0;
    }
  }
  printf("No");
  return 0;
}