use proconio::{input, marker::Chars};

fn main() {
    input! {
        mut s: Chars,
        t: Chars,
    }

    for _ in 0..s.len() {
        if s == t {
            println!("Yes");
            return;
        }
        s.rotate_left(1);
    }
    println!("No");
}
