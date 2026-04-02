#include <bits/stdc++.h>
using namespace std;

int main() {
  int N, M;
  cin >> N >> M;
  vector<long> A(N + 1), S(N + 1);
  map<long, long> mod;
  for (int i = 1; i <= N; ++i) {
    cin >> A.at(i);
    S.at(i) = S.at(i - 1) + A.at(i);
    ++mod[S.at(i) % (long)M];
  }
  ++mod[0L];
  long cnt = 0;
  for (auto& m : mod) cnt += (m.second)*(m.second - 1) / 2;
  cout << cnt << endl;
  
  return 0;
}