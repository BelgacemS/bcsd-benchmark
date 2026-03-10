use ac_library::ModInt1000000007;
use proconio::{input, marker::Chars};

type Mint = ModInt1000000007;

fn main() {
    input! { s: Chars }

    let idx = |c: char| match c {
        '?' => 0,
        'A' => 1,
        'B' => 2,
        'C' => 3,
        _ => unreachable!(),
    };

    let mut ans = Mint::raw(0);
    let mut left = [0; 4];
    let mut right = [0; 4];
    for &c in &s {
        let i = idx(c);
        right[i] += 1;
    }
    for &c in &s {
        let i = idx(c);
        right[i] -= 1;

        if i == 0 || i == 2 {
            ans += Mint::raw(3).pow(left[0] + right[0]) * left[1] * right[3];
            ans += Mint::raw(3).pow(left[0].saturating_sub(1) + right[0]) * left[0] * right[3];
            ans += Mint::raw(3).pow(left[0] + right[0].saturating_sub(1)) * left[1] * right[0];
            ans += Mint::raw(3).pow(left[0].saturating_sub(1) + right[0].saturating_sub(1))
                * left[0]
                * right[0];
        }
        left[i] += 1;
    }

    println!("{ans}");
}
