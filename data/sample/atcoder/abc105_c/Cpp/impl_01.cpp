#include <bits/stdc++.h>
using namespace std;
#define ll long long
#define rep(i,n) for(int i=0;i<n;i++)
int main() {
    ll n;cin >> n;
    if(n==0){
        cout << n << endl;
        return 0;
    }
    vector<int> a;
    while(n!=0){
        a.push_back(abs(n%2));
        n = n%2==0? n / (-2):(n-1)/(-2);
    }
    for(int i=0;i<a.size();i++){
        cout << a[a.size()-i-1];
    }
    cout << endl;
}