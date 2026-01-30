# 官方测试用例核心代码汇总

生成时间: 2026-01-30 16:39:49

## ffichecker__examples__c-in-rust-doublefree
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(int *p) { free(p); }

```

### src\main.rs
```rust
extern "C" {
    fn c_func(p: *mut i32);
}

fn main() {
    let mut n = Box::new(1);
    unsafe {
        c_func(&mut *n);
    }

    *n = 2;
}

```

## ffichecker__examples__c-in-rust-memleak
### build.rs
```rust
fn main() {
    cc::Build::new().file("src/c_struct.c").compile("c_struct");
}

```

### src\c_struct.c
```c
#include <stdio.h>
#include <stdlib.h>

struct CStruct {
  int x;
  int y;
};

void c_function(struct CStruct *cs) {
  printf("x=%d, y=%d\n", cs->x, cs->y);
  // To fix this bug, add the following:
  // free(cs);
}

```

### src\main.rs
```rust
// Mute the warning when using `Box` in FFI
#![allow(improper_ctypes)]
use libc;

#[repr(C)]
pub struct CStruct {
    pub x: libc::c_int,
    pub y: libc::c_int,
}

extern "C" {
    fn c_function(c_obj: *mut CStruct);
}

fn main() {
    // Rust allocates memory here
    let c_obj = Box::new(CStruct { x: 1, y: 2 });
    unsafe {
        // Rust passes the ownership to a C function.
        // Memory leaks since this function does not deallocate memory
        c_function(Box::into_raw(c_obj));
    }
}

```

## ffichecker__examples__c-in-rust-uaf
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(int *p) { free(p); }

```

### src\main.rs
```rust
extern "C" {
    fn c_func(p: *mut i32);
}

fn main() {
    let mut n = Box::new(1);
    unsafe {
        c_func(&mut *n);
    }

    *n = 2;
}

```

## ffichecker__examples__cstring-test
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(char *p) { free(p); }

```

### src\main.rs
```rust
extern "C" {
    fn c_func(p: *mut i8);
}

fn main() {
    let s = std::ffi::CString::new("hello!").unwrap();
    let p = s.into_raw();
    unsafe {
        c_func(p);
    }
    // let _s = unsafe { std::ffi::CString::from_raw(p) };
}

```

## ffichecker__examples__ffi-simplest
### src\main.rs
```rust
// This extern block links to the libm library
#[link(name = "m")]
extern "C" {
    // this is a foreign function that computes cosine.
    fn cos(arg: f64) -> f64;
}

fn main() {
    let pi = 3.1415926535;
    // calling FFI is unsafe
    println!("cos(PI/2) = {:?}", unsafe { cos(pi / 2.0) });
}

```

## ffichecker__examples__function-pointer-test
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(int *p) { free(p); }

```

### src\main.rs
```rust
// The FFI is called through a callable object instead of its name

pub type Callback = unsafe extern "C" fn(*mut i32);

extern "C" {
    fn c_func(p: *mut i32);
}

pub fn run_callback(callback_object: Callback) {
    let mut n = Box::new(1);
    unsafe {
        callback_object(&mut *n);
    }

    *n = 2;
}

fn main() {
    let f = c_func;
    run_callback(f);
}

```

## ffichecker__examples__mix-box-free
### src\main.rs
```rust
use libc::{c_void, free, malloc};
use std::mem::size_of;

#[derive(Clone)]
struct Data {
    a: Box<u32>,
}

impl Drop for Data {
    fn drop(&mut self) {
        println!("Dropping {}.", self.a);
    }
}

impl Default for Data {
    fn default() -> Self {
        println!("Initializing.");
        Self { a: Box::new(1) }
    }
}

fn main() {
    unsafe {
        let p = malloc(1 * size_of::<Data>());
        // let mut v: Vec<Data> = Vec::from_raw_parts(p as *mut Data, 100, 100);
        let v = Box::from_raw(p as *mut Data);
        // for item in v {
        //     println!("test {:?}", item.vec);
        // }
    }
}

```

## ffichecker__examples__mix-mem-allocator
### src\main.rs
```rust
use libc::{c_void, free};

#[derive(Clone)]
#[repr(C)]
struct Data {
    vec: Vec<u32>,
}

impl Drop for Data {
    fn drop(&mut self) {
        println!("Dropping.");
    }
}

impl Default for Data {
    fn default() -> Self {
        println!("Initializing.");
        Self { vec: vec![1, 2, 3] }
    }
}

fn main() {
    let mut n = Box::new(Data::default());

    // Here the destructor won't be executed, so the vector is not freed
    unsafe {
        // Adding the following line to free the internal vector
        // free(n.vec.as_mut_ptr() as *mut c_void);
        free(Box::into_raw(n) as *mut c_void);
    }
}

```

## ffichecker__examples__rc-test
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(int *p) { free(p); }

```

### src\main.rs
```rust
use std::rc::Rc;

extern "C" {
    fn c_func(p: *mut i32);
}

fn main() {
    let mut n = Rc::new(Box::new(1));
    unsafe {
        c_func(&mut **Rc::make_mut(&mut n));
    }

    // *n = 2;
}

```

## ffichecker__examples__return-value-test
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(int *p) { free(p); }

```

### src\main.rs
```rust
extern "C" {
    fn c_func(p: *mut i32);
}

fn return_value_func() -> Box<i32> {
    Box::new(1)
}

fn main() {
    let mut n = return_value_func();
    unsafe {
        c_func(&mut *n);
    }

    *n = 2;
}

```

## ffichecker__examples__rust-in-c-uaf
### src\main.c
```c
#include <stdio.h>
#include <stdlib.h>

struct A {
  int a;
  int b;
};

void rust_function(struct A *obj);

int main() {
  struct A *obj = (struct A *)malloc(sizeof(struct A));
  obj->a = 1;
  obj->b = 2;
  rust_function(obj);
  free(obj);
  return 0;
}

```

### src\rust_function.rs
```rust
#![crate_type = "staticlib"]

#[repr(C)]
pub struct A {
    a: i32,
    b: i32,
}

#[no_mangle]
pub extern "C" fn rust_function(obj: Box<A>) {
    println!("a={}, b={}", obj.a, obj.b);
}

```

## ffichecker__examples__rust-uaf-df
### src\main.rs
```rust
fn genvec() -> Vec<u8> {
    let mut s = vec![1, 2, 3, 4, 5];
    /*fix2: let mut s = ManuallyDrop::new(String::from("a tmp string"));*/
    let ptr = s.as_mut_ptr();
    unsafe {
        let v = Vec::from_raw_parts(ptr, s.len(), s.len());
        /*fix1: mem::forget(s);*/
        return v;
        /*s is freed when the function returns*/
    }
}
fn main() {
    let v = genvec();
    assert_eq!('l' as u8, v[0]); /*use-after-free*/
    /*double free: v is released when the function returns*/
}

```

## ffichecker__examples__side-effects-test
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(int *p) { free(p); }

```

### src\main.rs
```rust
extern "C" {
    fn c_func(p: *mut i32);
}

fn side_effect_func(p: *mut *mut i32) {
    let mut n = Box::new(1);
    unsafe {
        *p = &mut *n;
    }
    // If we don't forget it, it will be dropped here
    std::mem::forget(n);
}

fn main() {
    // Initialize a pointer `p`
    let mut p: *mut i32 = &mut 0;
    // Use side effect to change `p`, now it should point to
    // the heap memory allocated by `Box`
    side_effect_func(&mut p);
    unsafe {
        // Free `p`
        c_func(p);
        // This should be a use-after-free
        *p = 2;
    }
}

```

## ffichecker__examples__string-test
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(char *p) { free(p); }

```

### src\main.rs
```rust
extern "C" {
    fn c_func(p: *mut u8);
}

fn main() {
    let mut s = String::from("hello!");
    unsafe {
        c_func(s.as_mut_ptr());
    }

    s.clear();
}

```

## ffichecker__examples__vec-test
### build.rs
```rust
fn main() {
    cc::Build::new()
        .file("src/c_function.c")
        .compile("c_function");
}

```

### src\c_function.c
```c
#include <stdlib.h>

void c_func(int *p) { free(p); }

```

### src\main.rs
```rust
extern "C" {
    fn c_func(p: *mut i32);
}

fn main() {
    let mut n = vec![1, 2, 3, 4, 5];
    unsafe {
        c_func(n.as_mut_ptr());
    }

    n.clear();
}

```

## ffichecker__trophy-case__
_无源代码文件_

## ffichecker__trophy-case__README.md
_无源代码文件_

## mirchecker__tests__safe-bugs__division-by-zero
### src\main.rs
```rust
#[macro_use]
extern crate macros;

#[allow(unused_variables)]
#[allow(unconditional_panic)]
fn main() {
    let n = 0;
    let a = 100;

    verify!(n == 0);
    let b = a / n; // Error: division by zero!

    if n != 0 {
        verify!(n != 0);
        let c = a / n; // OK
    }
}

```

## mirchecker__tests__safe-bugs__incorrect-boundary-check
### src\main.rs
```rust
fn main() {
    let insert_at_index: usize = 5;

    let mut buf = vec![1, 2, 3, 4, 5];
    let max_index: usize = 5;
    // if insert_at_index > max_index {
    //     panic!();
    // }
    buf[insert_at_index] = 100;
}

```

## mirchecker__tests__safe-bugs__incorrect-cast
### src\main.rs
```rust
fn main() {
    let _a = overflow(-1);
}

fn overflow(time: i64) -> u32 {
    (time % 1000) as u32 * 1000000
}

```

## mirchecker__tests__safe-bugs__integer-overflow
### src\main.rs
```rust
// Proof of concept of RUSTSEC-2017-0004

#[allow(unused_assignments)]
fn main() {
    // We use a loop to make a non-constant variable `t`
    let mut t: i32 = 0;
    while t < 100 {
        t += 1;
    }
    // Here, t == 100

    let mut a: u32 = 1;
    // let mut a: u32 = 10000; // Fix
    a = a - t as u32; // Error: u32 cannot be negative

    let mut b = std::i32::MAX;
    // let mut b = 10000; // Fix
    b = b + t; // Error: integer overflow

    let mut c = 2_147_483_647i32;
    c = c - t; // OK
}

// /**
//  * How to reproduce this bug:
//  *     - This bug need to be reproduced in release build.
//  *     - cargo run --release
//  */
// fn mock_encode_size_buggy(bytes_len: usize) -> usize {
//     let rem = bytes_len % 3;

//     let complete_input_chunks = bytes_len / 3;
//     let complete_output_chars = complete_input_chunks * 4;
//     let printing_output_chars = if rem == 0 {
//         complete_output_chars
//     } else {
//         complete_output_chars + 4
//     };
//     let line_ending_output_chars = printing_output_chars * 2;

//     return printing_output_chars + line_ending_output_chars;
// }

// fn mock_encoded_size_patch(bytes_len: usize) -> Option<usize> {
//     let printing_output_chars = bytes_len
//         .checked_add(2)
//         .map(|x| x / 3)
//         .and_then(|x| x.checked_mul(4));

//     let line_ending_output_chars = printing_output_chars.and_then(|y| y.checked_mul(2));

//     printing_output_chars.and_then(|x|
//         line_ending_output_chars.and_then(|y| x.checked_add(y)))
// }

// fn main() {
//     let bytes_len = 1 << 63;
//     let mut ret = mock_encode_size_buggy(bytes_len);
//     println!("buggy ret: {}", ret);
//     let resv_size = match mock_encoded_size_patch(bytes_len) {
//         Some(ret) => {
//             println!("patch ret: {}", ret);
//         },
//         None => panic!("integer overflow when calculating buffer size"),
//     };

//     // If you use the ret as a hint to allocate memory, it can lead to memory corruption
// }

```

## mirchecker__tests__safe-bugs__out-of-bound-index
### src\main.rs
```rust
fn main() {
    let mut a = vec![1, 2, 3, 4, 5];
    let mut i = 0;
    while i < 5 {
        a[i] = i;
        i = i + 1;
    }
    let result = a[i];
    // println!("{}", a[i]);
}

```

## mirchecker__tests__safe-bugs__unreachable
### src\main.rs
```rust
// Bug in brotli-rs that may trigger unreachable!()

fn main() {
    let n = 100;

    match n {
        1..=96 | 123..=191 => {
            // do something...
        }
        _ => unreachable!(),
    }
}

```

## mirchecker__tests__unit-tests__alloc-test
### src\main.rs
```rust
#[macro_use]
extern crate macros;

extern crate alloc;
use alloc::vec;

#[allow(unused_variables)]
fn main() {
    let v1 = vec![1, 2, 3, 4, 5];
    // let v2 = vec![0; 10];
    verify!(v1[3] == 4);
}

```

## mirchecker__tests__unit-tests__annotation
### src\main.rs
```rust
#[macro_use]
extern crate macros;

fn main() {
    let a = 1;
    let b = 2;
    let c = a + b;
    verify!(c == 3);
}

```

## mirchecker__tests__unit-tests__arith
### src\main.rs
```rust
#[macro_use]
extern crate macros;

#[allow(unused_variables)]
fn main() {
    let a = 1;
    let b = 2;
    let c = a + b;
    let d = a - b;
    let e = a * b;
    let f = a / b;
    let g = a % b;
    let h = a << b;
    let i = a >> b;
    let j = a & b;
    let k = a | b;
    let l = a ^ b;
    verify!(c == 3);
    verify!(d == -1);
    verify!(e == 2);
    verify!(f >= 0 && f <= 1);
    verify!(g == 1);
    verify!(h == 4);
    verify!(i == 0);
    verify!(j == 0);
    verify!(k == 3);
    verify!(l == 3);
}

```

## mirchecker__tests__unit-tests__array
### src\main.rs
```rust
#[macro_use]
extern crate macros;

#[allow(unused_variables)]
fn main() {
    let mut a = [1, 2, 3, 4, 5];
    let c = a;
    let b = c[0];
    let c = a[4];
    verify!(b == 1);
    verify!(c == 5);
    a[4] = 10;
    verify!(a[4] == 10);
    // let c = &a[2..5]; // Constant slice in source
}

```

## mirchecker__tests__unit-tests__assignment
### src\main.rs
```rust
#[macro_use]
extern crate macros;

#[allow(unused_variables)]
fn main() {
    let a = 1;
    let b = a;

    let c = &a;
    let d = *c;

    // Make sure `b` and `d` are 1, `c` points to `a`
    verify!(b == 1);
    verify!(d == 1);

    // let e = vec![1, 2, 3, 4, 5];
    // let f = e[4];
    // let g = e[d];
    // verify!(f == 5);
    // verify!(g == 2);
}

```

## mirchecker__tests__unit-tests__big-loop
### src\main.rs
```rust
#[macro_use]
extern crate macros;

fn main() {
    let mut i = 0;
    while i < 1000000 {
        verify!(i < 1000000);
        i += 1;
    }
    verify!(i >= 1000000);

    let mut j = 1000000;
    while j > 0 {
        verify!(j > 0);
        j -= 1;
    }
    verify!(j <= 0);

    let k = 0;
    while k != 1000000 {
        verify!(k != 1000000);
        // Here will be a false positive
        // The checker will always alert that this is a potential integer overflow
        // This is because currently it cannot reason about whether `k` will be exactly 1000000
        // k += 2;
    }
}

```

## mirchecker__tests__unit-tests__cast
### src\main.rs
```rust
#[macro_use]
extern crate macros;

#[allow(unused_variables)]
#[allow(unused_assignments)]
fn main() {
    let a: u16 = 1000;
    let mut b: u8 = a as u8;

    verify!(b == 232);
    b = b + 1;
    verify!(b == 233);
}

```

## mirchecker__tests__unit-tests__crate-bin-test
### src\func.rs
```rust
pub fn foo(a: u32) -> u32 {
    a + 1
}

```

### src\main.rs
```rust
mod func;

fn main() {
    println!("{}", func::foo(1));
}

```

## mirchecker__tests__unit-tests__crate-lib-test
### src\fun.rs
```rust
pub fn boo(a: u32) -> u32 {
    a + 1
}

```

### src\lib.rs
```rust
mod fun;

pub fn foo() {
    fun::boo(1);
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}

```

## mirchecker__tests__unit-tests__empty
### src\main.rs
```rust
#[allow(unused_variables)]
fn main() {
    let a = 0;
}

```

## mirchecker__tests__unit-tests__enum-test
### src\main.rs
```rust
#[macro_use]
extern crate macros;

enum A {
    One,
    #[allow(dead_code)]
    Two,
    #[allow(dead_code)]
    Three,
}

#[allow(unused_variables)]
fn main() {
    let a = A::One;
    let b = match a {
        A::One => 1,
        A::Two => 2,
        A::Three => 3,
    };
    // Make sure `b` is 1 here
    verify!(b == 1);
}

```

## mirchecker__tests__unit-tests__function-call
### src\main.rs
```rust
#[macro_use]
extern crate macros;

// // side effect on return value
fn side_effect_return(a: i32) -> i32 {
    2 * a
}

// // side effect on mutable argument
fn side_effect_arg(a: &mut i32) {
    *a = *a + 1;
}

// side effect on heap
fn side_effect_heap(heap: &mut [u32]) {
    heap[0] = 100;
}

fn side_effect_nested(heap: &mut [u32]) {
    heap[1] = side_effect_return(3) as u32; // 6
}

#[allow(unused_variables)]
#[allow(unused_assignments)]
fn main() {
    let mut heap = [1, 2, 3, 4, 5];
    let mut r = 5;
    r = side_effect_return(3);
    // Make sure `r` is now 6
    verify!(r == 6);

    side_effect_arg(&mut r);
    // Make sure `r` is now 7
    verify!(r == 7);

    side_effect_heap(&mut heap);
    // Make sure `heap[0]` is now 100
    verify!(heap[0] == 100);

    side_effect_nested(&mut heap);
    // Make sure `heap[1]` is now 6
    verify!(heap[1] == 6);
}

```

## mirchecker__tests__unit-tests__index
### src\main.rs
```rust
#[macro_use]
extern crate macros;

#[allow(unused_variables)]
fn main() {
    let a = [1, 2, 3, 4, 5];
    let b = a[3];
    let c = a[b];

    // Make sure `b` is 4, `c` is 5
    verify!(b == 4);
    verify!(c == 5);
}

```

## mirchecker__tests__unit-tests__input-type
### src\lib.rs
```rust
pub fn multiply(a: u64, b: u64) -> u128 {
    (a as u128) * (b as u128)
}

```

## mirchecker__tests__unit-tests__iterator
### src\main.rs
```rust
#[macro_use]
extern crate macros;

#[allow(unused_assignments)]
#[allow(unused_variables)]
fn main() {
    let a = vec![1, 2, 3, 4, 5];
    let mut b = 0;
    for i in a {
        // verify!(i >= 1 && i <= 5);
        b = i;
        verify!(b == i);
    }
    // verify!(b == 5);
}

```

## mirchecker__tests__unit-tests__loop-test
### src\main.rs
```rust
#[macro_use]
extern crate macros;

// fn main() {
//     let mut i = 0;
//     while i < 5 {
//         verify!(i < 5);
//         i = i + 1;
//     }
//     verify!(i >= 5);

//     let mut i = 5;
//     while i > 0 {
//         verify!(i > 0);
//         i = i - 1;
//     }
//     verify!(i <= 0);
// }

fn main() {
    let mut a = 0;
    let r = &mut a;
    while *r < 5 {
        *r += 1;
    }
}

```

## mirchecker__tests__unit-tests__method-test
### src\main.rs
```rust
struct A {
    a: i32,
}

impl A {
    pub fn func(&mut self) {
        self.a = 0;
    }
}

fn main() {}

```

## mirchecker__tests__unit-tests__negation
### src\main.rs
```rust
#[macro_use]
extern crate macros;

// Use a function call to avoid constant propagation
fn func(a: i32) -> i32 {
    2 * a
}

#[allow(unused_variables)]
fn main() {
    let a = func(2);
    verify!(a == 4);
    let b = -a;
    verify!(b == -4);
}

```

## mirchecker__tests__unit-tests__recursion
### src\main.rs
```rust
// Make sure that our analysis for recursive calls can terminate
// Otherwise, there will be a stack overflow

#[allow(unused_variables)]
fn main() {
    let result = factorial(5);
}

fn factorial(n: u32) -> u32 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}

```

## mirchecker__tests__unit-tests__size-of
### src\main.rs
```rust
#[macro_use]
extern crate macros;

fn main() {
    let a = std::mem::size_of::<u32>();
    verify!(a == 4);
}

```

## mirchecker__tests__unit-tests__struct-test
### src\main.rs
```rust
#[macro_use]
extern crate macros;

struct A {
    x: i32,
    y: i32,
}

#[allow(unused_variables)]
fn main() {
    let a = A { x: 1, y: 0 };
    let b = 1 / a.x; // OK
    verify!(b == 1);
    verify!(a.y == 0);
}

```

## mirchecker__tests__unit-tests__vector
### src\main.rs
```rust
#[macro_use]
extern crate macros;

#[allow(unused_variables)]
fn main() {
    let a = vec![1, 2, 3, 4, 5];
    let b = a[0];
    // let c = a[4];
    verify!(b == 1);
    // verify!(c == 5);
}

```

## mirchecker__tests__unit-tests__widen-narrow
### src\main.rs
```rust
// Example for testing widening and narrow
// From the book "Static Program Analysis" by Anders M酶ller and Michael I. Schwartzbach

#[macro_use]
extern crate macros;

fn main() {
    let mut y = 0;
    let mut x = 7;
    x = x + 1;
    let mut i = 0;
    while i < 10 {
        i = i + 1;
        x = 7;
        x = x + 1;
        y = y + 1;
    }
    verify!(x == 8);
    verify!(y > 0);
}

```

## mirchecker__tests__unsafe-bugs__double-free
### src\main.rs
```rust
// Proof-of-concept of several double-free vulnerabilities (CVE-2018-20996, CVE-2019-16880, CVE-2019-16144, CVE-2019-16881)
// Not very similar to those real CVEs but should be enough for illustration purpose

pub struct Foo {
    pub s: Vec<u32>,
}

impl Drop for Foo {
    fn drop(&mut self) {
        println!("Dropping: {:?}", self.s);
    }
}

pub fn fun1() -> Foo {
    let mut src = vec![1, 2, 3, 4, 5, 6];
    let foo = fun2(&mut src);
    foo
}

pub fn fun2(src: &mut Vec<u32>) -> Foo {
    let s = unsafe { Vec::from_raw_parts(src.as_mut_ptr(), src.len(), 32) };
    Foo { s: s }
}

pub fn main() {
    let _foo = fun1();
}

```

## mirchecker__tests__unsafe-bugs__gmath
### src\lib.rs
```rust
const LEN: usize = 4;
const SIZE: usize = std::mem::size_of::<f32>() * LEN;

#[no_mangle]
pub unsafe fn alloc(size: usize) -> *mut u8 {
    let align = std::mem::align_of::<usize>();
    let layout = std::alloc::Layout::from_size_align_unchecked(size, align);
    std::alloc::alloc(layout)
}

#[no_mangle]
pub unsafe fn dealloc(ptr: *mut u8, size: usize) {
    let align = std::mem::align_of::<usize>();
    let layout = std::alloc::Layout::from_size_align_unchecked(size, align);
    std::alloc::dealloc(ptr, layout);
}

#[no_mangle]
pub unsafe fn matrix2invert(a: *mut f32) -> *mut u8 {
    let a = std::slice::from_raw_parts(a, LEN);

    let det = a[0] * a[3] - a[2] * a[1];

    if det == 0.0 {
        return std::ptr::null_mut();
    }

    let ptr = alloc(SIZE);
    let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);
    let det = 1f32 / det;

    mat[0] = a[3] * det;
    mat[1] = -a[1] * det;
    mat[2] = -a[2] * det;
    mat[3] = a[0] * det;

    ptr
}

```

## mirchecker__tests__unsafe-bugs__offset
### src\main.rs
```rust
fn main() {
    let mut array: [u8; 5] = [1, 2, 3, 4, 5];
    let p = array.as_mut_ptr();
    // println!("out_of_bound_access: {}", unsafe { *p.offset(5) });
    let _out_of_bound_access = unsafe { *p.offset(5) };
}

```

## mirchecker__tests__unsafe-bugs__spglib-rs
### src\lib.rs
```rust
use std::convert::TryFrom;

#[derive(Clone, Debug)]
pub struct Dataset {
    /// The number of symmetry operations.
    pub n_operations: i32,
    /// The rotation symmetry operations.
    pub rotations: Vec<[[i32; 3]; 3]>,
    /// The translation symmetry operations.
    pub translations: Vec<[f64; 3]>,
}

// Pretends to be a C style structure
#[derive(Clone, Debug)]
pub struct SpglibDataset {
    /// The number of symmetry operations.
    pub n_operations: i32,
    /// The rotation symmetry operations.
    pub rotations: *mut [[i32; 3]; 3],
    /// The translation symmetry operations.
    pub translations: *mut [f64; 3],
}

impl TryFrom<*mut SpglibDataset> for Dataset {
    type Error = &'static str;

    fn try_from(value: *mut SpglibDataset) -> Result<Self, Self::Error> {
        // dereference the raw pointer
        let ptr = unsafe { &mut *value };
        let n_operations = ptr.n_operations as i32;
        let rotations = unsafe {
            // This creates possible mutable shared memory
            Vec::from_raw_parts(ptr.rotations, n_operations as usize, n_operations as usize)
        };
        let translations = unsafe {
            Vec::from_raw_parts(
                ptr.translations,
                n_operations as usize,
                n_operations as usize,
            )
        };
        Ok(Dataset {
            n_operations,
            rotations,
            translations,
        })
    }
}

```

## mirchecker__tests__unsafe-bugs__use-after-free(CVE-2019-15551)
### src\main.rs
```rust
// Proof-of-concept of CVE-2019-15551

unsafe fn deallocate<T>(ptr: *mut T, capacity: usize) {
    let _vec: Vec<T> = Vec::from_raw_parts(ptr, 0, capacity);
}

fn bug(n: i32, v: &mut Vec<u32>) {
    if n < 0 {
        // Do something
    }
    // Fix
    // else {
    //     return;
    // }
    unsafe {
        deallocate(v.as_mut_ptr(), v.len());
    }
}

fn main() {
    let mut v = vec![1, 2, 3, 4, 5];
    bug(1, &mut v);
}

```

## mirchecker__tests__unsafe-bugs__use-after-free(CVE-2019-16140)
### src\main.rs
```rust
// Proof of concept of CVE-2019-16140

#[allow(unused_variables)]
fn main() {
    let v = test();
}

fn test() -> Vec<u8> {
    // let mut s = String::from("lifetime test");
    let mut s = vec![1, 2, 3, 4, 5];
    let ptr = s.as_mut_ptr();
    unsafe { Vec::from_raw_parts(ptr, s.len(), s.len()) }
}

// // Use-after-free in chttp
// // This will cause a segmentation fault

// fn allocate(len: usize) -> Vec<u8> {
//     let mut slice = vec![1; len];
//     unsafe {
//         let vec = Vec::from_raw_parts(slice.as_mut_ptr(), len, slice.len());
//         // std::mem::forget(slice); // Fix
//         vec
//     }
// }

// fn main() {
//     let v = allocate(5);
//     println!("{:?}", v);
// }

```

## mirchecker__trophy-case__bitvec-test
### src\main.rs
```rust
// This would cause division by zero
// https://github.com/bitvecto-rs/bitvec/issues/123

use bitvec::mem;

fn main() {
    let _a = mem::elts::<()>(1);
}

```

## mirchecker__trophy-case__brotli-test
### src\main.rs
```rust
// This would cause integer overflow
// https://github.com/dropbox/rust-brotli/issues/53

use brotli::enc::command::BrotliDistanceParams;
use brotli::enc::command::Command;

fn main() {
    let mut command = Command::default();
    command.dist_prefix_ = 1000;
    let params = BrotliDistanceParams {
        distance_postfix_bits: 40,
        num_direct_distance_codes: 0,
        alphabet_size: 0,
        max_distance: 0,
    };
    let _ = brotli::enc::command::CommandRestoreDistanceCode(&command, &params);
}

```

## mirchecker__trophy-case__brotli-test2
### src\main.rs
```rust
// This would cause integer overflow
// https://github.com/dropbox/rust-brotli/issues/53

use brotli::enc::command::PrefixEncodeCopyDistance;

fn main() {
    let mut code = 0;
    let mut extra_bits = 0;
    PrefixEncodeCopyDistance(100, 0, 100, &mut code, &mut extra_bits);
}

```

## mirchecker__trophy-case__brotli-test3
### src\main.rs
```rust
// This would cause out-of-bounds access
// https://github.com/dropbox/rust-brotli/issues/53

use brotli::enc::brotli_bit_stream::BrotliBuildAndStoreHuffmanTreeFast;
use brotli::enc::writer::StandardAlloc;
fn main() {
    let mut alloc = StandardAlloc::default();
    BrotliBuildAndStoreHuffmanTreeFast(
        &mut alloc,
        &[0],
        0,
        0,
        &mut [0],
        &mut [0],
        &mut 99999,
        &mut [0],
    );
}

```

## mirchecker__trophy-case__bytemuck-test
### src\main.rs
```rust
// This would enter unreachable code
// https://github.com/Lokathor/bytemuck/issues/52

use bytemuck;

fn main() {
    // Panic: enter unreachable code
    let zst: [u32; 0] = [];
    let _result = bytemuck::bytes_of(&zst);
}

```

## mirchecker__trophy-case__byte-unit-test
### src\main.rs
```rust
// This would cause integer overflow
// https://github.com/magiclen/Byte-Unit/issues/7

use byte_unit;

fn main() {
    // Panic: integer overflow
    println!("{}", byte_unit::n_zb_bytes(std::u128::MAX));
}

```

## mirchecker__trophy-case__executable-memory-test
### src\main.rs
```rust
// This would cause an integer overflow
// https://gitlab.com/nathanfaucett/rs-executable_memory/-/issues/1

use executable_memory::ExecutableMemory;

fn main() {
    let _memory = ExecutableMemory::new(std::usize::MAX);
}

```

## mirchecker__trophy-case__executable-memory-test2
### src\main.rs
```rust
// This will cause a segmentation fault
// https://gitlab.com/nathanfaucett/rs-executable_memory/-/issues/1

use executable_memory::ExecutableMemory;

fn main() {
    let memory = ExecutableMemory::new(2251799813685248);
    println!("len: {}", memory.len());
    println!("read: {}", memory.as_slice()[5000]);
}

```

## mirchecker__trophy-case__gmath-test
### gmath\wasm\lib.rs
```rust
pub mod matrix2;
pub mod matrix3;
pub mod matrix4;

#[no_mangle]
pub unsafe fn alloc(size: usize) -> *mut u8 {
  let align = std::mem::align_of::<usize>();
  let layout = std::alloc::Layout::from_size_align_unchecked(size, align);
  std::alloc::alloc(layout)
}

#[no_mangle]
pub unsafe fn dealloc(ptr: *mut u8, size: usize) {
  let align = std::mem::align_of::<usize>();
  let layout = std::alloc::Layout::from_size_align_unchecked(size, align);
  std::alloc::dealloc(ptr, layout);
}

```

### gmath\wasm\matrix2.rs
```rust
use crate::alloc;

const LEN: usize = 4;
const SIZE: usize = std::mem::size_of::<f32>() * LEN;

#[no_mangle]
pub unsafe fn matrix2determinant(a: *mut f32) -> f32 {
  let a = std::slice::from_raw_parts(a, LEN);

  a[0] * a[3] - a[2] * a[1]
}

#[no_mangle]
pub unsafe fn matrix2invert(a: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);

  let det = a[0] * a[3] - a[2] * a[1];

  if det == 0.0 {
    return std::ptr::null_mut();
  }

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);
  let det = 1f32 / det;

  mat[0] = a[3] * det;
  mat[1] = -a[1] * det;
  mat[2] = -a[2] * det;
  mat[3] = a[0] * det;

  ptr
}

#[no_mangle]
pub unsafe fn matrix2mul(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = a[0] * b[0] + a[2] * b[1];
  mat[1] = a[1] * b[0] + a[3] * b[1];
  mat[2] = a[0] * b[2] + a[2] * b[3];
  mat[3] = a[1] * b[2] + a[3] * b[3];

  ptr
}

#[no_mangle]
pub unsafe fn matrix2add(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = a[0] + b[0];
  mat[1] = a[1] + b[1];
  mat[2] = a[2] + b[2];
  mat[3] = a[3] + b[3];

  ptr
}

#[no_mangle]
pub unsafe fn matrix2sub(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = a[0] - b[0];
  mat[1] = a[1] - b[1];
  mat[2] = a[2] - b[2];
  mat[3] = a[3] - b[3];

  ptr
}

```

### gmath\wasm\matrix3.rs
```rust
use crate::alloc;

const LEN: usize = 9;
const SIZE: usize = std::mem::size_of::<f32>() * LEN;

#[no_mangle]
pub unsafe fn matrix3determinant(a: *mut f32) -> f32 {
  let a = std::slice::from_raw_parts(a, LEN);

  a[0] * (a[8] * a[4] - a[5] * a[7])
    + a[1] * (-a[8] * a[3] + a[5] * a[6])
    + a[2] * (a[7] * a[3] - a[4] * a[6])
}

#[no_mangle]
pub unsafe fn matrix3invert(a: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);

  let b01 = a[8] * a[4] - a[5] * a[7];
  let b11 = -a[8] * a[3] + a[5] * a[6];
  let b21 = a[7] * a[3] - a[4] * a[6];

  let det = a[0] * b01 + a[1] * b11 + a[2] * b21;

  if det == 0.0 {
    return std::ptr::null_mut();
  }

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);
  let det = 1f32 / det;

  mat[0] = b01 * det;
  mat[1] = (-a[8] * a[1] + a[2] * a[7]) * det;
  mat[2] = (a[5] * a[1] - a[2] * a[4]) * det;
  mat[3] = b11 * det;
  mat[4] = (a[8] * a[0] - a[2] * a[6]) * det;
  mat[5] = (-a[5] * a[0] + a[2] * a[3]) * det;
  mat[6] = b21 * det;
  mat[7] = (-a[7] * a[0] + a[1] * a[6]) * det;
  mat[8] = (a[4] * a[0] - a[1] * a[3]) * det;

  ptr
}

#[no_mangle]
pub unsafe fn matrix3mul(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = b[0] * a[0] + b[1] * a[3] + b[2] * a[6];
  mat[1] = b[0] * a[1] + b[1] * a[4] + b[2] * a[7];
  mat[2] = b[0] * a[2] + b[1] * a[5] + b[2] * a[8];
  mat[3] = b[3] * a[0] + b[4] * a[3] + b[5] * a[6];
  mat[4] = b[3] * a[1] + b[4] * a[4] + b[5] * a[7];
  mat[5] = b[3] * a[2] + b[4] * a[5] + b[5] * a[8];
  mat[6] = b[6] * a[0] + b[7] * a[3] + b[8] * a[6];
  mat[7] = b[6] * a[1] + b[7] * a[4] + b[8] * a[7];
  mat[8] = b[6] * a[2] + b[7] * a[5] + b[8] * a[8];

  ptr
}

#[no_mangle]
pub unsafe fn matrix3add(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = a[0] + b[0];
  mat[1] = a[1] + b[1];
  mat[2] = a[2] + b[2];
  mat[3] = a[3] + b[3];
  mat[4] = a[4] + b[4];
  mat[5] = a[5] + b[5];
  mat[6] = a[6] + b[6];
  mat[7] = a[7] + b[7];
  mat[8] = a[8] + b[8];

  ptr
}

#[no_mangle]
pub unsafe fn matrix3sub(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = a[0] - b[0];
  mat[1] = a[1] - b[1];
  mat[2] = a[2] - b[2];
  mat[3] = a[3] - b[3];
  mat[4] = a[4] - b[4];
  mat[5] = a[5] - b[5];
  mat[6] = a[6] - b[6];
  mat[7] = a[7] - b[7];
  mat[8] = a[8] - b[8];

  ptr
}

```

### gmath\wasm\matrix4.rs
```rust
use crate::alloc;

const LEN: usize = 16;
const SIZE: usize = std::mem::size_of::<f32>() * LEN;

#[no_mangle]
pub unsafe fn matrix4determinant(a: *mut f32) -> f32 {
  let a = std::slice::from_raw_parts(a, LEN);

  let b00 = a[0] * a[5] - a[1] * a[4];
  let b01 = a[0] * a[6] - a[2] * a[4];
  let b02 = a[0] * a[7] - a[3] * a[4];
  let b03 = a[1] * a[6] - a[2] * a[5];
  let b04 = a[1] * a[7] - a[3] * a[5];
  let b05 = a[2] * a[7] - a[3] * a[6];
  let b06 = a[8] * a[13] - a[9] * a[12];
  let b07 = a[8] * a[14] - a[10] * a[12];
  let b08 = a[8] * a[15] - a[11] * a[12];
  let b09 = a[9] * a[14] - a[10] * a[13];
  let b10 = a[9] * a[15] - a[11] * a[13];
  let b11 = a[10] * a[15] - a[11] * a[14];

  b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06
}

#[no_mangle]
pub unsafe fn matrix4invert(a: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);

  let b00 = a[0] * a[5] - a[1] * a[4];
  let b01 = a[0] * a[6] - a[2] * a[4];
  let b02 = a[0] * a[7] - a[3] * a[4];
  let b03 = a[1] * a[6] - a[2] * a[5];
  let b04 = a[1] * a[7] - a[3] * a[5];
  let b05 = a[2] * a[7] - a[3] * a[6];
  let b06 = a[8] * a[13] - a[9] * a[12];
  let b07 = a[8] * a[14] - a[10] * a[12];
  let b08 = a[8] * a[15] - a[11] * a[12];
  let b09 = a[9] * a[14] - a[10] * a[13];
  let b10 = a[9] * a[15] - a[11] * a[13];
  let b11 = a[10] * a[15] - a[11] * a[14];
  
  let det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06;

  if det == 0.0 {
    return std::ptr::null_mut();
  }

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);
  let det = 1f32 / det;

  mat[0] = (a[5] * b11 - a[6] * b10 + a[7] * b09) * det;
  mat[1] = (a[2] * b10 - a[1] * b11 - a[3] * b09) * det;
  mat[2] = (a[13] * b05 - a[14] * b04 + a[15] * b03) * det;
  mat[3] = (a[10] * b04 - a[9] * b05 - a[11] * b03) * det;
  mat[4] = (a[6] * b08 - a[4] * b11 - a[7] * b07) * det;
  mat[5] = (a[0] * b11 - a[2] * b08 + a[3] * b07) * det;
  mat[6] = (a[14] * b02 - a[12] * b05 - a[15] * b01) * det;
  mat[7] = (a[8] * b05 - a[10] * b02 + a[11] * b01) * det;
  mat[8] = (a[4] * b10 - a[5] * b08 + a[7] * b06) * det;
  mat[9] = (a[1] * b08 - a[0] * b10 - a[3] * b06) * det;
  mat[10] = (a[12] * b04 - a[13] * b02 + a[15] * b00) * det;
  mat[11] = (a[9] * b02 - a[8] * b04 - a[11] * b00) * det;
  mat[12] = (a[5] * b07 - a[4] * b09 - a[6] * b06) * det;
  mat[13] = (a[0] * b09 - a[1] * b07 + a[2] * b06) * det;
  mat[14] = (a[13] * b01 - a[12] * b03 - a[14] * b00) * det;
  mat[15] = (a[8] * b03 - a[9] * b01 + a[10] * b00) * det;

  ptr
}

#[no_mangle]
pub unsafe fn matrix4mul(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = b[0] * a[0] + b[1] * a[4] + b[2] * a[8] + b[3] * a[12];
  mat[1] = b[0] * a[1] + b[1] * a[5] + b[2] * a[9] + b[3] * a[13];
  mat[2] = b[0] * a[2] + b[1] * a[6] + b[2] * a[10] + b[3] * a[14];
  mat[3] = b[0] * a[3] + b[1] * a[7] + b[2] * a[11] + b[3] * a[15];
  mat[4] = b[4] * a[0] + b[5] * a[4] + b[6] * a[8] + b[7] * a[12];
  mat[5] = b[4] * a[1] + b[5] * a[5] + b[6] * a[9] + b[7] * a[13];
  mat[6] = b[4] * a[2] + b[5] * a[6] + b[6] * a[10] + b[7] * a[14];
  mat[7] = b[4] * a[3] + b[5] * a[7] + b[6] * a[11] + b[7] * a[15];
  mat[8] = b[8] * a[0] + b[9] * a[4] + b[10] * a[8] + b[11] * a[12];
  mat[9] = b[8] * a[1] + b[9] * a[5] + b[10] * a[9] + b[11] * a[13];
  mat[10] = b[8] * a[2] + b[9] * a[6] + b[10] * a[10] + b[11] * a[14];
  mat[11] = b[8] * a[3] + b[9] * a[7] + b[10] * a[11] + b[11] * a[15];
  mat[12] = b[12] * a[0] + b[13] * a[4] + b[14] * a[8] + b[15] * a[12];
  mat[13] = b[12] * a[1] + b[13] * a[5] + b[14] * a[9] + b[15] * a[13];
  mat[14] = b[12] * a[2] + b[13] * a[6] + b[14] * a[10] + b[15] * a[14];
  mat[15] = b[12] * a[3] + b[13] * a[7] + b[14] * a[11] + b[15] * a[15];

  ptr
}

#[no_mangle]
pub unsafe fn matrix4add(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = a[0] + b[0];
  mat[1] = a[1] + b[1];
  mat[2] = a[2] + b[2];
  mat[3] = a[3] + b[3];
  mat[4] = a[4] + b[4];
  mat[5] = a[5] + b[5];
  mat[6] = a[6] + b[6];
  mat[7] = a[7] + b[7];
  mat[8] = a[8] + b[8];
  mat[9] = a[9] + b[9];
  mat[10] = a[10] + b[10];
  mat[11] = a[11] + b[11];
  mat[12] = a[12] + b[12];
  mat[13] = a[13] + b[13];
  mat[14] = a[14] + b[14];
  mat[15] = a[15] + b[15];

  ptr
}

#[no_mangle]
pub unsafe fn matrix4sub(a: *mut f32, b: *mut f32) -> *mut u8 {
  let a = std::slice::from_raw_parts(a, LEN);
  let b = std::slice::from_raw_parts(b, LEN);

  let ptr = alloc(SIZE);
  let mut mat = Vec::from_raw_parts(ptr as *mut f32, LEN, LEN);

  mat[0] = a[0] - b[0];
  mat[1] = a[1] - b[1];
  mat[2] = a[2] - b[2];
  mat[3] = a[3] - b[3];
  mat[4] = a[4] - b[4];
  mat[5] = a[5] - b[5];
  mat[6] = a[6] - b[6];
  mat[7] = a[7] - b[7];
  mat[8] = a[8] - b[8];
  mat[9] = a[9] - b[9];
  mat[10] = a[10] - b[10];
  mat[11] = a[11] - b[11];
  mat[12] = a[12] - b[12];
  mat[13] = a[13] - b[13];
  mat[14] = a[14] - b[14];
  mat[15] = a[15] - b[15];

  ptr
}

```

### src\main.rs
```rust
use gmath::dealloc;
use gmath::matrix2;

fn main() {
    let mut matrix = [1.0, 1.0, 1.0, 0.0];
    unsafe {
        // `matrix2invert` returns a result that is freed
        let result = matrix2::matrix2invert(&mut matrix[0]);
        // This would cause a use-after-free
        // let mat = std::slice::from_raw_parts(result as *mut f32, 4);
        // dealloc(result, std::mem::size_of::<f32>() * 4);

        // let mat = Vec::from_raw_parts(result as *mut f32, 4, 4);
        // println!("outside: {} {} {} {}", mat[0], mat[1], mat[2], mat[3]);
        let ptr = result as *mut f32;
        *ptr.offset(0) = 1.0;
        *ptr.offset(1) = 2.0;
        *ptr.offset(2) = 3.0;
        *ptr.offset(3) = 4.0;
        *ptr.offset(4) = 5.0;
        println!(
            "{} {} {} {} {}",
            *ptr.offset(0),
            *ptr.offset(1),
            *ptr.offset(2),
            *ptr.offset(3),
            *ptr.offset(4),
        );
        // dealloc(result, std::mem::size_of::<f32>() * 4);
    }
}

```

## mirchecker__trophy-case__qrcode-generator-test
### src\main.rs
```rust
// This would cause an integer overflow
// https://github.com/magiclen/qrcode-generator/issues/2

use qrcode_generator::to_image_from_str;
use qrcode_generator::QrCodeEcc;

fn main() {
    to_image_from_str("hello", QrCodeEcc::Low, std::usize::MAX);
}

```

## mirchecker__trophy-case__r1cs-test
### src\main.rs
```rust
// This would cause a division-by-zero
// https://github.com/mir-protocol/r1cs/issues/11
use r1cs::Bn128;
use r1cs::Element;
use r1cs::MdsMatrix;
use r1cs::RescueBuilder;

fn main() {
    let mut builder = RescueBuilder::<Bn128>::new(0);
    let matrix = MdsMatrix::<Bn128>::new(vec![vec![Element::zero()]]);
    builder.mds_matrix(matrix);
    builder.build();
}

```

## mirchecker__trophy-case__r1cs-test2
### src\main.rs
```rust
// This would cause an out-of-range access
// https://github.com/mir-protocol/r1cs/issues/11

use r1cs::Bn128;
use r1cs::MdsMatrix;

fn main() {
    MdsMatrix::<Bn128>::new(vec![]);
}

```

## mirchecker__trophy-case__runes-test
### src\main.rs
```rust
// This would cause an integer overflow
// https://github.com/Determinant/runes/issues/1

use runes::utils::load_prefix;
use runes::utils::Read;

struct A {}

impl Read for A {
    fn read(&mut self, _buf: &mut [u8]) -> Option<usize> {
        None
    }
}

fn main() {
    load_prefix(&mut [1], 10, &mut A {});
}

```

## mirchecker__trophy-case__runes-test2
### src\main.rs
```rust
// This would cause a division-by-zero
// https://github.com/Determinant/runes/issues/1

use runes::utils::Sampler;

fn main() {
    Sampler::new(0, 0);
}

```

## mirchecker__trophy-case__safe-transmute-test
### src\main.rs
```rust
// use safe_transmute::base::transmute_many;
use safe_transmute::guard::AllOrNothingGuard;
use safe_transmute::guard::Guard;
use safe_transmute::guard::PedanticGuard;

struct Zst;

fn main() {
    // let _a = transmute_many::<Zst, SingleManyGuard>(&[0x00, 0x01, 0x00, 0x02]);
    println!("{:?}", AllOrNothingGuard::check::<Zst>(&[0x00, 0x01]));
    println!("{:?}", PedanticGuard::check::<Zst>(&[0x00, 0x01]));
}

```

## mirchecker__trophy-case__scriptful-test
### src\main.rs
```rust
// This would call `unwrap` on `None`
// https://github.com/aesedepece/scriptful/issues/1

use scriptful::op_systems::pokemon::{pokemon_op_sys, Command::*};
use scriptful::prelude::*;

fn main() {
    let mut machine = Machine::new(&pokemon_op_sys);
    machine.operate(&Item::Operator(Evolute));
}

```

## mirchecker__trophy-case__spglib-test
### src\main.rs
```rust
use spglib::dataset::Dataset;
use spglib_sys::spg_get_dataset;
use std::convert::TryFrom;

fn main() {
    let mut lattice = [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 3.0]];
    // This unsafe is OK, it calls an external C API to construct a dataset
    let spglib_dataset_ptr =
        unsafe { spg_get_dataset(&mut lattice[0], &mut [0.0, 0.0, 0.0], &1, 1, 0.00001) };

    // This would cause a double-free, because `try_from` gets ownership from input
    // So we basically construct two aliases of the dataset
    let dataset1 = Dataset::try_from(spglib_dataset_ptr);
    let dataset2 = Dataset::try_from(spglib_dataset_ptr);
}

```

## rudra__cases__panic_double_free
### src\main.rs
```rust
use std::ptr;

// Panic-safety bug: double free if `f` panics before we forget the original.
pub fn bad<F: FnOnce(String)>(s: String, f: F) {
    unsafe {
        let dup = ptr::read(&s); // duplicate ownership of s
        f(dup); // user-provided closure may panic while owning dup
        std::mem::forget(s); // avoid double free on normal path
    }
}

fn main() {
    let s = String::from("hello");
    bad(s, |owned| {
        let _ = owned.len();
        panic!("boom");
    });
}

```

## rudra__cases__panic_safe_guard
### src\main.rs
```rust
use std::mem::ManuallyDrop;
use std::ptr;

// Panic-safe variant using ManuallyDrop to avoid double free.
unsafe fn ok<F: FnOnce()>(v: Vec<u8>, f: F) {
    let mut v = ManuallyDrop::new(v);
    let _dup = ptr::read(&*v); // duplicate without automatic drop
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(f));
    // Always forget the duplicate; no double free on unwind.
    std::mem::forget(_dup);
    // Explicitly drop once.
    ManuallyDrop::drop(&mut v);
    let _ = result; // ignore panic for this demo
}

fn main() {
    let v = vec![10, 20, 30];
    unsafe {
        ok(v, || {
            if 2 + 2 == 4 { panic!("boom"); }
        });
    }
}

```

## rudra__tests__panic_safety__insertion_sort.rs
### rudra__tests__panic_safety__insertion_sort.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["UnsafeDataflow"]
```
!*/

use std::ptr;

fn insertion_sort_unsafe<T: Ord>(arr: &mut [T]) {
    unsafe {
        for i in 1..arr.len() {
            let item = ptr::read(&arr[i]);
            let mut j = i - 1;
            while j >= 0 && arr[j] > item {
                j = j - 1;
            }
            ptr::copy(&mut arr[j + 1], &mut arr[j + 2], i - j - 1);
            ptr::write(&mut arr[j + 1], item);
        }
    }
}

```

## rudra__tests__panic_safety__order_safe.rs
### rudra__tests__panic_safety__order_safe.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

use std::fmt::Debug;

fn test_order_safe<I: Iterator<Item = impl Debug>>(mut iter: I) {
    println!("{:?}", iter.next());
    unsafe {
        std::ptr::read(1234 as *const i32);
    }
}

```

## rudra__tests__panic_safety__order_safe_if.rs
### rudra__tests__panic_safety__order_safe_if.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

use std::fmt::Debug;

fn test_order_safe_if<I: Iterator<Item = impl Debug>>(mut iter: I) {
    if true {
        unsafe {
            std::ptr::read(1234 as *const i32);
        }
    } else {
        println!("{:?}", iter.next());
    }
}

```

## rudra__tests__panic_safety__order_safe_loop.rs
### rudra__tests__panic_safety__order_safe_loop.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

use std::fmt::Debug;

fn test_order_safe_loop<I: Iterator<Item = impl Debug>>(mut iter: I) {
    for item in iter {
        unsafe {
            // `read` on `Copy` is safe.
            std::ptr::read(1234 as *const i32);
        }
    }
}

```

## rudra__tests__panic_safety__order_unsafe.rs
### rudra__tests__panic_safety__order_unsafe.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["UnsafeDataflow"]
```
!*/

use std::fmt::Debug;

fn test_order_unsafe<I: Iterator<Item = impl Debug>>(mut iter: I) {
    unsafe {
        std::ptr::read(&Box::new(1234) as *const _);
    }
    println!("{:?}", iter.next());
}

```

## rudra__tests__panic_safety__order_unsafe_loop.rs
### rudra__tests__panic_safety__order_unsafe_loop.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["UnsafeDataflow"]
```
!*/

use std::fmt::Debug;

fn test_order_unsafe_loop<I: Iterator<Item = impl Debug>>(mut iter: I) {
    // Non-Copy type
    let non_copy = Box::new(1234);
    for item in iter {
        unsafe {
            std::ptr::read(&non_copy);
        }
    }
}

```

## rudra__tests__panic_safety__order_unsafe_transmute.rs
### rudra__tests__panic_safety__order_unsafe_transmute.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["UnsafeDataflow"]
```
!*/

use std::fmt::Debug;

fn test_order_unsafe<I: Iterator<Item = impl Debug>>(mut iter: I) {
    unsafe {
        std::mem::transmute::<_, *mut i32>(1234 as *const i32);
    }
    println!("{:?}", iter.next());
}

```

## rudra__tests__panic_safety__pointer_to_ref.rs
### rudra__tests__panic_safety__pointer_to_ref.rs
```rust
/*!
```rudra-test
test_type = "fn"
expected_analyzers = []
```
!*/

use std::fmt::Debug;

fn test_order_unsafe<I: Iterator<Item = impl Debug>>(mut iter: I) {
    unsafe {
        let _ = &*(1234 as *const i32);
    }
    println!("{:?}", iter.next());
}

```

## rudra__tests__panic_safety__vec_push_all.rs
### rudra__tests__panic_safety__vec_push_all.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["UnsafeDataflow"]
```
!*/

pub struct MyVec<T>(Vec<T>);

impl<T: Clone> MyVec<T> {
    // Example from: https://doc.rust-lang.org/nomicon/exception-safety.html#vecpush_all
    fn push_all(&mut self, to_push: &[T]) {
        self.0.reserve(to_push.len());
        unsafe {
            // can't overflow because we just reserved this
            self.0.set_len(self.0.len() + to_push.len());

            for (i, x) in to_push.iter().enumerate() {
                // Clone might panic
                self.0.as_mut_ptr().offset(i as isize).write(x.clone());
            }
        }
    }
}

```

## rudra__tests__send_sync__no_generic.rs
### rudra__tests__send_sync__no_generic.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

// `Sync` or `Send` is implemented for a struct without generic parameters
// In most of the case, this is fine
struct Atom(usize);

unsafe impl Sync for Atom {}
unsafe impl Send for Atom {}

```

## rudra__tests__send_sync__okay_channel.rs
### rudra__tests__send_sync__okay_channel.rs
```rust
/*!
```rudra-test
test_type = "fp"
expected_analyzers = ["SendSyncVariance"]
```
!*/

#![allow(dead_code)]
// This is valid for channel-like types that only transfers the ownership.
// This is invalid if the outer type implements dereference or peek functionality.
// SendSyncVariance analyzer reports low-sensitivity report for this pattern.
struct Channel<P, Q>(P, Q);
unsafe impl<P: Send, Q: Send> Sync for Channel<P, Q> {}

impl<P, Q> Channel<P, Q> {
    fn send_p<M>(&self, _msg: M)
    where
        M: Into<P>,
    {
    }
    fn send_q(&self, _msg: Box<Q>) {}
}

```

## rudra__tests__send_sync__okay_imm.rs
### rudra__tests__send_sync__okay_imm.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

struct Atom<P>(P);
unsafe impl<P: Ord + Sync> Sync for Atom<P> {}

```

## rudra__tests__send_sync__okay_negative.rs
### rudra__tests__send_sync__okay_negative.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/
#![feature(negative_impls)]

struct Negative<T>(T);

impl<T> !Send for Negative<T> {}
impl<T> !Sync for Negative<T> {}

```

## rudra__tests__send_sync__okay_phantom.rs
### rudra__tests__send_sync__okay_phantom.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["SendSyncVariance"]
```
!*/

use std::marker::PhantomData;

struct Atom1<'a, P, Q, R> {
    _marker0: PhantomData<P>,
    _marker1: PhantomData<Option<*mut P>>,
    _marker2: PhantomData<Box<(&'a mut Q, Box<Result<R, i32>>)>>,
}
unsafe impl<'a, A: Send, B, C> Send for Atom1<'a, A, B, C> {}
unsafe impl<'a, A: Sync, B, C> Sync for Atom1<'a, A, B, C> {}

```

## rudra__tests__send_sync__okay_ptr_like.rs
### rudra__tests__send_sync__okay_ptr_like.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

// impl `Send` for `PtrLike<Sync>` is okay
// Note that we don't check pointer-likeness yet

struct Atom1<P>(P);
unsafe impl<P: Sync> Send for Atom1<P> {}

struct Atom2<P>(P);
unsafe impl<P> Send for Atom2<P> where P: Sync {}

```

## rudra__tests__send_sync__okay_transitive.rs
### rudra__tests__send_sync__okay_transitive.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

trait Foo: Sync {}

// `Foo` is `Sync`, so this is okay.
struct Atom0<P>(P);
unsafe impl<P: Eq + Foo> Sync for Atom0<P> {}

// `Foo` is `Sync`, which means `Foo` is also `Send`. This is also okay.
struct Atom1<P>(P);
unsafe impl<P: Eq> Send for Atom1<P> where P: Foo {}

```

## rudra__tests__send_sync__okay_where.rs
### rudra__tests__send_sync__okay_where.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

struct Atom1<P, Q>(P, Q);
unsafe impl<P, Q> Send for Atom1<P, Q>
where
    Q: Send,
    P: Copy + Send,
{
}

struct Atom2<P>(P);
unsafe impl<P> Sync for Atom2<P> where P: Sync {}

```

## rudra__tests__send_sync__sync_over_send_fp.rs
### rudra__tests__send_sync__sync_over_send_fp.rs
```rust
/*!
```rudra-test
test_type = "fp"
expected_analyzers = ["SendSyncVariance"]
```
!*/

// This is valid for channel-like types that only transfers the ownership.
// This is invalid if the outer type implements dereference or peek functionality.
// We emit error by default for now.
struct Channel<P, Q>(P, Q);
unsafe impl<P: Sync, Q: Send> Sync for Channel<P, Q> {}

```

## rudra__tests__send_sync__wild_channel.rs
### rudra__tests__send_sync__wild_channel.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["SendSyncVariance"]
```
!*/

#![allow(dead_code)]
// This is valid for channel-like types that only transfers the ownership.
// This is invalid if the outer type implements dereference or peek functionality.
// We emit error by default for now.
struct Container<P, Q>(P, Q);
unsafe impl<P: Sync, Q: Send> Sync for Container<P, Q> {}

impl<P, Q> Container<P, Q> {
    fn append_to_queue(&self, _msg: Q) {}

    fn peek_queue_end(&self) -> Result<&Q, ()> {
        Ok(&self.1)
    }
}

```

## rudra__tests__send_sync__wild_phantom.rs
### rudra__tests__send_sync__wild_phantom.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["SendSyncVariance"]
```
!*/

use std::marker::PhantomData;
use std::ptr::NonNull;

struct Atom1<'a, T> {
    ptr: NonNull<T>,
    _marker1: PhantomData<&'a mut T>,
}
unsafe impl<'a, A> Send for Atom1<'a, A> {}
unsafe impl<'a, A> Sync for Atom1<'a, A> {}

```

## rudra__tests__send_sync__wild_send.rs
### rudra__tests__send_sync__wild_send.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["SendSyncVariance"]
```
!*/

struct Atom<P>(P);
unsafe impl<P: Ord> Send for Atom<P> {}

```

## rudra__tests__send_sync__wild_sync.rs
### rudra__tests__send_sync__wild_sync.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["SendSyncVariance"]
```
!*/

struct Atom<P, Q>(P, Q);
unsafe impl<P: Send, Q> Sync for Atom<P, Q>
where
    Q: Copy,
    P: Sync,
{
}

```

## rudra__tests__unsafe_destructor__copy_filter.rs
### rudra__tests__unsafe_destructor__copy_filter.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

pub fn test_copy1<F>(f: F)
where
    F: FnOnce(),
{
    unsafe {
        core::ptr::read(0x1234 as *const u8);
    }
    f();
}

pub fn test_copy2<F, T>(f: F)
where
    F: FnOnce(),
    T: Copy,
{
    unsafe {
        core::ptr::read(0x1234 as *const T);
    }
    f();
}

pub fn test_copy3<F, T, U>(f: F)
where
    F: FnOnce(),
    U: Copy,
{
    unsafe {
        core::ptr::read(0x1234 as *const T as *const U);
    }
    f();
}

```

## rudra__tests__unsafe_destructor__ffi.rs
### rudra__tests__unsafe_destructor__ffi.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

extern "C" {
    fn extern_unsafe(x: u8);
}

pub struct MyStruct(u8);

// calling extern unsafe function should not alarm
impl Drop for MyStruct {
    fn drop(&mut self) {
        unsafe {
            extern_unsafe(self.0);
        }
    }
}

```

## rudra__tests__unsafe_destructor__fp1.rs
### rudra__tests__unsafe_destructor__fp1.rs
```rust
/*!
```rudra-test
test_type = "fp"
expected_analyzers = ["UnsafeDestructor"]
```
!*/

pub struct Leak<'a> {
    vec: &'a mut Vec<u32>,
}

// calling an actual unsafe function, needs developer triage
// this case, memory is leaked but it is not UB
impl Drop for Leak<'_> {
    fn drop(&mut self) {
        unsafe {
            self.vec.set_len(0);
        }
    }
}

```

## rudra__tests__unsafe_destructor__normal1.rs
### rudra__tests__unsafe_destructor__normal1.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = []
```
!*/

// types without unsafe code should not be reported
pub struct NoDrop {
    vec: Vec<u32>,
}

pub struct FooSafe<'a> {
    vec: &'a mut Vec<u32>,
}

impl Drop for FooSafe<'_> {
    fn drop(&mut self) {
        println!("{}", self.vec.len());
    }
}

pub struct BarSafe {
    vec: Vec<u32>,
}

impl Drop for BarSafe {
    fn drop(&mut self) {
        println!("{}", self.vec.len());
    }
}

```

## rudra__tests__unsafe_destructor__normal2.rs
### rudra__tests__unsafe_destructor__normal2.rs
```rust
/*!
```rudra-test
test_type = "normal"
expected_analyzers = ["UnsafeDestructor"]
```
!*/

// RUSTSEC-2020-0032 simplified
use std::os::raw::c_char;

pub struct StrcCtx {
    pub ptr: *mut c_char,
}

impl Drop for StrcCtx {
    fn drop(&mut self) {
        unsafe {
            let _ = std::ffi::CString::from_raw(self.ptr as *mut std::os::raw::c_char);
        }
    }
}

```

## rudra__tests__utility__generic_param_ctxts.rs
### rudra__tests__utility__generic_param_ctxts.rs
```rust
#![allow(dead_code)]

// B.index = 1
struct My<A, B> {
    val1: A,
    val2: B,
}

// B.index = 2
// By using `generic_param_idx_map`, we can retrieve the original index 1.
unsafe impl<'a, A: 'a + Send, B: Sync> Sync for My<A, B>
    where B: Fn(&'a A)
{}

impl<'a, A: 'a + Send, B: Sync> My<A, B>
    where B: Fn(&'a A)
{
    // C.index = 3
    pub fn hello<'b, C>(&self, x: C, y: &'b B) {}
}

```

## rudra__tests__utility__identify_generic_params.rs
### rudra__tests__utility__identify_generic_params.rs
```rust
// Test case to check whether our implementation can successfully identify
// same generic parameters in multiple impl blocks with different indices.
#![allow(dead_code)]
struct My<A, B> {
    val1: A,
    val2: B,
}

unsafe impl<'a, F: Send> Send for My<i32, F> // F.index = 1
    where F: Fn(&'a u32) -> &'a u32 {}

unsafe impl<F: Sync> Sync for My<i32, F> // F.index = 0
    where F: Fn(&u32) -> &u32 {}

// unsafe impl<A: Sync, B: Sync> Sync for My<B, A> {}
    
impl<F> My<i32, F> {
    fn foo(&self) {}
}

impl<A, B> My<A, B> {
    fn bar(&self) {}
}

```

## rudra__tests__utility__report_handle_macro.rs
### rudra__tests__utility__report_handle_macro.rs
```rust
use std::marker::PhantomData;
use std::cell::UnsafeCell;

pub struct Opaque(PhantomData<UnsafeCell<*mut ()>>);

macro_rules! generic_foreign_type_and_impl_send_sync {
    (
        $(#[$impl_attr:meta])*
        type CType = $ctype:ty;
        fn drop = $drop:expr;
        $(fn clone = $clone:expr;)*

        $(#[$owned_attr:meta])*
        pub struct $owned:ident<T>;
        $(#[$borrowed_attr:meta])*
        pub struct $borrowed:ident<T>;
    ) => {
        $(#[$owned_attr])*
        pub struct $owned<T>(*mut $ctype, Box<T>);

        $(#[$borrowed_attr])*
        pub struct $borrowed<T>(Opaque, Box<T>);

        unsafe impl<T> Send for $owned<T>{}
        unsafe impl<T> Send for $borrowed<T>{}
        unsafe impl<T> Sync for $owned<T>{}
        unsafe impl<T> Sync for $borrowed<T>{}
    };
}

pub enum X509_LOOKUP_METHOD {}

extern "C" {
    pub fn X509_LOOKUP_meth_free(method: *mut X509_LOOKUP_METHOD);
}

generic_foreign_type_and_impl_send_sync! {
    type CType = X509_LOOKUP_METHOD;
    fn drop = |_method| {
        ffi::X509_LOOKUP_meth_free(_method);
    };

    /// Method used to look up certificates and CRLs.
    pub struct X509LookupMethod<T>;
    /// Reference to an `X509LookupMethod`.
    pub struct X509LookupMethodRef<T>;
}

```

## rudra__tests__utility__rudra_paths_discovery.rs
### rudra__tests__utility__rudra_paths_discovery.rs
```rust
// cargo run --bin rudra -- --crate-type lib tests/utility/rudra_paths_discovery.rs
use std::ptr::NonNull;

struct PathsDiscovery;

impl PathsDiscovery {
    fn discover() {
        unsafe {
            // Strong bypasses
            std::ptr::read(12 as *const i32);
            (12 as *const i32).read();

            std::intrinsics::copy(12 as *const i32, 34 as *mut i32, 56);
            std::intrinsics::copy_nonoverlapping(12 as *const i32, 34 as *mut i32, 56);
            std::ptr::copy(12 as *const i32, 34 as *mut i32, 56);
            std::ptr::copy_nonoverlapping(12 as *const i32, 34 as *mut i32, 56);

            vec![12, 34].set_len(5678);
            std::vec::Vec::from_raw_parts(12 as *mut i32, 34, 56);

            // Weak bypasses
            std::mem::transmute::<_, *mut i32>(12 as *const i32);

            (12 as *mut i32).write(34);
            std::ptr::write(12 as *mut i32, 34);

            (12 as *const i32).as_ref();
            (12 as *mut i32).as_mut();

            let mut ptr = NonNull::new(1234 as *mut i32).unwrap();
            ptr.as_ref();
            ptr.as_mut();

            [12, 34].get_unchecked(0);
            [12, 34].get_unchecked_mut(0);

            std::ptr::slice_from_raw_parts(12 as *const i32, 34);
            std::ptr::slice_from_raw_parts_mut(12 as *mut i32, 34);
            std::slice::from_raw_parts(12 as *const i32, 34);
            std::slice::from_raw_parts_mut(12 as *mut i32, 34);

            // Generic function call
            std::intrinsics::drop_in_place(12 as *mut i32);
            std::ptr::drop_in_place(12 as *mut i32);
            (12 as *mut i32).drop_in_place();
        }
    }
}

```



