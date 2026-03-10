use std::io::{self, BufRead};

use itertools::Itertools;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut s = String::new();
    io::stdin().read_line(&mut s)?;
    let c = s.trim().chars().collect::<Vec<_>>();
    let n = c.len();

    let a = c.iter().position(|&n| n == 'A');
    let b = c.iter().position(|&n| n == 'C');

    let ret = if match (a, b) {
        (Some(v1), Some(v2)) if v1 == 0 && (2..n - 1).contains(&v2) => {
            c.iter().enumerate().all(|(i, cc)| {
                if i == v1 || i == v2 {
                    true
                } else {
                    cc.is_lowercase()
                }
            })
        }
        _ => false,
    } {
        "AC"
    } else {
        "WA"
    };
    println!("{ret}");

    Ok(())
}
