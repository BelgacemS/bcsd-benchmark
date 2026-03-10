#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <stdbool.h>
#include <limits.h>

#define ll long long
#define rp(i, k, n) for (int (i) = (k); (i) < (n); (i)++)
int min (int a, int b) { return a < b ? a : b; }

int main(void){
  int d, g, ans = INT_MAX;
	scanf("%d\n", &d);
	scanf("%d\n", &g);
	g /= 100;
	int p[d][2];
	rp(i, 0, d) scanf("%d %d", &p[i][0], &p[i][1]);
	rp(i, 0, d) p[i][1] /= 100;
	rp(b, 0, 1 << d) {
	  int sum = 0, cnt = 0;
	  rp(i, 0, d) {
  	  if ((b & 1 << i) != 0) {
  	    sum += p[i][0] * (i + 1) + p[i][1];
  	    cnt += p[i][0];
  	  }
	  }
	  if (sum >= g) {
	    ans = min(ans, cnt);
	    continue;
	  }
	  for (int i = d - 1; i >= 0; i--) {
  	  if ((b & 1 << i) == 0) {
  	    if (sum + (i + 1) * p[i][0] < g) {
  	      sum += (i + 1) * p[i][0];
  	      cnt += p[i][0];
  	    } else {
  	      cnt += (g - sum + i) / (i + 1);
  	      ans = min(ans, cnt);
  	      break;
  	    }
  	  }
	  }
	}
	printf("%d", ans);
	return 0;
}
