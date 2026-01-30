# tools 使用手册（Docker）

本目录包含 Rudra、FFIChecker、MirChecker 的 Docker 构建/启动脚本，以及一键检测脚本。

## 通用：如何启动 Docker

1. 启动 Docker Desktop。
2. 验证：

```powershell
docker info
```

如果能输出 Client/Server 信息，说明 Docker 已就绪。

## 通用：查看当前已启动的 Docker 容器

```powershell
docker ps
```

只看名称、镜像和状态：
```powershell
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
```

## Rudra

### 构建镜像
```powershell
cd D:\毕业论文\paper_rustSec\tools\Rudra
.\build_rudra.ps1
```

### 运行容器（交互式）
```powershell
.\run_rudra_docker.ps1
```

### 一键检测某个 case
```powershell
.\run_rudra.ps1 -Case tests\panic_safety\order_safe_if
```

## FFIChecker

### 构建镜像
```powershell
cd D:\毕业论文\paper_rustSec\tools\FFIChecker
.\build_ffi_checker.ps1
```

### 运行容器（交互式）
```powershell
.\run_ffi_checker_docker.ps1
```

### 一键检测某个 case
```powershell
.\run_ffi_checker.ps1 -Target examples\rust-uaf-df -Precision low
```

（可选）批量/选择性测试：
```powershell
.\run_ffi_checker_all.ps1 -List
.\run_ffi_checker_all.ps1 -Case examples\rust-uaf-df
```

## MirChecker

### 构建镜像
```powershell
cd D:\毕业论文\paper_rustSec\tools\mirchecker
.\build_mir_checker.ps1
```

### 运行容器（交互式）
```powershell
.\run_mir_checker_docker.ps1
```

### 一键检测某个 case
```powershell
# 以 Cargo 项目目录为目标
.\run_mir_checker.ps1 -Target tests\safe-bugs\division-by-zero -Domain interval -Entry main

# 以单个 .rs 文件为目标
.\run_mir_checker_file.ps1 -Target tests\safe-bugs\division-by-zero\src\main.rs -Domain interval -Entry main
```

## 常见问题

- 提示镜像不存在：先运行对应的 `build_*.ps1`。
- 网络不稳定：可重试构建或在空闲时段再试。
