#![feature(cell_leak)]
#![cfg_attr(feature = "driver", feature(rustc_private))]
#![feature(box_patterns)]

#[cfg(feature = "driver")]
extern crate rustc_ast;
#[cfg(feature = "driver")]
extern crate rustc_data_structures;
#[cfg(feature = "driver")]
extern crate rustc_driver;
#[cfg(feature = "driver")]
extern crate rustc_errors;
#[cfg(feature = "driver")]
extern crate rustc_hir;
#[cfg(feature = "driver")]
extern crate rustc_index;
#[cfg(feature = "driver")]
extern crate rustc_interface;
#[cfg(feature = "driver")]
extern crate rustc_middle;
#[cfg(feature = "driver")]
extern crate rustc_session;
#[cfg(feature = "driver")]
extern crate rustc_span;
#[cfg(feature = "driver")]
extern crate rustc_target;

pub mod utils;

#[cfg(feature = "driver")]
pub mod entry_collection {
    pub mod callback;
}

#[cfg(feature = "analysis")]
pub mod analysis {
    pub mod abstract_domain;
    pub mod block_visitor;
    pub mod context;
    pub mod diagnosis;
    pub mod known_names;
    pub mod option;
    pub mod summary;
    pub mod taint_analysis;
}
