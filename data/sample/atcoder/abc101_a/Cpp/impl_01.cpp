#include <bits/stdc++.h>
using namespace std;
int main(){
	char a , b, c, d;
	int sum = 0 ;
	cin >> a >> b >> c >> d;
	if(a == '+') {
		sum++;
	}
	else {
		sum--;
	}
	if(b == '+') {
		sum++;
	}
	else {
		sum--;
	}
	if(c == '+') {
		sum++;
	}
	else {
		sum--;
	}
	if(d == '+') {
		sum++;
	}
	else {
		sum--;
	}
	cout << sum;
	return 0;
}
