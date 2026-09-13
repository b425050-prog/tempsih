#include <bits/stdc++.h>
using namespace std;

using i64 = long long;

const i64 MOD = 998244353;
const int MAXN = 200000;

i64 fact[MAXN + 1];
i64 inv[MAXN + 1];

void precompute() {
    fact[0] = 1;

    for (int i = 1; i <= MAXN; i++) {
        fact[i] = fact[i - 1] * i % MOD;
    }

    inv[1] = 1;

    for (int i = 2; i <= MAXN; i++) {
        inv[i] = MOD - (MOD / i) * inv[MOD % i] % MOD;
    }
}

void solve() {
    int n;
    cin >> n;

    vector<i64> a(n);

    for (auto &x : a)
        cin >> x;

    if (n == 1) {
        cout << 0 << '\n';
        return;
    }

    sort(a.begin(), a.end());

    vector<i64> suf(n + 1, 0);

    for (int i = n - 1; i >= 0; i--) {
        suf[i] = (suf[i + 1] + a[i]) % MOD;
    }

    i64 totalTrees = fact[n - 1];

    i64 ans = 0;

    for (int i = 0; i < n - 1; i++) {

        i64 cnt = n - i - 1;

        // sum_{j > i} (a[j] - a[i])
        i64 diffSum =
            (suf[i + 1] - (cnt % MOD) * (a[i] % MOD)) % MOD;

        if (diffSum < 0)
            diffSum += MOD;

        // (n-1)! / cnt
        i64 ways = totalTrees * inv[cnt] % MOD;

        ans = (ans + ways * diffSum) % MOD;
    }

    cout << ans << '\n';
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    precompute();

    int t;
    cin >> t;

    while (t--)
        solve();

    return 0;
}
