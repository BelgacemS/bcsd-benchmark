#[allow(unused_imports)]
use proconio::{input, marker::Chars};
fn main() {
    input! {
        d: usize,
        n: usize
    }
    let res = match d {
        0 => (1..102).filter(|&i| i != 100).collect::<Vec<usize>>(),
        1 => (1..102)
            .filter(|&i| i != 100)
            .map(|x| x * 100)
            .collect::<Vec<usize>>(),
        _ => (1..102)
            .filter(|&i| i != 100)
            .map(|x| x * 10000)
            .collect::<Vec<usize>>(),
    };
    println!("{}", res[n - 1]);
}
