#include <bits/stdc++.h>
using namespace std;

int main() {
    string s,t;
    string b=s;
    cin >> s >> t;
    if(s == t){
        cout << "Yes\n";
        return 0;
    }
    for(int i=0;i<s.size()-1;i++){
        string a ="g";
        a[0]=s[s.size()-1];
        a+= s;
        a.erase(a.size()-1);
        s = a;
        if(s == t){
            cout << "Yes\n";
            return 0;
        }
    }
    if(s == t){
        cout << "Yes\n";
        return 0;
    }
    else{
        cout << "No\n";
        return 0;
    }
    return 0;
}
