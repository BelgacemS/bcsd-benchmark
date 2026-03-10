use proconio::{input, fastout};

#[fastout]
fn main() {
    input! {
        n: usize,
        k: usize,
    }
    let div = n / k;
    let rest = n % k;
    let mut nums = vec![div; k];

    for i in 0..rest {
        nums[i] += 1;
    }

    let max = nums.iter().max().unwrap();
    let min = nums.iter().min().unwrap();

    println!("{}", max - min);

}
