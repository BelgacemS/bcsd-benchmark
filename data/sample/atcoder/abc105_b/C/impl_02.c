#include <stdio.h>
int main(void) {
  int n,i,j;
  scanf("%d%d",&n);
  for (i = 0; i <= 15; i++) {
    for (j = 0; j <= 25; j++) {
      if (i*7 + j*4 == n) {
        printf("Yes\n");
        return (0);
      }
    }
  }
  printf("No\n");
  return (0);
}