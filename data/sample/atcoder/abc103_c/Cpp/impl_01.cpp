#include<bits/stdc++.h>
#define fast_io ios_base::sync_with_stdio(false);cin.tie(NULL)
using namespace std;
typedef vector<long long> vll;
typedef long long ll;
void init_code(){
    fast_io;
    #ifndef ONLINE_JUDGE
    freopen("input.txt","r",stdin);
    freopen("output.txt","w",stdout);
    #endif
}

vector<bool> prime_sieve(int n) {
    vector<bool> is_prime(n + 1, true);
    if (n >= 0) is_prime[0] = false;
    if (n >= 1) is_prime[1] = false;

    for (int i = 4; i <= n; i += 2)
        is_prime[i] = false;

    for (int i = 3; i * i <= n; i += 2) {
        if (is_prime[i]) {
            for (int p = i * i; p <= n; p += 2 * i)
                is_prime[p] = false;
        }
    }
    return is_prime;
} 
void display(vll v){
    for (ll i = 0; i < v.size(); i++)
    {
        cout<<v[i]<<" ";
   }
    cout<<endl;
 }


 void solve(){
    ll n,s=0;
    cin>>n;
    vll a(n);
    for(auto &it:a)cin>>it;
    for (int i = 0; i < n; ++i)
    {
        s+=a[i];
    }
    cout<<s-n<<endl;
}
 
signed main() {
    init_code();
    ios_base::sync_with_stdio(0); cin.tie(0);
    int ttt = 1;
    //cin>>ttt;
    while(ttt--) {
        solve();
    }
}