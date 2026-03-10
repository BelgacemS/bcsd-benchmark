use proconio::{input, marker::Chars};
use proconio::fastout;
use std::char::ToUppercase;
use std::collections::HashMap;
use std::fmt::Display;
use std::i64;
use std::iter::StepBy;
use std::slice::ChunksExact;
use std::collections::HashSet;

// outマクロ 可変数引数対応
macro_rules! out {
    ($($x:expr),*) => {
        println!("{}", vec![$($x.to_string()),*].join(" "));
    };
}

macro_rules! min {
    ($x:expr) => ($x);
    ($x:expr, $($rest:expr),+) => {
        std::cmp::min($x, min!($($rest),+))
    };
}

macro_rules! max {
    ($x:expr) => ($x);
    ($x:expr, $($rest:expr),+) => {
        std::cmp::max($x, max!($($rest),+))
    };
}

#[fastout]
fn main() {
    input! {
       n : i64,
    }

    for i in 0..=100{
        for j in 0..=100{
            if i*4 + j*7 == n{
                an(0);
                return;
            }
        }
    }
    an(-1);
    


}





//ライブラリ

// outl: 1 次元スライスをスペース区切りで出力（Go の outl 相当）
fn outl<T: Display>(l: &[T]) {
    if l.is_empty() {
        println!();
        return;
    }
    print!("{}", l[0]);
    for x in &l[1..] {
        print!(" {}", x);
    }
    println!();
}

// outll: 2 次元スライスを行ごとに出力（Go の outll 相当）
fn outll<T: Display>(ll: &[Vec<T>]) {
    for row in ll {
        outl(row);
    }
}

//an(0)で"Yes",an(0以外)で"No"を返す。
fn an(x: i32) {
    if x == 0 {
        println!("Yes");
    } else {
        println!("No");
    }
}