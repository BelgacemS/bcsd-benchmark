#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <stdbool.h>
#include <limits.h>

#define ll long long
#define rp(i, k, n) for (int (i) = (k); (i) < (n); (i)++)
int max (int a, int b) { return a > b ? a : b; }
int min (int a, int b) { return a < b ? a : b; }

typedef struct {
  ll l;
  ll r;
} br;
int cmp(const void* a, const void* b) {
  return ((br*)a)->r - ((br*)b)->r;
}
int main(void){
  ll n, m, ans = 0, bef = -1;
  scanf("%lld %lld\n", &n, &m);
  br x[m];
  rp(i, 0, m) scanf("%lld %lld", &x[i].l, &x[i].r);
  qsort(x, m, sizeof(br), cmp);
  rp(i, 0, m) {
    if (bef == -1 || bef <= x[i].l) {
      ans++;
      bef = x[i].r;
    }
  }
  printf("%lld\n", ans);
	return 0;
}
