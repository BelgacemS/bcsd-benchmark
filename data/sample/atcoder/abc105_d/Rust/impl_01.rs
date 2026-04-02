use ac_library::ModInt998244353 as Mint;
use ac_library::*;
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
use std::collections::{BTreeMap, BTreeSet, BinaryHeap, HashMap, HashSet, VecDeque};
#[allow(unused_imports)]
use std::iter::FromIterator;
#[allow(unused_macros)]
macro_rules! debug {
    ($($a:expr),* $(,)*) => {
        #[cfg(debug_assertions)]
        eprintln!(concat!($("| ", stringify!($a), "={:?} "),*, "|"), $(&$a),*);
    };
}

#[fastout]
fn main() {
    input! {n:usize,m:usize,a:[usize;n]}
    let mut sum = 0;
    let mut map = HashMap::new();
    map.insert(0, 1);
    a.into_iter().for_each(|ai| {
        sum = (sum + ai) % m;
        *map.entry(sum).or_insert(0) += 1;
    });
    let mut ans = 0usize;
    for (_, c) in map {
        ans += c * (c - 1) / 2;
    }

    println!("{}", ans);
}
