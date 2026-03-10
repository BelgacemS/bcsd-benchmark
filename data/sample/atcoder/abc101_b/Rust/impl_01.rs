use std::io::{self, BufRead};

use itertools::Itertools;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut n = String::new();
    io::stdin().read_line(&mut n)?;
    let total = n.trim().chars().filter_map(|n| n.to_digit(10)).sum::<u32>();
    let n = n.trim().parse::<u32>()?;

    let ret = if n % total == 0 { "Yes" } else { "No" };

    println!("{ret}");

    Ok(())
}
