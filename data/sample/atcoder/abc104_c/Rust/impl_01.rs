use proconio::input;

fn main() {
    input! {
        d: usize, g: usize,
        pc: [(usize, usize); d],
    }

    let mut ans = usize::MAX;
    for bits in 0..1 << d {
        let mut g = g;
        let mut cand = 0;
        for (i, &(p, c)) in pc.iter().enumerate() {
            if bits >> i & 1 == 1 {
                cand += p;
                g = g.saturating_sub(100 * (i + 1) * p + c);
            }
        }

        for (i, &(p, _)) in pc.iter().enumerate().rev() {
            if bits >> i & 1 == 0 {
                let solve = g.div_ceil(100 * (i + 1)).min(p);
                cand += solve;
                g = g.saturating_sub(100 * (i + 1) * solve);
            }
        }

        ans = ans.min(cand);
    }
    println!("{ans}");
}
