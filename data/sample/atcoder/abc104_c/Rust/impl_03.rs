use ac_library::*;
use bitvec::store;
#[allow(unused_imports)]
use itertools::{iproduct, Itertools};
#[allow(unused_imports)]
use num_traits::pow;
#[allow(unused_imports)]
use proconio::{
    fastout, input,
    marker::{Chars, Usize1},
};
use std::cmp::Reverse;
#[allow(unused_imports)]
use std::cmp::{max, min};
#[allow(unused_imports)]
use std::collections::{BinaryHeap, HashMap, HashSet, VecDeque};
#[allow(unused_imports)]
use std::iter::FromIterator;

#[fastout]
fn main() {
    input! {
        d:usize,g:usize,pc:[(usize,usize);d]
    }
    let mut ans = std::usize::MAX;
    for mask in 0..(1 << d) {
        let mut score = 0;
        let mut cnt = 0;
        for i in 0..d {
            if (mask >> i) & 1 == 1 {
                score += pc[i].0 * (i + 1) * 100 + pc[i].1;
                cnt += pc[i].0;
            }
        }
        if score >= g {
            ans = min(ans, cnt);
            continue;
        }
        let compset = compset(mask, d);
        let last = if let Some(&x) = compset.last() {
            x
        } else {
            continue;
        };
        for i in (0..pc[last].0).rev() {
            score += (last + 1) * 100;
            cnt += 1;
            if score >= g {
                ans = min(ans, cnt);
                break;
            }
        }
    }
    println!("{}", ans);
}
fn subset(mask: usize, n: usize) -> Vec<usize> {
    (0..n).filter(|&i| (mask >> i) & 1 == 1).collect()
}
fn compset(mask: usize, n: usize) -> Vec<usize> {
    (0..n).filter(|&i| (mask >> i) & 1 == 0).collect()
}
