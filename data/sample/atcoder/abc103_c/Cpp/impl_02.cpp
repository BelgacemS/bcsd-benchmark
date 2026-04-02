#include<iostream>
#include<iomanip>
#include<vector>
#include<unordered_map>
#include<unordered_set>
#include<deque>
#include<stack>
#include<algorithm>
#include<numeric>
#include<utility>
#include<limits>
using namespace std;
#define ll long long
#define dbg(x) cout<<#x<<' '<<x<<' '
#define all(x) x.begin(),x.end()
#define umap unordered_map
#define uset unordered_set
// #define MULCASE

void init(vector<int>& a) {
    for(auto& x: a) {
        cin>>x;
    }
}

void init(vector<ll>& a) {
    for(auto& x: a) {
        cin>>x;
    }
}

void print(const vector<vector<int>>& grid) {
    for(int i=0; i<grid.size(); i++) {
        for(int j=0; j<grid[i].size(); j++) {
            cout<<grid[i][j]<<' ';
        }
        cout<<endl;
    }
    // cout<<endl;
}

void print(const vector<int>& a) {
    for(int i=0; i<a.size(); i++) {
        cout<<a[i]<<' ';
    }
    cout<<endl;
}

void print(const vector<ll>& a) {
    for(int i=0; i<a.size(); i++) {
        cout<<a[i]<<' ';
    }
    cout<<endl;
}

void solve() {
    ll n;
    cin>>n;
    ll maxF=0;
    while(n--) {
        ll x;
        cin>>x;
        maxF+=(x-1);
    }
    cout<<maxF<<endl;
}

int main() {
    #ifdef MULCASE
    int t;
    cin>>t;
    while(t--)
    #endif
    solve();
    return 0;
}