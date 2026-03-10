use std::io::{self, BufRead};

use itertools::Itertools;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut nums = String::new();
    io::stdin().read_line(&mut nums)?;
    let mut nums = nums.split_whitespace();
    let a: i32 = nums.next().unwrap().parse()?;
    let b: i32 = nums.next().unwrap().parse()?;

    let ret = if a <= 8 && b <= 8 { "Yay!" } else { ":(" };

    println!("{ret}");

    Ok(())
}
