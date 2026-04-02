#include <stdio.h>
#include <string.h>

#define N	100000
#define MD	1000000007

int main() {
	static char cc[N + 1];
	static int dp[4];
	int n, i, a;

	scanf("%s", cc), n = strlen(cc);
	dp[0] = 1;
	for (i = 0; i < n; i++)
		for (a = 3; a >= 0; a--) {
			if (a < 3 && (cc[i] == a + 'A' || cc[i] == '?'))
				dp[a + 1] = (dp[a + 1] + dp[a]) % MD;
			if (cc[i] == '?')
				dp[a] = (long long) dp[a] * 3 % MD;
		}
	printf("%d\n", dp[3]);
	return 0;
}