#[allow(unused_imports)]
use proconio::{input, marker::Chars};
fn main() {
    input! {
        a: u8,
        b: u8
    }
    let res = if a <= 8 && b <= 8 { "Yay!" } else { ":(" };
    println!("{}", res);
}
