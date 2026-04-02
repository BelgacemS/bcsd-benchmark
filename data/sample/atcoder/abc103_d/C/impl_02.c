#include <stdio.h>
#include <stdlib.h>

typedef struct _islands
{
	int start;
	int end;
} islands;

islands a[100000];

int compar(const void *p1, const void *p2)
{
	return ((islands *)p1)->end - ((islands *)p2)->end;
}

int main(void)
{
	int n, m, i, count = 1;
	islands temp;
	scanf("%d%d", &n, &m);

	for (i = 0; i < m; i++)
		scanf("%d%d", &(a[i].start), &(a[i].end));

	qsort(a, m, sizeof(islands), compar);
	
	temp = a[0];
	for (i = 1; i < m; i++)
	{
		if (a[i].start >= temp.end)
		{
			temp = a[i];
			count++;
		}
	}
	printf("%d\n", count);
	return 0;
}