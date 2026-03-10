pub use __cargo_equip::prelude::*;

use cp_library::utils::yes_no_custom;
use proconio::{fastout, input};

#[fastout]
fn main() {
    input! {
        a: u64,
        b: u64,
    }
    let d = a.abs_diff(b);
    yes_no_custom(a == b || 16 - a.min(b) * 2 > 2 * d + 1, "Yay!", ":(");
}

// The following code was expanded by `cargo-equip`.

///  # Bundled libraries
/// 
///  - `git+https://github.com/itto4869/cp_library.git?branch=rust-1.89.0#cp_library@0.1.0` licensed under `MIT` as `crate::__cargo_equip::crates::cp_library`
#[cfg_attr(any(), rustfmt::skip)]
#[allow(unused)]
mod __cargo_equip {
    pub(crate) mod crates {
        pub mod cp_library {pub mod algorithm{mod lis{pub fn lis<T:Ord>(seq:&[T])->usize{let mut dp:Vec<&T> =Vec::new();for x in seq{let idx=dp.partition_point(|item|*item<x);if idx<dp.len(){dp[idx]=x;}else{dp.push(x);}}dp.len()}}pub use lis::lis;}pub mod data_structure{}pub mod graph{}pub mod grid{pub fn neighbors4(r:usize,c:usize,h:usize,w:usize)->Vec<(usize,usize)>{let mut neighbors=Vec::with_capacity(4);let dr=[0,0,1,!0];let dc=[1,!0,0,0];for i in 0..4{let nr=r.wrapping_add(dr[i]);let nc=c.wrapping_add(dc[i]);if nr<h&&nc<w{neighbors.push((nr,nc));}}neighbors}pub fn neighbors8(r:usize,c:usize,h:usize,w:usize)->Vec<(usize,usize)>{let mut neighbors=Vec::with_capacity(8);for dr in[!0,0,1]{for dc in[!0,0,1]{if dr==0&&dc==0{continue;}let nr=r.wrapping_add(dr);let nc=c.wrapping_add(dc);if nr<h&&nc<w{neighbors.push((nr,nc));}}}neighbors}}pub mod math{pub mod combinations{pub struct Combination{fact:Vec<u64>,inv_fact:Vec<u64>,modulo:u64,}impl Combination{pub fn new(max_n:usize,modulo:u64)->Self{let mut fact=vec![1;max_n+1];let mut inv_fact=vec![1;max_n+1];for i in 1..=max_n{fact[i]=(fact[i-1]*i as u64)%modulo;}inv_fact[max_n]=Self::mod_pow(fact[max_n],modulo-2,modulo);for i in(1..=max_n).rev(){inv_fact[i-1]=(inv_fact[i]*i as u64)%modulo;}Combination{fact,inv_fact,modulo,}}pub fn n_c_r(&self,n:usize,r:usize)->u64{if r>n{return 0;}let numer=self.fact[n];let denom=(self.inv_fact[r]*self.inv_fact[n-r])%self.modulo;(numer*denom)%self.modulo}pub fn n_p_r(&self,n:usize,r:usize)->u64{if r>n{return 0;}let numer=self.fact[n];let denom=self.inv_fact[n-r];(numer*denom)%self.modulo}pub fn n_h_r(&self,n:usize,r:usize)->u64{if n==0&&r==0{return 1;}if n==0{return 0;}self.n_c_r(n+r-1,r)}pub fn fact(&self,n:usize)->u64{self.fact[n]}pub fn inv_fact(&self,n:usize)->u64{self.inv_fact[n]}fn mod_pow(mut base:u64,mut exp:u64,modulo:u64)->u64{let mut res=1;base%=modulo;while exp>0{if exp%2==1{res=(res*base)%modulo;}base=(base*base)%modulo;exp/=2;}res}}}pub mod numeric{pub trait GCD{fn gcd(self,other:Self)->Self;fn lcm(self,other:Self)->Self;}macro_rules!impl_gcd{($($t:ty),*)=>{$(impl GCD for$t{fn gcd(self,other:Self)->Self{let mut a=self;let mut b=other;while b!=0{let t=b;b=a%b;a=t;}a}fn lcm(self,other:Self)->Self{if self==0&&other==0{return 0;}(self/self.gcd(other))*other}})*};}impl_gcd!(u8,u16,u32,u64,u128,usize,i8,i16,i32,i64,i128,isize);pub fn gcd<T:GCD>(a:T,b:T)->T{a.gcd(b)}pub fn lcm<T:GCD>(a:T,b:T)->T{a.lcm(b)}}}pub mod utils{pub fn yes_no(b:bool){yes_no_custom(b,"Yes","No");}pub fn yes_no_custom(b:bool,yes:&str,no:&str){println!("{}",if b{yes}else{no});}}pub use algorithm::lis;}
    }

    pub(crate) mod macros {
        pub mod cp_library {}
    }

    pub(crate) mod prelude {pub use crate::__cargo_equip::crates::*;}

    mod preludes {
        pub mod cp_library {}
    }
}
