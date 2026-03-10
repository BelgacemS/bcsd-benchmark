#[allow(unused_imports)]
use proconio::{input, marker::Chars};
fn main() {
    input! {
        n: usize,
        m: usize,
    }
    let mut a = vec![vec![]; 3];
    for _ in 0..n {
        for j in 0..3 {
            input! { x: isize}
            a[j].push(x);
        }
    }
    let mut res = 0;
    for bit in 0..1 << 3 {
        let mut b = vec![];
        for i in 0..n {
            let mut tmp = 0;
            for j in 0..3 {
                if (bit & (1 << j)) != 0 {
                    tmp += a[j][i];
                } else {
                    tmp -= a[j][i];
                }
            }
            b.push(tmp);
        }
        b.sort_by(|a, b| b.cmp(&a));
        let sum = b[..m].iter().sum();
        res = res.max(sum);
    }
    println!("{}", res);
}
