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

trait DisplayVec<T> {
    fn print(&self, sep: &str);
}

impl<T> DisplayVec<T> for Vec<T>
where
    T: ToString,
{
    fn print(&self, sep: &str) {
        println!(
            "{}",
            self.iter()
                .map(std::string::ToString::to_string)
                .collect::<Vec<_>>()
                .join(sep)
        )
    }
}
#[allow(dead_code)]
fn print_chars(input_: &[char]) {
    println!("{}", &input_.iter().collect::<String>())
}
#[allow(dead_code)]
fn ctoi(c: &char) -> i32 {
    *c as i32 - 48
}
#[allow(dead_code)]
#[allow(non_snake_case)]
fn YESNO(res: bool) {
    if res {
        println!("YES")
    } else {
        println!("NO")
    }
}
#[allow(dead_code)]
#[allow(non_snake_case)]
fn YesNo(res: bool) {
    if res {
        println!("Yes")
    } else {
        println!("No")
    }
}
#[allow(dead_code)]
fn yesno(res: bool) {
    if res {
        println!("yes")
    } else {
        println!("no")
    }
}

#[allow(unused_macros)]
macro_rules! input_arrays_with_len {
    ($e:expr, $t:ty) => {
        (0..$e)
            .map(|_| {
                input! {
                    l: u32,
                    nums: [$t; l]
                }
                nums
            })
            .collect_vec()
    };
}

use counter_both_side::CounterBothSide;
pub mod counter_both_side {
    use counter::Counter;
    use std::hash::Hash;
    use std::iter::FromIterator;
    pub struct CounterBothSide<'a, T>
    where
        T: Hash + Eq + Clone,
    {
        array: &'a [T],
        left_ctr: Counter<T>,
        right_ctr: Counter<T>,
    }
    impl<'a, T> CounterBothSide<'a, T>
    where
        T: Hash + Eq + Clone,
    {
        pub fn new(array: &'a [T]) -> Self {
            let right_ctr = Counter::from_iter(array.iter().cloned());
            Self {
                left_ctr: Counter::new(),
                right_ctr,
                array,
            }
        }
        pub fn run<F>(&mut self, mut f: F)
        where
            F: FnMut(usize, &T, &mut Counter<T, usize>, &mut Counter<T, usize>),
        {
            for (idx, v) in self.array.iter().enumerate() {
                *self.right_ctr.entry(v.clone()).or_default() -= 1;
                f(idx, v, &mut self.left_ctr, &mut self.right_ctr);
                *self.left_ctr.entry(v.clone()).or_default() += 1;
            }
        }
    }
    #[cfg(test)]
    impl<'a, T> CounterBothSide<'a, T>
    where
        T: Hash + Eq + Clone,
    {
        pub fn array(&self) -> &'a [T] {
            &self.array
        }
        pub fn left_ctr(&self) -> &Counter<T> {
            &self.left_ctr
        }
        pub fn right_ctr(&self) -> &Counter<T> {
            &self.right_ctr
        }
    }
}

use ac_library::ModInt1000000007;
type Mint = ModInt1000000007;

#[fastout]
fn main() {
    input! {
        s: Chars
    }

    let mut ctr_iter = CounterBothSide::new(&s);
    let mut ans = Mint::new(0);

    ctr_iter.run(|_, &v, left, right| {
        if v == 'A' || v == 'C' {
            return;
        }
        let left_a = Mint::new(left[&'A']);
        let left_ques = Mint::new(left[&'?']);
        let right_c = Mint::new(right[&'C']);
        let right_ques = Mint::new(right[&'?']);

        ans += left_a * right_c * Mint::new(3).pow((left_ques + right_ques).val().into());
        if (left_ques + right_ques).val() > 0 {
            ans +=
                left_a * right_ques * Mint::new(3).pow((left_ques + right_ques - 1).val().into());
            ans +=
                left_ques * right_c * Mint::new(3).pow((left_ques + right_ques - 1).val().into());
        }
        if (left_ques + right_ques).val() >= 2 {
            ans += left_ques
                * right_ques
                * Mint::new(3).pow((left_ques + right_ques - 2).val().into());
        }
    });
    println!("{}", ans.val());
}
