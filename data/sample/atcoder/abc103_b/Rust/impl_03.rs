use proconio::{fastout, input, marker::Chars};

#[fastout]
fn main() {
    input! {
        mut s: Chars,
        t: Chars,
    }

    let s_len = s.len();
    let mut s_clone = s.clone();
    s_clone.remove(s_clone.len() - 1);

    s.extend(s_clone);

    for i in 0..s_len {
        let start = i;
        let end = i + s_len - 1;

        let mut flag = true;
        for (s, t) in s[start..end].iter().zip(&t) {
            if *s != *t {
                flag = false;
                break;
            }
        }

        if flag {
            println!("Yes");
            return;
        }
    }

    println!("No");
}
