// https://atcoder.jp/contests/abc104/tasks/abc104_d
// Mon 02 Mar 2026 09:43:44 AM JST
#include <bits/stdc++.h>
using namespace std;
#include <atcoder/all>
using namespace atcoder;
// using mint = modint998244353;
using mint = modint1000000007;
// using vmint = vector<mint>;
// modint::set_mod(10);
// using mint = modint;
// #include <boost/multiprecision/cpp_int.hpp>
// using namespace boost::multiprecision;
// using int128 = int128_t;
#define all(v) (v).begin(), (v).end()
#define rall(v) (v).rbegin(), (v).rend()
#define rep(i, n) for (long long int i = 0; i < (n); ++i)
#define rep2(i, k, n) for (long long int i = (k); i < (n); ++i)
#define pb push_back
using ll = long long;
using vint = vector<int>;
using vll = vector<ll>;
using vvint = vector<vector<int>>;
using vvll = vector<vector<ll>>;

const ll INF = (ll)2e18 + 9;
// const int INF = (int)2e9 + 7;

template <typename T>
bool chmin(T& a, T b) {
    bool change = a > b;
    a = min(a, b);
    return change;
}
template <typename T>
bool chmax(T& a, T b) {
    bool change = a < b;
    a = max(a, b);
    return change;
}

template <typename T>
void print(vector<T> v) {
    int n = v.size();
    rep(i, n) {
        if (i == 0)
            cout << v[i];
        else
            cout << ' ' << v[i];
    }
    cout << endl;
}

template <typename T>
void vprint(vector<T> v) {
    for (auto x : v) cout << x << '\n';
}

void yesno(bool x) { cout << (x ? "Yes" : "No") << '\n'; }

void Yes() { yesno(true); }

void No() { yesno(false); }

// ceil(a/b)
ll ceil(ll a, ll b) { return (a + b - 1) / b; }

// floor(a/b)
ll floor(ll a, ll b) { return a / b; }

void solve();

int main() {
    solve();
    return 0;
}

void solve() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);

    string S;
    cin >> S;

    int N = S.size();

    vll la(N), lc(N), lq(N);
    vll ra, rc, rq;
    {
        rep(i, N) {
            if (S[i] == 'A') la[i]++;
            if (S[i] == 'C') lc[i]++;
            if (S[i] == '?') lq[i]++;
        }
        ra = la, rc = lc, rq = lq;

        reverse(all(ra));
        reverse(all(rc));
        reverse(all(rq));

        rep(i, N - 1) {
            la[i + 1] += la[i];
            lc[i + 1] += lc[i];
            lq[i + 1] += lq[i];
            ra[i + 1] += ra[i];
            rc[i + 1] += rc[i];
            rq[i + 1] += rq[i];
        }
        reverse(all(ra));
        reverse(all(rc));
        reverse(all(rq));
    }

    vector<mint> powthree(N);
    powthree[0] = 1;
    rep2(i, 1, N) {
        powthree[i] = powthree[i - 1] * 3;
    }

    mint ans = 0;
    rep2(i, 1, N - 1) {
        if (S[i] == 'B' || S[i] == '?') {
            mint l = la[i - 1] * powthree[lq[i - 1]];
            if (lq[i - 1])
                l += lq[i - 1] * powthree[lq[i - 1] - 1];

            mint r = rc[i + 1] * powthree[rq[i + 1]];
            if (rq[i + 1])
                r += rq[i + 1] * powthree[rq[i + 1] - 1];

            ans += r * l;
        }
    }

    cout << ans.val() << endl;
}
