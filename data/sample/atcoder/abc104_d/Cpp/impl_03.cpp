#include<bits/stdc++.h>
using namespace std;

string s;
const int mod = 1e9+7;
int main() {
  ios::sync_with_stdio(0);
  cin.tie(0);
  cin >> s;
  long long cntA = 0,cntAB = 0,cntABC = 0;
  long long k = 1;
  for (auto c:s) {
    if (c == 'A') {
      (cntA += k) %= mod;
    } else if (c == 'B') {
      (cntAB += cntA) %= mod;  
    } else if (c == 'C') {
      (cntABC += cntAB) %= mod;
    } else {
      (cntABC *= 3)%= mod;
      (cntABC += cntAB) %= mod;
      (cntAB *= 3) %= mod;
      (cntAB += cntA) %= mod;
      (cntA *= 3) %= mod;
      (cntA += k) %= mod;
      (k *= 3) %= mod;
    }
  }
  cout << cntABC;
}