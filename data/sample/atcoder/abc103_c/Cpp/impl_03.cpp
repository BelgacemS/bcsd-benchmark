#include<bits/stdc++.h>
using namespace std;
#define ll long long

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr); 
    cout.tie(nullptr); 
    
    int n;
    cin >> n;
    ll ans = 0;
    for(int i = 0 ; i < n;i++){
        int num;
        cin >> num;
        ans += num-1;
    }
    cout << ans << endl;

    return 0;

}

