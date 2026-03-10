#[allow(unused_imports)]
use proconio::{input, marker::Chars};
fn main() {
    input! {
        n: usize,
        mut a: [usize; n]
    }
    let mut res = 0;
    for mut c in a {
        while c % 2 == 0 {
            c /= 2;
            res += 1;
        }
    }
    println!("{}", res);
}
