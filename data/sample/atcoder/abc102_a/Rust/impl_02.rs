use num_integer::lcm;
#[allow(unused_imports)]
use proconio::{input, marker::Chars};
fn main() {
    input! {
        n: isize
    }
    println!("{}", lcm(2, n));
}
