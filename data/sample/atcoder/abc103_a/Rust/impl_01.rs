use std::io::{self, BufRead};

use itertools::Itertools;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut nums = String::new();
    io::stdin().read_line(&mut nums)?;
    let mut nums = nums.split_whitespace();
    let a1: i32 = nums.next().unwrap().parse()?;
    let a2: i32 = nums.next().unwrap().parse()?;
    let a3: i32 = nums.next().unwrap().parse()?;

    let a1v = (a1.abs_diff(a2) + a2.abs_diff(a3)).min(a1.abs_diff(a3) + a3.abs_diff(a2));
    let a2v = (a2.abs_diff(a1) + a1.abs_diff(a3)).min(a2.abs_diff(a3) + a3.abs_diff(a1));
    let a3v = (a3.abs_diff(a1) + a1.abs_diff(a2)).min(a3.abs_diff(a2) + a2.abs_diff(a1));

    let ret = a1v.min(a2v).min(a3v);
    println!("{ret}");

    Ok(())
}
