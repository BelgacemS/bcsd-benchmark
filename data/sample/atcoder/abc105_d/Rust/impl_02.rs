// ----------------------------------------------------------------------
// Problem: abc105 - d
// Link: https://atcoder.jp/contests/abc105/tasks/abc105_d
// ----------------------------------------------------------------------
//
// # 隗｣豕輔Γ繝｢
//
//
// # 諢滓Φ繝ｻ蜿咲怐
//
// ----------------------------------------------------------------------
// region: Imports and Macros
#![allow(unused_imports)]
#![allow(unused_macros)]
#![allow(dead_code)]
#![allow(clippy::needless_range_loop)]
#![allow(clippy::ptr_arg)]

use std::cmp::{max, min, Reverse};
use std::collections::{BTreeMap, BTreeSet, BinaryHeap, VecDeque};
use std::io::{stdout, BufWriter, Write};

use proconio::{input, fastout, marker::{Chars, Usize1, Bytes}};
use itertools::Itertools;
use superslice::Ext;
use ac_library::*;
use num::{BigInt, Complex, Integer, Rational64, ToPrimitive, Zero, One};
use rand::prelude::*;

use rustc_hash::{FxHashMap, FxHashSet};
type Map<K, V> = FxHashMap<K, V>;
type Set<T> = FxHashSet<T>;

const UINF: u64 = 1 << 61;
const IINF: i64 = 1 << 61;
const MINF: i64 = -(1 << 61);

macro_rules! yesno { ($condition:expr) => { println!("{}", if $condition { "Yes" } else { "No" }); }; }
macro_rules! oob { ($r:expr, $c:expr, $h:expr, $w:expr) => { ($r as isize) < 0 || ($r as isize) >= ($h as isize) || ($c as isize) < 0 || ($c as isize) >= ($w as isize) }; }
macro_rules! chmin { ($base:expr, $($arg:expr),+) => {{ let mut updated = false; $( if $arg < $base { $base = $arg; updated = true; } )+ updated }}; }
macro_rules! chmax { ($base:expr, $($arg:expr),+) => {{ let mut updated = false; $( if $arg > $base { $base = $arg; updated = true; } )+ updated }}; }
macro_rules! mat { ($($e:expr),*) => { Vec::from(vec![$($e),*]) }; ($($e:expr,)*) => { Vec::from(vec![$($e),*]) }; ($e:expr; $d:expr) => { Vec::from(vec![$e; $d]) }; ($e:expr; $d:expr $(; $ds:expr)+) => { Vec::from(vec![mat![$e $(; $ds)*]; $d]) }; }
macro_rules! compress { ($a:expr) => {{ let mut xs = $a.clone(); xs.sort(); xs.dedup(); let ids: Vec<usize> = $a.iter().map(|x| xs.binary_search(x).unwrap()).collect(); (xs, ids) }}; }
macro_rules! unite { ($dest:expr, $src:expr) => {{ if $dest.len() < $src.len() { std::mem::swap(&mut $dest, &mut $src); } $dest.extend($src.drain()); }}; }
macro_rules! merge_sets { ($sets:expr, $ids:expr, $a:expr, $b:expr) => {{ if $sets[$ids[$a]].len() > $sets[$ids[$b]].len() { $ids.swap($a, $b); } let temp: Vec<_> = $sets[$ids[$a]].drain().collect(); $sets[$ids[$b]].extend(temp); }}; }
// endregion

fn main() {
  input! {
    n: usize,
    m: usize,
    a: [usize; n]
  }
  let mut map = Map::default();
  let mut current = 0;
  let mut ans :u64= 0;
  for i in 0..n {
    current += a[i];
    current %= m;
    let other = (m+current)%m;
    let e = map.entry(other).or_insert(0);
    ans += *e;
    if current%m == 0 {
      ans += 1;
    }
    *map.entry(current).or_insert(0) += 1;
  }
  println!("{}", ans);
}
