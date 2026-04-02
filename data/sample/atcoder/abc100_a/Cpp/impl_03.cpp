/**
 * @author      : Davi Guimarães
 * @problem     : 100A
 * @created     : 01/03/2026
 */

// chegou ao fundo do poço

#include <bits/stdc++.h>
using namespace std;

#define endl "\n"

int a, b;

int main(){
    cin.tie(0)->sync_with_stdio(0);
    cin >> a >> b;
    if(a <= 8 && b <= 8){
        cout << "Yay!" << endl;
    }
    else cout << ":(" << endl;
    return 0;
}

