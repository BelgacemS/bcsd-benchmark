use proconio::{fastout, input, marker::Bytes};

#[fastout]
fn main() {
    input! {
        s: Bytes,
        t: Bytes,
    }
    let n = s.len();
    for i in 0..n {
        let mut ok = true;
        for j in 0..n {
            if s[(j + i) % n] != t[j] {
                ok = false;
                break;
            }
        }

        if ok {
            println!("Yes");
            return;
        }
    }

    println!("No");
}
