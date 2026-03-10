use proconio::input;
use std::collections::HashMap;

fn main() {
    input! {
        n: usize,
        m: usize,
        a: [usize; n],
    }

    let mut s = vec![0; n + 1];
    for i in 0..n {
        s[i + 1] = s[i] + a[i];
        s[i + 1] %= m;
    }

    let mut map: HashMap<usize, usize> = HashMap::new();
    for &s_i in &s {
        *map.entry(s_i).or_insert(0) += 1;
    }

    let mut ans: usize = 0;
    for &cnt in map.values() {
        ans += cnt * (cnt - 1) / 2;
    }

    println!("{}", ans);
}
