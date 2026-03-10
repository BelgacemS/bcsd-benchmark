use proconio::input;

fn main() {
    input! {
        mut a: [usize; 3]
    }
    a.sort_unstable();
    let ans = a[2] - a[0];
    println!("{ans}");
}
