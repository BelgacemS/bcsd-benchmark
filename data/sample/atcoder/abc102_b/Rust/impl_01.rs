use std::io::{self, BufRead};

use itertools::Itertools;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut n = String::new();
    let mut a = String::new();

    io::stdin().read_line(&mut n)?;
    io::stdin().read_line(&mut a)?;

    let a = a
        .split_whitespace()
        .map(|n| n.parse::<u32>())
        .collect::<Vec<_>>();

    let min = a.iter().flatten().min().unwrap();
    let max = a.iter().flatten().max().unwrap();

    let ret = min.abs_diff(*max);
    println!("{ret}");

    Ok(())
}
