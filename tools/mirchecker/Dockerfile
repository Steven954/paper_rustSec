# MirChecker container image for deterministic builds/runs
FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:/opt/llvm15/bin:$PATH \
    RUSTUP_TOOLCHAIN=nightly-2020-12-29 \
    RUSTUP_DIST_SERVER=https://mirrors.ustc.edu.cn/rust-static \
    RUSTUP_UPDATE_ROOT=https://mirrors.ustc.edu.cn/rustup \
    CARGO_NET_GIT_FETCH_WITH_CLI=true \
    LIBCLANG_PATH=/opt/llvm15/lib/libclang.so \
    RUSTFLAGS="-Clink-args=-fuse-ld=lld"

RUN set -eux; \
    pkgs="curl ca-certificates git build-essential pkg-config cmake python3 libgmp-dev libmpfr-dev libppl-dev libz3-dev wget xz-utils lld m4 file"; \
    try_mirror() { \
      base="$1"; sec="$2"; \
      printf "deb %s bullseye main\n" "$base" > /etc/apt/sources.list; \
      printf "deb %s bullseye-updates main\n" "$base" >> /etc/apt/sources.list; \
      printf "deb %s bullseye-security main\n" "$sec" >> /etc/apt/sources.list; \
      apt-get -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false update; \
      for i in 1 2 3; do \
        if DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false -o Acquire::Retries=3 install -y --no-install-recommends --fix-missing $pkgs; then \
          return 0; \
        fi; \
        sleep 3; \
      done; \
      return 1; \
    }; \
    (try_mirror https://mirrors.aliyun.com/debian https://mirrors.aliyun.com/debian-security) || \
    (try_mirror https://mirrors.cloud.tencent.com/debian https://mirrors.cloud.tencent.com/debian-security) || \
    (try_mirror https://mirrors.163.com/debian https://mirrors.163.com/debian-security) || \
    (try_mirror https://mirrors.ustc.edu.cn/debian https://mirrors.ustc.edu.cn/debian-security) || \
    (try_mirror https://mirrors.tuna.tsinghua.edu.cn/debian https://mirrors.tuna.tsinghua.edu.cn/debian-security) || \
    (try_mirror https://deb.debian.org/debian https://security.debian.org/debian-security); \
    rm -rf /var/lib/apt/lists/*

# Install Rust and required components
RUN set -eux; \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      https://mirrors.ustc.edu.cn/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init || \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      https://mirrors.ustc.edu.cn/rust-static/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init || \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      http://mirrors.ustc.edu.cn/rust-static/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init || \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      https://rsproxy.cn/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init || \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      https://static.rust-lang.org/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init; \
    chmod +x /tmp/rustup-init; \
    installed=0; \
    for i in 1 2 3; do \
      if RUSTUP_INIT_SKIP_PATH_CHECK=yes CARGO_HOME=/usr/local/cargo RUSTUP_HOME=/usr/local/rustup /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain ${RUSTUP_TOOLCHAIN}; then \
        installed=1; \
        break; \
      fi; \
      echo "rustup-init failed (ustc), retry $i" >&2; \
      rm -rf /usr/local/cargo /usr/local/rustup; \
      sleep 5; \
    done; \
    if [ "$installed" -ne 1 ]; then \
      RUSTUP_DIST_SERVER=https://static.rust-lang.org RUSTUP_UPDATE_ROOT=https://static.rust-lang.org/rustup \
        RUSTUP_INIT_SKIP_PATH_CHECK=yes CARGO_HOME=/usr/local/cargo RUSTUP_HOME=/usr/local/rustup /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain ${RUSTUP_TOOLCHAIN}; \
    fi; \
    /usr/local/cargo/bin/rustup --version; \
    added=0; \
    for i in 1 2 3; do \
      if /usr/local/cargo/bin/rustup component add rustc-dev llvm-tools-preview --toolchain ${RUSTUP_TOOLCHAIN}; then \
        added=1; \
        break; \
      fi; \
      echo "rustup component add failed (ustc), retry $i" >&2; \
      sleep 5; \
    done; \
    if [ "$added" -ne 1 ]; then \
      RUSTUP_DIST_SERVER=https://static.rust-lang.org /usr/local/cargo/bin/rustup component add rustc-dev llvm-tools-preview --toolchain ${RUSTUP_TOOLCHAIN}; \
    fi; \
    /usr/local/cargo/bin/rustup default ${RUSTUP_TOOLCHAIN}; \
    rm /tmp/rustup-init

# Download LLVM/Clang 15 (required by bindgen)
RUN set -eux; \
    cd /opt; \
    LLVM_TAR=clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04.tar.xz; \
    download_ok=0; \
    for url in \
      "https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/${LLVM_TAR}" \
      "https://mirror.ghproxy.com/https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/${LLVM_TAR}" \
      "https://ghproxy.com/https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/${LLVM_TAR}"; do \
      for i in 1 2 3; do \
        if curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused -o ${LLVM_TAR} "${url}"; then \
          download_ok=1; \
          break; \
        fi; \
        sleep 3; \
      done; \
      if [ "$download_ok" -eq 1 ]; then break; fi; \
    done; \
    if [ "$download_ok" -ne 1 ]; then \
      echo "Failed to download ${LLVM_TAR} from all mirrors." >&2; \
      exit 1; \
    fi; \
    tar -xJf ${LLVM_TAR}; \
    mv clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04 llvm15; \
    rm ${LLVM_TAR}; \
    ln -s /opt/llvm15/bin/llvm-config /usr/local/bin/llvm-config || true

WORKDIR /workspace

ENTRYPOINT ["/bin/bash"]
