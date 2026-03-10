#[allow(unused)]
use proconio::input;

#[allow(unused)]
use proconio::marker::Chars;
#[allow(non_snake_case)]
fn main() {
    input! {
        s:Chars
    }
    if s[0] != 'A' {
        println!("WA");
        return;
    }
    let mut cnt = 0;
    for i in 2..s.len()-1{
        if s[i]=='C'{
            cnt+=1;
        }
    }
    if cnt !=1{
        println!("WA");
        return;
    }
    for i in 0..s.len(){
        if s[i]!='A'&&s[i]!='C'{
            if s[i].is_uppercase(){
                println!("WA");
                return;
            }
        }
    }
    println!("AC");
}

