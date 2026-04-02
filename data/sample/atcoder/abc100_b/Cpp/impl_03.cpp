/**
 * @author      : Davi Guimarães
 * @problem     : 100B
 * @created     : 01/03/2026
 */

// chegou ao fundo do poço

#include <bits/stdc++.h>
using namespace std;

#define endl "\n"

int d, n;

int main(){
    cin.tie(0)->sync_with_stdio(0);
    cin >> d >> n;
    int x = 1;
    while(1){
        int cnt = 0, y = x;
        while(y % 100 == 0){
            y /= 100;
            cnt++;
        }
        if(cnt == d) n--;
        if(n == 0) break;
        x++;
    }
    cout << x << endl;
    return 0;
}

