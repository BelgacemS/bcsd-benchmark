#[allow(unused_imports)]
use proconio::{input, marker::Chars};
fn main() {
    input! {
        n: usize,
        mut a: [usize; n]
    }
    let res = a.iter().max().unwrap() - a.iter().min().unwrap();
    println!("{}", res);
}
