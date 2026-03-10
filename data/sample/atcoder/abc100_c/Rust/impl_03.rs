use proconio::input;

fn main() {
    input! {
        n: usize,
        a: [usize; n],
    }

    let ans = a.iter().map(|&a| a.trailing_zeros()).sum::<u32>();
    println!("{ans}");
}
