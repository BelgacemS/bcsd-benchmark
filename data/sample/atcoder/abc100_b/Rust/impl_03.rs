use proconio::input;

fn main() {
    input! {
        d: u32, n: usize,
    }
    let n = if n == 100 { 101 } else { n };
    let ans = n * 100usize.pow(d);
    println!("{ans}");
}
