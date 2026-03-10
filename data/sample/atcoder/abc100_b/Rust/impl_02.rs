use proconio::{fastout, input};

#[fastout]
fn main() {
    input! {
        d: u32,
        n: u64,
    }
    let base = 100u64.pow(d);
    let mut ans = base;
    ans += base * (n - 1);
    if n == 100 {
        ans += base;
    }
    println!("{}", ans);
}
