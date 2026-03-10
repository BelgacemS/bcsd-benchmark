#[allow(unused)]
use proconio::input;
#[allow(unused)]
use proconio::marker::Chars;
#[allow(non_snake_case)]
fn main() {
    input! { r:usize }
    match r {
        0..=1199 => println!("ABC"),
        1200..=2799 => println!("ARC"),
        _ => println!("AGC")
    }
}
