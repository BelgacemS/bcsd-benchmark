use proconio::{fastout, input};

#[fastout]
fn main() {
    input! {
        n: usize,
        m: usize,
        mut ab: [(usize, usize); m],
    }
    ab.sort();
    let mut l = 0;
    let mut r = 0;
    let mut ans = 0;
    for &(a, b) in &ab {
        if r <= a {
            ans += 1;
            l = a;
            r = b;
        } else if l <= a && b <= r {
            l = a;
            r = b;
        } else if l <= a && r < b {
            l = a;
        }
    }

    println!("{}", ans);
}
