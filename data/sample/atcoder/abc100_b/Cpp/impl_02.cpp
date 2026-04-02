#include <bits/stdc++.h>
using namespace std;
using ll = long long;
using P = pair<int, int>;
const int INF = 1001001001;
#define rep(i, s, n) for (int i = (int)(s); i < (int)(n); i++)
#define ALL(obj) (obj).begin(), (obj).end()
template<class T> inline bool chmin(T& a, T b) { if (a > b) { a = b; return true; } return false; }
template<class T> inline bool chmax(T& a, T b) { if (a < b) { a = b; return true; } return false; }
struct Fast {Fast() {cin.tie(0); ios::sync_with_stdio(false);}} fast;

int main() {
    int D, N;
    cin >> D >> N;
    if(N == 100) N++;
    rep(i, 0, D) N *= 100;
    cout << N << '\n';
    
    return 0;
}