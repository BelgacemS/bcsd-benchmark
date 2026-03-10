/**
 * @author      : Davi Guimarães
 * @problem     : 100C
 * @created     : 01/03/2026
 */

// chegou ao fundo do poço

#include <bits/stdc++.h>
using namespace std;

#define endl "\n"

const int N = 1e4;
int n;
int a[N];

int main(){
    cin.tie(0)->sync_with_stdio(0);
    cin >> n;
    int ans = 0;
    for(int i = 0; i < n; i++){
        cin >> a[i];
        while(a[i] % 2 == 0){
            a[i] /= 2;
            ans++;
        }
    }
    cout << ans << endl;
    return 0;
}

