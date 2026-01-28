# Rudra 操作手册（本地用例）

本手册说明如何在本机使用 Docker 运行 Rudra，并测试两组样例：
- `panic_double_free`（应当被 Rudra 报警）
- `panic_safe_guard`（不应报警）

## 前置条件
- Docker Desktop 已启动
- Rudra 镜像已构建完成（`rudra:latest`）

## 另一台电脑的 Docker 配置（国内镜像）

以下步骤用于在另一台电脑上配置 Docker 镜像源，避免拉取/构建失败。

### 1) 安装并启动 Docker Desktop
- 安装 Docker Desktop（默认 WSL2 模式）
- 首次启动后确认 Docker 正常运行

### 2) 配置镜像源（中科大 + 备用）
在 PowerShell 中执行（会覆盖/创建配置文件）：  
```powershell
$json='{"registry-mirrors":["https://docker.mirrors.ustc.edu.cn","https://docker.m.daocloud.io","https://hub-mirror.c.163.com","https://mirror.ccs.tencentyun.com"]}'

# 当前用户配置
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.docker" | Out-Null
[System.IO.File]::WriteAllText("$env:USERPROFILE\.docker\daemon.json",$json,[System.Text.UTF8Encoding]::new($false))

# 系统级配置（部分环境需要）
New-Item -ItemType Directory -Force -Path "C:\ProgramData\Docker\config" | Out-Null
[System.IO.File]::WriteAllText("C:\ProgramData\Docker\config\daemon.json",$json,[System.Text.UTF8Encoding]::new($false))
```

### 3) 重启 Docker Desktop 并验证
- 关闭并重启 Docker Desktop（确保新配置生效）
- 执行：
```powershell
docker info --format 'Mirrors: {{.RegistryConfig.Mirrors}}'
```
应能看到镜像源列表。

### 4) 构建 Rudra 镜像
在 `d:\毕业论文\tools\Rudra` 目录执行：
```powershell
docker build . -t rudra:latest
```

> 说明：本项目的 `Dockerfile` 已改用 `rsproxy.cn` 作为 rustup 下载源，避免 `static.rust-lang.org` 连接失败。若你需要恢复官方源，可自行将 `RUSTUP_DIST_SERVER` 相关配置改回官方地址。

## 目录结构
```
d:\毕业论文\tools\Rudra\cases\panic_double_free
└─ src\main.rs

d:\毕业论文\tools\Rudra\cases\panic_safe_guard
└─ src\main.rs
```

## 运行方式（PowerShell）

### 1) 运行 `panic_double_free`（应有告警）
```powershell
$env:RUDRA_RUNNER_HOME = "d:\毕业论文\tools\Rudra\rudra-home"
$target = "d:\毕业论文\tools\Rudra\cases\panic_double_free"

docker run -t --rm `
  -v "$env:RUDRA_RUNNER_HOME:/tmp/rudra-runner-home" `
  --env CARGO_HOME=/tmp/rudra-runner-home/cargo_home `
  --env SCCACHE_DIR=/tmp/rudra-runner-home/sccache_home `
  --env SCCACHE_CACHE_SIZE=10T `
  --env RUSTUP_TOOLCHAIN=nightly-2021-10-21 `
  -v "$target:/tmp/rudra" -w /tmp/rudra rudra:latest cargo rudra
```

预期输出包含类似：
```
Warning (UnsafeDataflow:/ReadFlow): Potential unsafe dataflow issue in `bad`
```

### 2) 运行 `panic_safe_guard`（不应报警）
```powershell
$env:RUDRA_RUNNER_HOME = "d:\毕业论文\tools\Rudra\rudra-home"
$target = "d:\毕业论文\tools\Rudra\cases\panic_safe_guard"

docker run -t --rm `
  -v "$env:RUDRA_RUNNER_HOME:/tmp/rudra-runner-home" `
  --env CARGO_HOME=/tmp/rudra-runner-home/cargo_home `
  --env SCCACHE_DIR=/tmp/rudra-runner-home/sccache_home `
  --env SCCACHE_CACHE_SIZE=10T `
  --env RUSTUP_TOOLCHAIN=nightly-2021-10-21 `
  -v "$target:/tmp/rudra" -w /tmp/rudra rudra:latest cargo rudra
```

## 常见问题
- 若提示 `RUDRA_RUNNER_HOME is not set`，请确认已设置环境变量并且目录存在：
  - `d:\毕业论文\tools\Rudra\rudra-home`

- 若 Docker 无法启动或拉取依赖，请先确保镜像源可用并重启 Docker Desktop。
