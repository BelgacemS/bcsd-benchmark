#[allow(unused_imports)]
use proconio::{input, marker::Chars};
fn main() {
    input! {
        s: Chars
    }
    let res: isize = s.iter().filter(|&&x| x == '+').count() as isize
        - s.iter().filter(|&&x| x == '-').count() as isize;
    println!("{}", res);
}
