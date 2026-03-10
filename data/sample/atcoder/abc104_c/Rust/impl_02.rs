use proconio::input;

fn main() {
    input! {
        d: usize,
        g: usize,
        mut data: [(usize, usize); d],
    }

    let mut ans = usize::MAX;

    for bit in 0..(1 << d) {
        let mut count = 0;
        let mut score = 0;
        //for i in 0..d {
        for (i, d) in data
            .iter()
            .enumerate()
            .filter(|(i, _d)| (bit >> i) & 1 == 1)
            .collect::<Vec<_>>()
        {
            if (bit >> i) & 1 == 1 {
                let (pi, ci) = d;
                score += pi * (i + 1) * 100 + ci;
                count += pi;
            }
        }

        if score < g {
            for i in (0..d).rev() {
                if (bit >> i) & 1 == 0 {
                    let pi = data[i].0;
                    let rest = g - score;
                    count += (rest as f64 / ((i as f64 + 1.0) * 100.0)).ceil() as usize;
                    score += count.min(pi) * (i + 1) * 100;
                    break;
                }
            }
        }
        if score >= g {
            ans = ans.min(count);
        }
    }
    println!("{}", ans);
}
