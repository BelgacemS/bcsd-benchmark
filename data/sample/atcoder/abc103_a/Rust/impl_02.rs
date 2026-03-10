use proconio::{fastout, input};

#[fastout]
fn main() {
    input! {
        a: [u64; 3],
    }
    let ans = (a[0].abs_diff(a[1]) + a[1].abs_diff(a[2]))
        .min(a[2].abs_diff(a[0]) + a[1].abs_diff(a[2]))
        .min(a[1].abs_diff(a[0]) + a[0].abs_diff(a[2]))
        .min(a[1].abs_diff(a[2]) + a[2].abs_diff(a[0]))
        .min(a[2].abs_diff(a[0]) + a[0].abs_diff(a[1]))
        .min(a[2].abs_diff(a[1]) + a[1].abs_diff(a[0]));
    println!("{}", ans);
}
