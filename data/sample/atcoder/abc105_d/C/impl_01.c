#include <stdio.h>
#include <sys/time.h>

#define N	100000

unsigned int X;

void srand_() {
	struct timeval tv;

	gettimeofday(&tv, NULL);
	X = tv.tv_sec ^ tv.tv_usec | 1;
}

int rand_() {
	return (X *= 3) >> 1;
}

void sort(int *aa, int l, int r) {
	while (l < r) {
		int i = l, j = l, k = r, a = aa[l + rand_() % (r - l)], tmp;

		while (j < k)
			if (aa[j] == a)
				j++;
			else if (aa[j] < a) {
				tmp = aa[i], aa[i] = aa[j], aa[j] = tmp;
				i++, j++;
			} else {
				k--;
				tmp = aa[j], aa[j] = aa[k], aa[k] = tmp;
			}
		sort(aa, l, i);
		l = k;
	}
}

int main() {
	static int aa[N + 1];
	int n, m, i, j;
	long long ans;

	srand_();
	scanf("%d%d", &n, &m);
	for (i = 1; i <= n; i++) {
		scanf("%d", &aa[i]);
		aa[i] = (aa[i] + aa[i - 1]) % m;
	}
	sort(aa, 0, n + 1);
	ans = 0;
	for (i = 0; i <= n; i = j) {
		j = i + 1;
		while (j <= n && aa[j] == aa[i])
			j++;
		ans += (long long) (j - i) * (j - i - 1) / 2;
	}
	printf("%lld\n", ans);
	return 0;
}