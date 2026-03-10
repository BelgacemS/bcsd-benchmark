use std::io::{self, BufRead};

use itertools::Itertools;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut n = String::new();
    io::stdin().read_line(&mut n)?;
    let n: u32 = n.trim().parse()?;

    let ret = if n % 2 == 0 { n } else { n * 2 };
    println!("{ret}");

    Ok(())
}
