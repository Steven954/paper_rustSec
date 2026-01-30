use std::vec::Vec;

fn main() {
    let mut a = vec![1, 2];
    let ptr = a.as_mut_ptr();
    unsafe {
        let _v = Vec::from_raw_parts(ptr, 2, 2);
    }
}
