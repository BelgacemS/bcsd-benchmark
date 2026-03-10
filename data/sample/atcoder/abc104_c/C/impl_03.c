#include <stdio.h>

#define N	10
#define INF	0x3f3f3f3f

int min(int a, int b) { return a < b ? a : b; }

int main() {
	static int pp[N], cc[N];
	int n, s_, b, i, s, p, p_;

	scanf("%d%d", &n, &s_), s_ /= 100;
	for (i = 0; i < n; i++)
		scanf("%d%d", &pp[i], &cc[i]), cc[i] /= 100;
	p_ = INF;
	for (b = 0; b < 1 << n; b++) {
		s = 0, p = 0;
		for (i = 0; i < n; i++)
			if ((b & 1 << i) != 0)
				s += pp[i] * (i + 1) + cc[i], p += pp[i];
		if (s >= s_) {
			p_ = min(p_, p);
			continue;
		}
		for (i = n - 1; i >= 0; i--)
			if ((b & 1 << i) == 0) {
				if (s + pp[i] * (i + 1) < s_)
					s += pp[i] * (i + 1), p += pp[i];
				else {
					p += (s_ - s + i) / (i + 1);
					p_ = min(p_, p);
					break;
				}
			}
	}
	printf("%d\n", p_);
	return 0;
}