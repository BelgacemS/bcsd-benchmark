#include <stdio.h>

#define HASH 1000003
const int H_Mod = HASH;

typedef struct List {
	struct List *next;
	int v, num;
} list;

int main()
{
	int i, N, M, A[100001];
	scanf("%d %d", &N, &M);
	for (i = 1; i <= N; i++) scanf("%d", &(A[i]));
	
	int hn = 0, h, sum = 0;
	list *hash[HASH] = {}, hd[100001], *hp;
	hd[hn].v = sum;
	hd[hn].num = 1;
	hd[hn].next = hash[0];
	hash[0] = &(hd[hn++]);
	for (i = 1; i <= N; i++) {
		sum += A[i];
		sum %= M;
		h = sum % H_Mod;
		for (hp = hash[h]; hp != NULL; hp = hp->next) if (hp->v == sum) break;
		if (hp != NULL) hp->num++;
		else {
			hd[hn].v = sum;
			hd[hn].num = 1;
			hd[hn].next = hash[h];
			hash[h] = &(hd[hn++]);
		}
	}
	
	long long ans = 0;
	for (i = 0; i < hn; i++) ans += (long long)hd[i].num * (hd[i].num - 1) / 2;
	printf("%lld\n", ans);
	fflush(stdout);
	return 0;
}