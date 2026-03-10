#include <bits/stdc++.h>
using namespace std;

bool isValid(string s) {
    int n = s.length();
    if (s[0] != 'A') return false;
    
    int ctC = 0;
    int cIdx = -1;
    for(int i=2;i<n-1;i++) {
        if (s[i] == 'C') {
            ctC++;
            cIdx = i;
        }
    }
    if (ctC > 1 || ctC == 0 ) return false;
    
    for(int i=1;i<n;i++) {
        if (i==cIdx) continue;
        if (s[i] >= 65 && s[i] <= 90) return false;
    }
    
    return true;

}

int main() {
    
    string s;
    cin>>s;
    if (isValid(s)) cout<<"AC";
    else cout<<"WA";
}