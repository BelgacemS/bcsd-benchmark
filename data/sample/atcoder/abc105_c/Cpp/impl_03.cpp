#include <bits/stdc++.h>
using namespace std;

string slv(int n) {
	if (!n) return "";
	if (abs(n) % 2 == 1) return slv((1 - n) / 2) + "1";
	return slv(-n / 2) + "0";
}

int main() {
	int n;
	cin >> n;
	if (n == 0) printf("0\n");
	else cout << slv(n) << endl;
	return 0;
} 