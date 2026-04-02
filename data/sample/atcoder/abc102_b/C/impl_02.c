#include <stdio.h>
int main(void) {
  int n;
  scanf("%d",&n);
  int a[n];
  int min = 1000000001, max = -1;
  for (int i = 0; i < n; i++) {
    scanf("%d",&a[i]);
    if (min > a[i]) {
      min = a[i];
    }
    if (max < a[i]) {
      max = a[i];
    }
  }
  printf("%d\n",max-min);
  return (0);
}