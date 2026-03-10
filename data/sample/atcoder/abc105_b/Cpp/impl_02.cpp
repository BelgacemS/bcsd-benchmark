// 4 7
#include <bits/stdc++.h>

using namespace std;

int main()
{
    bool has_ans = false;

    int n, i, j; cin >> n;
    for (i=0; i<=n; i+=4)
    {
        if (n == i)
        {
            has_ans = true;
            cout << "Yes\n";
        }
    }

    for (i=0; (i<n)&&(!has_ans); i+=4)
    {
        for (j=i; j<=n; j+=7)
        {
            if (j == n)
            {
                has_ans = true;
                cout << "Yes\n";
            }
        }
    }

    if (!has_ans)
    {
        cout << "No\n";
    }


    return 0;
}
