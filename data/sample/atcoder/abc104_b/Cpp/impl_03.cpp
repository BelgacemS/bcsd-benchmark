#include <bits/stdc++.h>
using namespace std;

#define int long long
#define double long double

signed main()
{
    string S;
    cin >> S;

    if (S[0] != 'A') {
        cout << "WA";
        return 0;
    }

    int cnt = 0;
    int sum = 0;

    for (int i = 2; i < S.length() - 1; i++) {
        if (S[i] == 'C') {
            cnt++;
            sum = i;
        }
    }

    if (cnt != 1) {
        cout << "WA";
        return 0;
    }

    for (int i = 1; i < S.length(); i++) {
        if (i == sum) continue;

        if (S[i] < 'a' || S[i] > 'z') {
            cout << "WA";
            return 0;
        }
    }

    cout << "AC";
}