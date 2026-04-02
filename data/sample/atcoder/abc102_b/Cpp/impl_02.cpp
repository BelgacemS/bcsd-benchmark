#include <bits/stdc++.h>
using namespace std;

int main() {

    int N;
    cin >> N;

    vector<int>A(N);
    for (int i = 0; i < N; i++) {
        cin >> A[i];
    }

    int ans = 0;

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (i != j) {
                ans = max(ans, abs(A[i] - A[j]));
           }
           
        }
    }

    cout << ans << endl;

}