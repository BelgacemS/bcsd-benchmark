use proconio::input;

fn main() {
    input! {
        mut n: i64,
    }

    let mut ans = 0;
    for i in 0..40 {
        let sign = if i % 2 == 0 { 1 } else { -1 };
        if n.rem_euclid(1 << (i + 1)) != 0 {
            n -= (1 << i) * sign;
            ans += 1 << i;
        }
    }
    println!("{ans:b}");
}
