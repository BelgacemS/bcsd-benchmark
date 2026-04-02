#include <algorithm>
#include <iostream>
using namespace std;
int main() {
  int n, d;
  cin >> d >> n;
  int ans = 1;
  int k = n + (n - 1) / 99;
  for (int i = 1; i <= d; i++) {
    ans *= 100;
  }
  ans *= k;
  cout << ans << endl;
  return 0;
}