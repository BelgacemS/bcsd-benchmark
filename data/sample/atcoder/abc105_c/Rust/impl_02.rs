#[rustfmt::skip]
pub mod lib {pub use ac_library::*;pub use itertools::{join, Combinations, Itertools, MultiProduct, Permutations};pub use proconio::{input,marker::{Chars, Usize1}};pub use std::{cmp::*, collections::*, mem::swap};pub use regex::Regex;pub use superslice::Ext;pub use num_traits::{One, ToPrimitive, FromPrimitive, PrimInt};#[macro_export]macro_rules! degg {($($val:expr),+ $(,)?) => {println!("[{}:{}] {}",file!(),line!(),{let mut parts = Vec::new();$(parts.push(format!("{} = {:?}", stringify!($val), &$val));)+parts.join(", ")})}}}
use lib::*;

pub trait ProductRepeat: Iterator + Clone
where
    Self::Item: Clone,
{
    fn product_repeat(self, repeat: usize) -> MultiProduct<Self> {
        std::iter::repeat(self).take(repeat).multi_cartesian_product()
    }
}

impl<T: Iterator + Clone> ProductRepeat for T where T::Item: Clone {}

fn main() {
    input! {
        n: isize
    }
    if n == 0 {
        return println!("0");
    }
    let keta = 34isize;
    let p = (0..=keta).filter(|&e| e % 2 == 0).collect_vec();
    let m = (0..=keta).filter(|&e| e % 2 == 1).collect_vec();
    let mut ps = BTreeSet::new();
    let mut ms = BTreeSet::new();
    ps.insert(0);
    ms.insert(0);

    for pp in (0..=1).product_repeat(p.len()) {
        let mut t = 0;
        for i in 0..p.len() {
            if pp[i] == 0 {
                continue;
            }
            t += 1isize << p[i];
        }
        ps.insert(t);
    }

    for pp in (0..=1).product_repeat(m.len()) {
        let mut t = 0;
        for i in 0..m.len() {
            if pp[i] == 0 {
                continue;
            }
            t += 1isize << m[i];
        }
        ms.insert(t);
    }

    for &num in ms.iter() {
        let target = n + num;
        if !ps.contains(&target) {
            continue;
        }
        
        let mut ans = vec![0; keta as usize];
        let now = num;
        for &idx in m.iter() {
            let t = (now >> idx) & 1 == 1;
            if t {
                ans[idx as usize] = 1;
            }
        }
        let now = target;
        for &idx in p.iter() {
            let t = (now >> idx) & 1 == 1;
            if t {
                ans[idx as usize] = 1;
            }
        }
        while !ans.is_empty() {
            let &la = ans.last().unwrap();
            if la != 0 {
                break;
            }
            ans.pop().unwrap();
        }
        ans.reverse();
        println!("{}", ans.iter().join(""));
        return;
    }
}
