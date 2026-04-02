#include <bits/stdc++.h>
#include <cstdlib>
 
#define ll long long 
#define i64 long long
using i128 = __int128;

std::istream& operator>>(std::istream& iss, i128& n) {
    std::string s;
    iss >> s;
    n = 0;

    for (int i = (s[0] == '-'); i < s.size(); i++) {
        n = n * 10 + (s[i] - '0');
    }

    if (s[0] == '-') n = -n;
    return iss;
}

std::ostream& operator<<(std::ostream& oss, i128 n) {
    if (n == 0) return oss << "0";

    std::string s;
    if (n < 0) {
        s += '-';
        n = -n;
    }

    while (n) {
        s += '0' + n % 10;
        n /= 10;
    }

    std::reverse(s.begin() + (s[0] == '-'), s.end());
    return oss << s;
}

static const long long pow2[] = { 
    1LL, 2LL, 4LL, 8LL, 16LL, 32LL, 64LL, 128LL, 256LL, 512LL, 1024LL, 2048LL, 4096LL, 8192LL, 16384LL, 32768LL, 65536LL, 131072LL, 262144LL, 524288LL, 1048576LL, 2097152LL, 4194304LL, 8388608LL, 16777216LL, 33554432LL, 67108864LL, 134217728LL, 268435456LL, 536870912LL, 1073741824LL, 2147483648LL, 4294967296LL, 8589934592LL, 17179869184LL, 34359738368LL, 68719476736LL, 137438953472LL, 274877906944LL, 549755813888LL, 1099511627776LL, 2199023255552LL, 4398046511104LL, 8796093022208LL, 17592186044416LL, 35184372088832LL, 70368744177664LL, 140737488355328LL, 281474976710656LL, 562949953421312LL, 1125899906842624LL, 2251799813685248LL, 4503599627370496LL, 9007199254740992LL, 18014398509481984LL, 36028797018963968LL, 72057594037927936LL, 144115188075855872LL, 288230376151711744LL, 576460752303423488LL
};
static const long long pow3[] = {
    1LL, 3LL, 9LL, 27LL, 81LL, 243LL, 729LL, 2187LL, 6561LL, 19683LL, 59049LL, 177147LL, 531441LL, 1594323LL, 4782969LL, 14348907LL, 43046721LL, 129140163LL, 387420489LL, 1162261467LL, 3486784401LL, 10460353203LL, 31381059609LL, 94143178827LL, 282429536481LL, 847288609443LL, 2541865828329LL, 7625597484987LL, 22876792454961LL, 68630377364883LL, 205891132094649LL, 617673396283947LL, 1853020188851841LL, 5559060566555523LL, 16677181699666569LL, 50031545098999707LL, 150094635296999121LL, 450283905890997363LL
};
static const long long pow5[] = {
    1LL, 5LL, 25LL, 125LL, 625LL, 3125LL, 15625LL, 78125LL, 390625LL, 1953125LL, 9765625LL, 48828125LL, 244140625LL, 1220703125LL, 6103515625LL, 30517578125LL, 152587890625LL, 762939453125LL, 3814697265625LL, 19073486328125LL, 95367431640625LL, 476837158203125LL, 2384185791015625LL, 11920928955078125LL, 59604644775390625LL, 298023223876953125LL, 1490116119384765625LL
};
static const long long pow10[] = {
    1LL, 10LL, 100LL, 1000LL, 10000LL, 100000LL, 1000000LL, 10000000LL, 100000000LL, 1000000000LL, 10000000000LL, 100000000000LL, 1000000000000LL, 10000000000000LL, 100000000000000LL, 1000000000000000LL, 10000000000000000LL, 100000000000000000LL, 1000000000000000000LL
};

using namespace std;
#include <ext/pb_ds/assoc_container.hpp>
#include <ext/pb_ds/tree_policy.hpp>
#include <ext/pb_ds/detail/standard_policies.hpp>

using namespace __gnu_pbds;
typedef tree<int, null_type, less<int>, rb_tree_tag, tree_order_statistics_node_update> ordered_set;
typedef tree<std::pair<int, int>, null_type, less<std::pair<int, int>>, rb_tree_tag, tree_order_statistics_node_update> ordered_set_pair;

typedef tree<i64, null_type, less<i64>, rb_tree_tag, tree_order_statistics_node_update> ordered_set_64;
typedef tree<std::pair<i64, i64>, null_type, less<std::pair<i64, i64>>, rb_tree_tag, tree_order_statistics_node_update> ordered_set_pair_64;

const i64 MOD1 = 1e9 + 7;
const i64 MOD2 = 998244353;
const i64 LARGE = 1e17;

struct Kosaraju {
    // for the scc graph
    i64 idx = 1;
    std::map<i64, i64> scc_idx;
    std::map<i64, std::vector<i64>> scc_comp;
    std::vector<std::vector<i64>> scc_edges;
    std::vector<i64> in, out;

    // for toposort
    std::vector<i64> start, finish, toposort;

    Kosaraju(
        i64 n, 
        std::vector<std::vector<i64>> adj
    ) {
        std::vector<std::vector<i64>> adjr(n + 1);
        for (int i = 1; i <= n; i++) {
            for (auto u: adj[i]) {
                adjr[u].push_back(i);
            }
        }

        start.resize(n + 1, 0LL);
        finish.resize(n + 1, 0LL);
        std::vector<bool> vis(n + 1, false);
        i64 timer = 1;

        std::function<void(i64)> dfs = [&] (i64 u) -> void {
            start[u] = timer++;
            vis[u] = true;
            for (auto v: adj[u]) {
                if (vis[v]) continue;
                dfs(v);
            }
            finish[u] = timer++;
            toposort.push_back(u);
            return;
        };

        for (int i = 1; i <= n; i++) {
            if (vis[i]) continue;
            dfs(i);
        }
 
        std::reverse(toposort.begin(), toposort.end());
        for (int i = 1; i <= n; i++) {
            vis[i] = false;
        }

        std::function<void(i64)> dfsr = [&] (i64 u) -> void {
            vis[u] = true;
            scc_idx[u] = idx;
            scc_comp[idx].push_back(u);
            for (auto v: adjr[u]) {
                if (vis[v]) continue;
                dfsr(v);
            }
            return;
        };
    
        for (auto u: toposort) {
            if (vis[u]) continue;
            dfsr(u);
            idx++;
        }
    }

    void construct(const std::map<std::array<i64, 2>, bool>& edges) {
        in.resize(idx);
        out.resize(idx);
        scc_edges.resize(idx);

        for (auto [u, v]: edges) {
            i64 l1 = scc_idx[u[0]];
            i64 l2 = scc_idx[u[1]];
            if (l1 == l2) continue;
            out[l1]++;
            in[l2]++;
            scc_edges[l1].push_back(l2);
        }
    }
};

struct DSU {
    std::vector<i64> par, sz;
    DSU(i64 n) {
        par.resize(n + 1, 0LL); 
        sz.resize(n + 1, 1LL);
        for (int i = 1; i <= n; i++) {
            par[i] = i;
        }
    }

    i64 find(i64 x) {
        while (x != par[x]) {
            x = par[x] = par[par[x]];
        }
        return x;
    }

    i64 size(i64 x) {
        x = find(x);
        return sz[x];
    }

    bool same(i64 x, i64 y) {
        return find(x) == find(y);
    }

    bool merge(i64 x, i64 y) {
        x = find(x); y = find(y);
        if (x == y) return false;
        if (sz[x] < sz[y]) std::swap(x, y);
        par[y] = x;
        sz[x] += sz[y];
        return true;
    }
};

const i64 SIEVE_MAX = 1e9;
const i64 SIEVE_SQRT = 1e7 + 1;

i64 lp[SIEVE_SQRT + 1];
std::vector<i64> prs;

void init_sieve() {
    for (i64 i = 2; i <= SIEVE_SQRT; i++) {
        if (lp[i] == 0) {
            lp[i] = i;
            prs.push_back(i);
        }
        for (i64 j = 0; i * prs[j] <= SIEVE_SQRT; j++) {
            lp[i * prs[j]] = prs[j];
            if (prs[j] == lp[i]) break;
        }
    }
}

i64 binpow(i64 x, i64 y,i64 m) {
    x %= m;
    i64 result = 1;

    while (y > 0) {
        if (y & 1) result = result * x % m;
        x = x * x % m;
        y >>= 1;
    }

    result %= m;
    return result;
}

i64 modinv(i64 x, i64 p) {
    return binpow(x, p - 2, p);
}

template <i64 Z>
struct modint {
private:
    i64 norm(i64 x_val) {
        if (x_val < 0) {
            x_val += Z;
        }
        if (x_val >= Z) {
            x_val -= Z;
        }
        return x_val;
    }
    i64 power(i64 a, i64 b) const {
        i64 res = 1;
        for (; b; b /= 2, a = (a * a) % Z) {
            if (b % 2) {
                res = (res * a) % Z;
            }
        }
        return res;
    }

public:
    i64 x; // the actual number

    // modint constructors
    modint(): x(0) {}
    modint(i64 x_val): x(norm(x_val % Z)) {} 

    // modint functions
    // 1. unary negative
    modint operator-() const {
        return modint(norm(Z - x));
    }
    // 2. operation assignment
    modint& operator+=(const modint& other) {
        x = norm(x + other.x);
        return *this;
    }
    modint& operator-=(const modint& other) {
        x = norm(x - other.x);
        return *this;
    }
    modint& operator*=(const modint& other) {
        x = (x * other.x) % Z;
        return *this;
    }
    // 3. modular inverse
    modint inv() const {
        return modint(power(x, Z - 2));
    }
    modint& operator/=(const modint& other) {
        x = (x * other.inv().x) % Z;
        return *this;
    }
    // 4. binary operators
    friend modint operator+(modint first, const modint& second) {
        first += second;
        return first;
    }
    friend modint operator-(modint first, const modint& second) {
        first -= second;
        return first;
    }
    friend modint operator*(modint first, const modint& second) {
        first *= second;
        return first;
    }
    friend modint operator/(modint first, const modint& second) {
        first /= second;
        return first;
    }
    // 5. stream operators
    friend std::istream& operator>>(std::istream& iss, modint& a) {
        i64 result;
        iss >> result;
        a = modint(result);
        return iss;
    }
    friend std::ostream& operator<<(std::ostream& oss, const modint& a) {
        return oss << a.x;
    }
};

using z1 = modint<MOD1>;
using z2 = modint<MOD2>;

template <typename T>
struct MatrixExpo {
/**
    everything is 1-indexed
    n -> size of matrix is n x n
    mod -> optional => used to perform operations modulo mod
    expo -> compute the xth power of the matrix
 */

public:
    i64 n;
    i64 mod = -1;
    std::vector<std::vector<T>> matrix;

    MatrixExpo(std::vector<std::vector<T>>& vec, i64 n): 
        n(n), matrix(vec) {}

    MatrixExpo(std::vector<std::vector<T>>& vec, i64 n, i64 mod):
        n(n), matrix(vec), mod(mod) {}

    // normal matrix multiplication (supports both mod and non mod)
    std::vector<std::vector<T>> multiply(const std::vector<std::vector<T>>& a, 
                                        const std::vector<std::vector<T>>& b) {
        std::vector<std::vector<T>> result(n + 1, std::vector<T>(n + 1, 0));
        
        for (i64 i = 1; i <= n; i++) {
            for (i64 j = 1; j <= n; j++) {
                T sum = 0;
                for (i64 k = 1; k <= n; k++) {
                    if (mod == -1) {
                        sum += a[i][k] * b[k][j];
                    } else {
                        sum = (sum + a[i][k] * b[k][j]) % mod;
                    }
                }
                result[i][j] = sum;
            }
        }
        return result;
    }

    // generate the identity matrix
    std::vector<std::vector<T>> identity() {
        std::vector<std::vector<T>> id(n + 1, std::vector<T>(n + 1, 0));
        for (i64 i = 1; i <= n; i++) {
            id[i][i] = 1;
        }
        return id;
    }
    
    // fast matrix exponentiation
    std::vector<std::vector<T>> expo(i64 x) {
        std::vector<std::vector<T>> result = identity();
        std::vector<std::vector<T>> base = matrix;

        while (x) {
            if (x & 1) {
                result = multiply(result, base);
            }
            base = multiply(base, base);
            x >>= 1;
        }
        return result;
    }
};

struct StringHash {
    i64 B;
    static const i64 MOD = (1LL << 61) - 1;

    int n;
    string s;
    vector<i64> pow, hash1;

    StringHash(const string &str) {
        s = str;
        n = s.size();
        pow.resize(n + 1);
        hash1.resize(n + 1);

        static mt19937_64 rng(chrono::steady_clock::now().time_since_epoch().count());
        static uniform_int_distribution<i64> dist(256, 1000000000);
        static i64 global_base = dist(rng);
        B = global_base;

        pow[0] = 1;
        for (int i = 1; i <= n; ++i)
            pow[i] = modmul(pow[i - 1], B);

        for (int i = 0; i < n; ++i)
            hash1[i + 1] = modadd(modmul(hash1[i], B), s[i]);
    }

    static i64 modmul(i64 a, i64 b) {
        __int128_t t = (__int128_t)a * b;
        t = (t >> 61) + (t & MOD);
        if (t >= MOD) t -= MOD;
        return (i64)t;
    }

    static i64 modadd(i64 a, i64 b) {
        i64 res = a + b;
        if (res >= MOD) res -= MOD;
        return res;
    }

    i64 get_hash(int l, int r) const {
        i64 val = hash1[r + 1] + MOD - modmul(hash1[l], pow[r - l + 1]);
        if (val >= MOD) val -= MOD;
        return val;
    }

    i64 get_suffix_hash(int len) const {
        if (len > n) return -1;
        return get_hash(n - len, n - 1);
    }

    static bool equal_suffix(const StringHash &A, const StringHash &B, int len) {
        if (len > A.n || len > B.n) return false;
        return A.get_suffix_hash(len) == B.get_suffix_hash(len);
    }
};

struct Factorise {
    // usage: 
    /**
        int n; std::cin >> n;
        std::vector<int> a(n + 1);
        for (int i = 1; i <= n; i++) std::cin >> a[i];

        Factorise f(n, a);
     */
    int n;
    std::vector<int>& a;
    std::set<int> primes; // set of all primes that divide atleast someone in the list
    std::vector<std::vector<int>> factors; // list of prime factors for each element in the list
    std::vector<std::vector<int>> powers; // list of prime powers for each factor of element
    std::vector<std::map<int, int>> mp; // prime to index mapping for element

    Factorise(int n, std::vector<int>& a): n(n), a(a) {
        factors.resize(n + 1);
        powers.resize(n + 1);
        mp.resize(n + 1); 
        a = a; factorise();
    } 

    void factorise() {
        int max_val = 0;
        for (int i = 1; i <= n; i++) {
            max_val = std::max(max_val, a[i]);
        }

        if (max_val > SIEVE_SQRT) return;
        for (int i = 1; i <= n; i++) {
            int temp = a[i];
            while (temp > 1) {
                int p = lp[temp];
                int cnt = 0LL;
                while (temp % p == 0) {
                    temp /= p;
                    cnt++;
                }
                factors[i].push_back(p);
                powers[i].push_back(cnt);
                mp[i][p] = cnt;
                primes.insert(p);
            }
        }
    }
};

void solve() {
    i64 n;
    std::cin >> n;

    std::vector<char> ans;
    while (n != 0) {
        i64 r = n % -2;
        if (r < 0) {
            r += 2;
            n = (n - r) /- 2;
        } else {
            n /= -2;
        }
        ans.push_back('0' + r);
    }

    if (ans.size() == 0) ans.push_back('0');
    std::reverse(ans.begin(), ans.end());
    for (auto u: ans) {
        std::cout << u;
    }
}

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(0);

    int t = 1;
    // std::cin >> t;

    // init_sieve();
    
    bool print_tc = false;
    int T = 9330; // number of tests you want to debug
    int L = 79; // test number you want to debug

    for (int test = 1; test <= t; test++) {
        if (print_tc && t == T) {
            i64 n;
            std::cin >> n;

            i64 a[n + 1];
            for (int i = 1; i <= n; i++) {
                std::cin >> a[i];
            }

            if (test == L) {
                // print the test;
                std::cout << n << '\n';
                for (int i = 1; i <= n; i++) {
                    std::cout << a[i] << " \n"[i == n];
                }
            }
            continue;
        }

        solve();
    }

    // iterative segment tree
    // ll tree[2 * n + 3];
    // for (ll i = 1; i <= n; i++) tree[n + i - 1] = a[i];

    // for (ll i = n - 1; i > 0; i--) tree[i] = tree[i << 1] + tree[i << 1 | 1];

    // auto query = [&] (ll l_, ll r_) -> ll {
    //     ll res = 0;
    //     for (l_ += n - 1, r_ += n - 1; l_ < r_; l_ >>= 1, r_ >>= 1){
    //         if (l_&1) res += tree[l_++];
    //         if (r_&1) res += tree[--r_];
    //     }
    //     return res;
    // };

    // auto update = [&] (ll ind, ll val) -> void {
    //     for (tree[ind += n - 1] += val; ind > 1; ind >>= 1) tree[ind >> 1] = tree[ind] + tree[ind ^ 1];
    // };
}
