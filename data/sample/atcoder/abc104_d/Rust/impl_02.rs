use core::cmp::Reverse;
use nalgebra::{max, min};
use proconio::marker::Chars;
use proconio::{fastout, input};
use std::collections::BinaryHeap;
use std::collections::{HashMap, HashSet};

#[fastout]
fn main() {
    input! {s:Chars}
    let n = s.len();
    let mut abch = vec![vec![0; n + 1]; 4];
    for i in 0..n {
        for j in 0..4 {
            abch[j][i + 1] = abch[j][i];
        }
        match s[i] {
            'A' => abch[0][i + 1] += 1,
            'B' => abch[1][i + 1] += 1,
            'C' => abch[2][i + 1] += 1,
            '?' => abch[3][i + 1] += 1,
            _ => {}
        }
    }
    //eprintln!("{:?}", abch);
    let mut ans = ModInt::new(0);
    for i in 0..n {
        if s[i] != 'B' && s[i] != '?' {
            continue;
        }
        let q1 = abch[3][i];
        let a = ModInt::new(abch[0][i]);
        let c = ModInt::new(abch[2][n] - abch[2][i + 1]);
        let q2 = abch[3][n] - abch[3][i + 1];
        ans += a * c * ModInt::new(3).pow(q1 + q2);
        if q2 > 0 {
            ans += a * ModInt::new(q2) * ModInt::new(3).pow(q1 + q2 - 1);
        }
        if q1 > 0 {
            ans += c * ModInt::new(q1) * ModInt::new(3).pow(q1 + q2 - 1);
        }
        if q1 > 0 && q2 > 0 {
            ans += ModInt::new(q1) * ModInt::new(q2) * ModInt::new(3).pow(q1 + q2 - 2);
        }
    }
    println!("{}", ans.value());
}

use std::ops;

const MOD: usize = 1000000007;

#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct ModInt {
    value: usize,
}

impl ModInt {
    pub fn new(value: usize) -> ModInt {
        ModInt { value: value % MOD }
    }

    pub fn value(&self) -> usize {
        self.value
    }

    pub fn inverse(&self) -> ModInt {
        // (a, b) -> (x, y) s.t. a * x + b * y = gcd(a, b)
        fn extended_gcd(a: isize, b: isize) -> (isize, isize) {
            if (a, b) == (1, 0) {
                (1, 0)
            } else {
                let (x, y) = extended_gcd(b, a % b);
                (y, x - (a / b) * y)
            }
        }

        let (x, _y) = extended_gcd(self.value() as isize, MOD as isize);
        ModInt::new((MOD as isize + x) as usize)
    }

    // a^n
    pub fn pow(&self, mut n: usize) -> ModInt {
        let mut res = ModInt::new(1);
        let mut x = *self;
        while n > 0 {
            if n % 2 == 1 {
                res *= x;
            }
            x *= x;
            n /= 2;
        }

        res
    }
}

impl ops::Add for ModInt {
    type Output = ModInt;
    fn add(self, other: Self) -> Self {
        ModInt::new(self.value + other.value)
    }
}

impl ops::Sub for ModInt {
    type Output = ModInt;
    fn sub(self, other: Self) -> Self {
        ModInt::new(MOD + self.value - other.value)
    }
}

impl ops::Mul for ModInt {
    type Output = ModInt;
    fn mul(self, other: Self) -> Self {
        ModInt::new(self.value * other.value)
    }
}

impl ops::Div for ModInt {
    type Output = ModInt;
    fn div(self, other: Self) -> Self {
        self * other.inverse()
    }
}

impl ops::AddAssign for ModInt {
    fn add_assign(&mut self, other: Self) {
        *self = *self + other;
    }
}

impl ops::SubAssign for ModInt {
    fn sub_assign(&mut self, other: Self) {
        *self = *self - other;
    }
}

impl ops::MulAssign for ModInt {
    fn mul_assign(&mut self, other: Self) {
        *self = *self * other;
    }
}

impl ops::DivAssign for ModInt {
    fn div_assign(&mut self, other: Self) {
        *self = *self / other;
    }
}

/// 組み合わせ計算用の前計算構造体
pub struct Comb {
    fact: Vec<ModInt>,     // 階乗
    inv_fact: Vec<ModInt>, // 階乗の逆元
    max_n: usize,          // 前計算の最大値
}

impl Comb {
    /// n以下の階乗と階乗の逆元を前計算
    pub fn new(n: usize) -> Self {
        let mut fact = vec![ModInt::new(1); n + 1];
        let mut inv_fact = vec![ModInt::new(1); n + 1];

        // 階乗を計算
        for i in 1..=n {
            fact[i] = fact[i - 1] * ModInt::new(i);
        }

        // 最大の階乗の逆元を計算
        inv_fact[n] = fact[n].inverse();

        // 階乗の逆元を逆順に計算
        for i in (1..n).rev() {
            inv_fact[i] = inv_fact[i + 1] * ModInt::new(i + 1);
        }

        Self {
            fact,
            inv_fact,
            max_n: n,
        }
    }

    /// n!を計算
    pub fn factorial(&self, n: usize) -> ModInt {
        assert!(
            n <= self.max_n,
            "n ({}) must be <= max_n ({})",
            n,
            self.max_n
        );
        self.fact[n]
    }

    /// nPrを計算
    pub fn permutation(&self, n: usize, r: usize) -> ModInt {
        if n < r {
            ModInt::new(0)
        } else {
            assert!(
                n <= self.max_n,
                "n ({}) must be <= max_n ({})",
                n,
                self.max_n
            );
            self.fact[n] * self.inv_fact[n - r]
        }
    }

    /// nCrを計算
    pub fn combination(&self, n: usize, r: usize) -> ModInt {
        if n < r {
            ModInt::new(0)
        } else {
            assert!(
                n <= self.max_n,
                "n ({}) must be <= max_n ({})",
                n,
                self.max_n
            );
            self.fact[n] * self.inv_fact[r] * self.inv_fact[n - r]
        }
    }

    /// nHr（重複組み合わせ）を計算
    pub fn homogeneous(&self, n: usize, r: usize) -> ModInt {
        if n == 0 && r > 0 {
            ModInt::new(0)
        } else {
            self.combination(n + r - 1, r)
        }
    }

    /// カタラン数 C_n = C(2n, n) / (n+1) を計算
    pub fn catalan(&self, n: usize) -> ModInt {
        if n == 0 {
            ModInt::new(1)
        } else {
            self.combination(2 * n, n) / ModInt::new(n + 1)
        }
    }

    /// 階乗の逆元を取得
    pub fn inv_factorial(&self, n: usize) -> ModInt {
        assert!(
            n <= self.max_n,
            "n ({}) must be <= max_n ({})",
            n,
            self.max_n
        );
        self.inv_fact[n]
    }
}

// 後方互換性のための関数（非推奨）
pub fn factorial(n: usize) -> ModInt {
    (1..=n).fold(ModInt::new(1), |x, y| x * ModInt::new(y))
}

pub fn permutation(n: usize, r: usize) -> ModInt {
    if n < r {
        ModInt::new(0)
    } else {
        (n - r + 1..=n).fold(ModInt::new(1), |x, y| x * ModInt::new(y))
    }
}

pub fn combination(n: usize, r: usize) -> ModInt {
    if n < r {
        ModInt::new(0)
    } else {
        permutation(n, r) / factorial(r)
    }
}

pub fn homogeneous(n: usize, r: usize) -> ModInt {
    combination(n + r - 1, r)
}
