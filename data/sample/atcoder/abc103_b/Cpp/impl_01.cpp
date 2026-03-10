#include <iostream>
#include <deque>
using namespace std;

void solve() {
    string s, r;
    cin >> s >> r;

    if (s.size() != r.size()) {
        cout << "No";
        return;
    }

    if (s == r) {
        cout << "Yes";
        return;
    }

    deque<char> ds(s.begin(), s.end());

    for (int i = 0; i < s.size(); i++) {
        char c = ds.front();
        ds.pop_front();
        ds.push_back(c);

        bool match = true;
        for (int j = 0; j < ds.size(); j++) {
            if (ds[j] != r[j]) {
                match = false;
                break;
            }
        }
        if (match) {
            cout << "Yes";
            return;
        }
    }

    cout << "No";
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    solve();
}