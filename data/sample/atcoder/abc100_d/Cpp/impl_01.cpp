#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
const ll INF = 1e18;

ll read()
{
	ll x = 0, f = 1;
	char ch = getchar();
	while (ch < '0' || ch > '9')
	{
		if (ch == '-')
		{
			f = -1;
		}
		ch = getchar();
	}
	while (ch >= '0' && ch <= '9')
	{
		x = (x << 3) + (x << 1) + ch - '0';
		ch = getchar();
	}
	return x * f;
}

const ll N = 2e5;

struct node
{
	ll x, y, z;
	bool operator<(const node &cmp)const
	{
		return x + y + z > cmp.x + cmp.y + cmp.z;
	}
} a[N + 5], b[N + 5];

ll h[8][3] = {{1, 1, 1}, {1, 1, -1}, {1, -1, 1}, { -1, 1, 1}, { -1, -1, 1}, { -1, 1, -1}, {1, -1, -1}, { -1, -1, -1}};

int main()
{
	ll n = read(), m = read();
	for (ll i = 1; i <= n; i++)
	{
		a[i].x = read(), a[i].y = read(), a[i].z = read();
	}
	ll maxx = -INF;
	for (ll i = 0; i < 8; i++)
	{
		for (ll j = 1; j <= n; j++)
		{
			b[j].x = a[j].x * h[i][0];
			b[j].y = a[j].y * h[i][1];
			b[j].z = a[j].z * h[i][2];
		}
		sort(b + 1, b + n + 1);
		ll ans = 0;
		for (ll j = 1; j <= m; j++)
		{
			ans += (b[j].x + b[j].y + b[j].z);
		}
		maxx = max(maxx, ans);
	}
	cout << maxx << endl;
	return 0;
}