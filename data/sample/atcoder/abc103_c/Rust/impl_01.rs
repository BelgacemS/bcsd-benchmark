use proconio::{fastout, input};

#[fastout]
fn main() {
    input! {
        n: usize,
        a: [u64; n],
    }
    let mut ans = 0;
    for &ai in &a {
        ans += ai - 1;
    }

    println!("{}", ans);
}
