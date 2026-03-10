#include <cstdio>
using namespace std;
int main() {
  int a, b;
  scanf("%d %d", &a, &b);
  if (a % b == 0) {
    printf("0\n");
  } else {
    printf("1\n");
  }
  return 0;
}