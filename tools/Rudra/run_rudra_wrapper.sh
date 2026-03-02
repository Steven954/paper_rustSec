#!/bin/bash
set -e
# 与 MirChecker 一致：重定向 crates.io-index 到 USTC 镜像
git config --global url.'https://mirrors.ustc.edu.cn/crates.io-index'.insteadOf 'https://github.com/rust-lang/crates.io-index'
exec "$@"
