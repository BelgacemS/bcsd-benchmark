#[allow(unused_imports)]
use itertools::{iproduct, Itertools};
#[allow(unused_imports)]
use num_traits::pow;
#[allow(unused_imports)]
use proconio::{
    fastout, input,
    marker::{Chars, Usize1},
};
#[allow(unused_imports)]
use std::cmp::{max, min};
#[allow(unused_imports)]
use std::collections::{HashMap, HashSet, VecDeque};
#[allow(unused_imports)]
use std::iter::FromIterator;

/**
 * マクロ
 */

/**
 * 汎用関数
 */
// toi:文字列→数値
#[rustfmt::skip] #[allow(dead_code)]
fn toi<T: std::str::FromStr>(s: &str) -> T where <T as std::str::FromStr>::Err: std::fmt::Debug {s.parse::<T>().unwrap()}

// ctoi:文字→数値(安全 > 速度)
#[rustfmt::skip] #[allow(dead_code)]
fn ctoi<T>(c: char) -> T where T: From<u32> { T::from(c.to_digit(10).expect("not a digit")) }

// ctoifast: 文字→数値 (速度 > 安全)
#[rustfmt::skip] #[allow(dead_code)]
fn ctoifast<T>(c: char) -> T where T: From<u32> { T::from(c as u32 - '0' as u32) }

/**
 * 以下回答
 */
#[fastout]
fn main() {
    input! {
        n: usize,
        a: [u128; n]
    }

    let mut m = 0;
    for &val in &a {
        m += val - 1;
    }
    println!("{}", m);
}
