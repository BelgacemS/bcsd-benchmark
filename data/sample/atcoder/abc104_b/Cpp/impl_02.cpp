#include <iostream>
using namespace std;
bool isz(char c) {
  if (c <= 'z' && c >= 'a') {
    return true;
  } else {
    return false;
  }
}
int main() {
  string s;
  cin >> s;
  bool f = true;
  if (s[0] != 'A') {
    f = false;
  }
  int s_c = 0;
  for (int i = 2; i < s.size() - 1; i++) {
    if (s[i] == 'C') {
      s_c++;
    }
  }
  if (s_c != 1) {
    f = false;
  }
  for (int i = 1; i < s.size(); i++) {
    bool ret = isz(s[i]);
    if (s[i] != 'C' && ret == false) {
      f = false;
      break;
    }
  }
  if (f == true) {
    cout << "AC\n";
  } else {
    cout << "WA\n";
  }
  return 0;
}