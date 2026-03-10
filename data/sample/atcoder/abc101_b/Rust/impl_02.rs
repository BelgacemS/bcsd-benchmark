#[allow(unused_imports)]
use proconio::{input, marker::Chars};
fn main() {
    input! {
        n: String
    }
    let mut cnt = 0;
    for c in n.chars() {
        cnt += c.to_digit(10).unwrap();
    }
    let res = if n.parse::<u32>().unwrap() % cnt == 0 {
        "Yes"
    } else {
        "No"
    };
    println!("{}", res);
}