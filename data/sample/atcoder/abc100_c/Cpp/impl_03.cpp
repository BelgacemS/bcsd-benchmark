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
    int N;
    cin >> N;
    // 2の倍数の数だけ見ればいい
    int ans = 0;
    rep(i, 0, N) {
        int a;
        cin >> a;
        while(a%2 == 0){
            ans++;
            a /= 2;
        }
    }
    cout << ans << '\n';
    return 0;
}