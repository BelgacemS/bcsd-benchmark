#![allow(unused_imports)]
#![allow(non_snake_case)]
#![allow(unused_variables)]

use ac_library::ModInt1000000007 as Mint;
use itertools::Itertools;
use num::{
  integer::{div_ceil, gcd, lcm, sqrt},
  range_step, range_step_inclusive,
  rational::Ratio,
};
use proconio::{
  fastout, input,
  marker::{Bytes, Chars, Usize1},
};
use std::cmp::Reverse;
use std::collections::{BTreeMap, BTreeSet, BinaryHeap, HashMap, HashSet, VecDeque};
use std::mem::swap;
use superslice::Ext;

#[fastout]
fn main() {
  input! {
    mut n: i64,
  }

  if n == 0 {
    println!("0");
    return;
  }

  let mut digs = Vec::new();
  while n != 0 {
    let r = (n % 2).abs();

    n = (n - r) / (-2);

    digs.push(r);
  }

  println!("{}", digs.iter().rev().join(""));
}
