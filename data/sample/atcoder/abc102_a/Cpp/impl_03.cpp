#include <bits/stdc++.h>
#include <atcoder/all>
using namespace std;
using namespace atcoder;
#ifdef __GNUC__
#pragma GCC target("avx2")
#pragma GCC optimize("O3")
#pragma GCC optimize("unroll-loops")
#endif
#define rep(i,n) for(int i=0;i<(int)(n);i++)
#define reps(i,a,n) for(int i=(a);i<(int)(n);i++)
#define repp(i,n) for(int i=(int)(n)-1;i>=0;i--)
#define all(v) v.begin(),v.end()
#define rall(v) v.rbegin(),v.rend()
#define Yes cout<<"Yes\n"
#define No cout<<"No\n"
#define YES cout<<"YES\n"
#define NO cout<<"NO\n"
#define spe " "
#define endl '\n'
#define pb push_back
#define vec vector
#define eb emplace_back
#define sor(v) sort(all(v))
#define rev(v) reverse(all(v))
#define rsor(v) sort(rall(v))
using ll=long long;
using ull=unsigned long long;
using i128=__int128_t;
using ld=long double;
using pii=pair<int,int>;
using pll=pair<ll,ll>;
using vi=vec<int>;
using vii=vec<vi>;
using vl=vec<ll>;
using vll=vec<vl>;
using vs=vec<string>;
using vss=vec<vs>;
using vc=vec<char>;
using vcc=vec<vc>;
using mint=modint998244353;
using mint7=modint1000000007;
const int INF=1e9;
const ll LINF=4e18;
const int dx[4]={1,0,-1,0};
const int dy[4]={0,1,0,-1};
int ri() {int n;cin>>n;return n;}
ll rii() {ll n;cin>>n;return n;}
double rd() {double n;cin>>n;return n;}
string rs() {string n;cin>>n;return n;}
char ss() {char n;cin>>n;return n;}

template<class T>
void print(const T& x){
    cout<<x<<'\n';
}

template<class T,class... Ts>
void print(const T& x,const Ts&... xs){
    cout<<x<<spe;
    print(xs...);
}

ll gcdll(ll a,ll b){
    return gcd(a,b);
}

ll lcmll(ll a,ll b){
    return a/gcd(a,b)*b;
}

void yesno(bool f){
    print(f?"Yes":"No");
}



void solve(){
    int n=ri();
    if(n%2==0) print(n);
    else print(2*n);
}

int main(void) {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t=1;
    //cin>>t;
    while(t--) solve();
    return 0;
}