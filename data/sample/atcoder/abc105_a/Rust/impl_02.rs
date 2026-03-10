#![allow(non_snake_case)]

fn main() {
    let stdin = std::io::read_to_string(std::io::stdin()).unwrap();
    let mut stdin = stdin.split_whitespace();
    let N: i32 = stdin.next().unwrap().parse().unwrap();
    let K: i32 = stdin.next().unwrap().parse().unwrap();
    println!("{}", (N % K).min(1));
}