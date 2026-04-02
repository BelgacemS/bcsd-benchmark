#include <bits/stdc++.h>
using namespace std;
#define rep(i, n) for(int i=0; i< (int)(n); i++)
#define reps(i, n) for(int i=1; i<= (int)(n); i++)
#define rrep(i, s, n) for(int i = (s); i <(int) (n); i++)
#define all(v) v.begin(), v.end()
using ll = long long;
using ull = unsigned long long;
using vi = vector<int>;
using vs = vector<string>;
using vc = vector<char>;
using vb = vector<bool>;
using vll = vector<long long>;
using vvi = vector<vector<int>>;
using vvll = vector<vector<long long>>;
using vvs = vector<vector<string>>;
using vvc = vector<vector<char>>;
using vvb = vector<vector<bool>>;
using pii = pair<int,int>;
using vpii = vector<pair<int,int>>;
#define pb push_back
#define YesNo(b) cout << ((b) ? "Yes" : "No") << endl // Yes/No を出力する
#define YESNO(b) cout << ((b) ? "YES" : "NO") << endl // YES/NO を出力する

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    if(n%2==0) cout << n << endl;
    else cout << 2*n << endl;
}