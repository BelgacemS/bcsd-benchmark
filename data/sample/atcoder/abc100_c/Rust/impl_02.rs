use proconio::{fastout, input};

#[fastout]
fn main() {
    input! {
        n: usize,
    }
    let mut ans = 0;
    for _ in 0..n {
        input! {
            mut a: u64,
        }
        while a % 2 == 0 {
            a /= 2;
            ans += 1;
        }
    }

    println!("{}", ans);
}
