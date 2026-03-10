use proconio::{fastout, input, marker::Bytes};

#[fastout]
fn main() {
    input! {
        s: Bytes
    }
    let mut ans = 0;
    for &c in &s {
        if c == b'+' {
            ans += 1;
        } else {
            ans -= 1;
        }
    }

    println!("{}", ans);
}
