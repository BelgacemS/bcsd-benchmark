use proconio::{input, marker::Chars};

fn main() {
    input! {
        s: Chars,
    }

    let mut ans = true;
    ans &= s[0] == 'A';
    ans &= s[2..s.len() - 1].iter().filter(|&&c| c == 'C').count() == 1;
    ans &= s[1..]
        .iter()
        .filter(|&&c| c != 'C')
        .all(|c| c.is_ascii_lowercase());
    println!("{}", if ans { "AC" } else { "WA" });
}
