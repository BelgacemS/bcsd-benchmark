use proconio::{input, marker::Usize1};

fn main() {
    input! {
        _n: usize, m: usize,
        mut ab: [(Usize1, Usize1); m],
    }
    ab.sort_unstable();

    let mut ans = 1;
    let (mut l, mut r) = ab[0];
    for &(a, b) in &ab[1..] {
        let nl = l.max(a);
        let nr = r.min(b);
        if nl < nr {
            (l, r) = (nl, nr);
        } else {
            ans += 1;
            (l, r) = (a, b);
        }
    }
    println!("{ans}");
}
