#include <bits/stdc++.h>
using namespace std;

int N;
int A[210];

int main() {
    cin >> N;
    for(int i = 0; i < N; i++) {
        cin >> A[i]; 
    }
    int gap;
    int gap_max = -1;

    for(int i = 0; i < N; i++) {
        for(int j = 0; j < N; j++) {
            gap = abs(A[i] - A[j]);
            if(gap_max < gap) gap_max = gap;
        }
    }
    cout << gap_max << endl;
}