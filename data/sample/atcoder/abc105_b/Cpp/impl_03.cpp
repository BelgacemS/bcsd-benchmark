#include <bits/stdc++.h>
using namespace std;
#define ll long long
#define rep(i,n) for(int i=0;i<n;i++)
int main() {
    int n;cin >> n;
    rep(i,21){
        rep(j,13){
            if(i*4+j*7 == n){
                cout << "Yes" << endl;
                return 0;
            }
        }
    }
    cout << "No" << endl;
}   