# 第 6 章 实验与结果分析

本章基于第五章构建的评测框架，对 Rudra、MirChecker、FFIChecker 三款静态分析工具在 100 个非正常控制流相关测试用例上进行系统评测。首先介绍实验环境与配置，随后给出数据集概览与总体对比结果，分场景分析各工具表现并讨论误差来源，最后总结跨场景能力边界并提出改进建议。

## 6.1 实验环境与配置

### 6.1.1 硬件与操作系统

实验在 Windows 10 环境下执行，使用 PowerShell 作为运行脚本的默认 shell。评测管线通过 Python 3 脚本驱动，各工具在本地或容器化环境中运行。为保障可复现性，所有样例的构建与工具调用均通过 `eval` 目录下的自动化脚本完成，超时时间设置为 1200 秒（20 分钟），以应对部分 FFI 样例所需的 C 编译与链接耗时。

### 6.1.2 工具与依赖版本

评测对象包括：

- Rudra：面向 unsafe 误用与 panic safety 的静态检测工具，基于 Rust 编译器 HIR 进行数据流与模式分析。工具位于 `tools/Rudra`，通过 `run_rudra.ps1` 调用。
- MirChecker：基于 MIR 的约束与路径分析工具，可检测整数溢出、索引越界、除零、panic 可达性等。工具位于 `tools/mirchecker`，通过 `run_mir_checker.ps1` 调用。
- FFIChecker：面向跨语言边界（FFI）的内存安全分析工具，可检测 UAF、double free、内存泄漏等 FFI 相关风险。工具位于 `tools/FFIChecker`，通过 `run_ffi_checker.ps1` 调用。

各工具均使用其官方仓库或评测框架提供的默认版本与配置。样例构建依赖各样例自身携带的 `rust-toolchain.toml`、`Cargo.toml` 及 `Cargo.lock`，确保 Rust 工具链与依赖版本锁定。评测过程中未显式修改 panic 策略，默认采用 panic=unwind 语义。

### 6.1.3 评测流程

评测管线执行顺序为：加载 `testcase_categories.csv` 中的用例列表 → 将各样例拷贝至工具对应 staging 目录 → 依次调用各工具执行脚本 → 收集 stdout/stderr 至 `raw` 目录 → 通过解析器将各工具输出归一化为 `normalized.csv` → 计算指标并生成报告。归一化阶段依据各工具的规则模式（如 Rudra 的 `Warning (rule_id)`、MirChecker 的 `[MirChecker] Provably/Possible error`、FFIChecker 的 `Possible bugs`）判定是否检出漏洞，并将告警与运行状态一并记录。

## 6.2 数据集概览

### 6.2.1 样例总数与来源

评测数据集共包含 100 个 测试用例，覆盖 S1–S4 四类非正常控制流场景。用例来源包括：

- examples：FFIChecker 等工具自带的 FFI 示例（如 `c-in-rust-doublefree`、`c-in-rust-uaf`、`cstring-test` 等），主要归属 S3；
- tests：Rudra、MirChecker 等工具的单元测试与安全测试（如 `safe-bugs`、`unit-tests`、`panic_safety`、`unsafe_destructor`、`send_sync` 等），主要归属 S1、S2、S3、S4；
- trophy-case：来自真实漏洞或 trophy-case 的抽象样例（如 `bitvec-test`、`brotli-test`、`byte-unit-test` 等），主要归属 S2、S4；
- cases：自定义 panic 相关样例（如 `panic_double_free`、`panic_safe_guard`），主要归属 S4。

### 6.2.2 场景分布

表 6-1 给出了各场景的样例数量与占比。

表 6-1 数据集场景分布

| 场景 | 描述 | 样例数 | 占比 |
| :--- | :--- | ---: | ---: |
| S1 | Drop 执行中途发生 panic | 4 | 4% |
| S2 | 未初始化/部分初始化状态下 panic 中断 | 66 | 66% |
| S3 | panic 跨 FFI 边界传播 | 16 | 16% |
| S4 | 自定义资源清理逻辑中 panic | 14 | 14% |
| 合计 | | 100 | 100% |

S2 场景占比最高，反映了“部分初始化 + panic”这一机制在 Rust 安全研究中的典型性；S3 与 S4 分别覆盖 FFI 与手工清理两类边界场景；S1 样例数较少，与真实 Drop 中 panic 的样例相对稀缺有关。

## 6.3 总体对比结果

### 6.3.1 总表：工具 × 场景 → Recall / Executability / 平均耗时

表 6-2 汇总了各工具在各场景下的 Recall（检出率）、Executability（可运行率）及平均运行时间（秒）。

表 6-2 工具 × 场景 评测结果汇总

| 工具 | 场景 | Recall | Executability | 平均耗时 (s) |
| :--- | :--- | ---: | ---: | ---: |
| Rudra | S1 | 75.00% | 100.00% | 1.40 |
| Rudra | S2 | 51.52% | 100.00% | 4.00 |
| Rudra | S3 | 12.50% | 100.00% | 13.84 |
| Rudra | S4 | 57.14% | 100.00% | 1.97 |
| MirChecker | S1 | 25.00% | 100.00% | 4.64 |
| MirChecker | S2 | 19.70% | 100.00% | 7.09 |
| MirChecker | S3 | 0.00% | 93.75% | 3.96 |
| MirChecker | S4 | 0.00% | 100.00% | 4.08 |
| FFIChecker | S1 | 0.00% | 100.00% | 58.80 |
| FFIChecker | S2 | 0.00% | 100.00% | 25.96 |
| FFIChecker | S3 | 68.75% | 100.00% | 21.56 |
| FFIChecker | S4 | 0.00% | 100.00% | 26.96 |

### 6.3.2 总体 Recall 与可运行率

表 6-3 给出各工具在全部 100 个用例上的总体表现。

表 6-3 工具总体指标

| 工具 | 检出用例数 | 总 Recall | 可运行率 | 平均耗时 (s) |
| :--- | ---: | ---: | ---: | ---: |
| Rudra | 47 | 47.00% | 100.00% | 5.19 |
| MirChecker | 14 | 14.00% | 99.00% | 6.07 |
| FFIChecker | 11 | 11.00% | 100.00% | 26.71 |

Rudra 在总体 Recall 上领先，但需注意其部分检出可能来自非安全相关的告警（如编译器警告、cargo metadata 错误等）；MirChecker 在 1 个用例（`rust-in-c-uaf`）上运行失败；FFIChecker 平均耗时最长，但其在 S3 场景下的检出能力显著。

### 6.3.3 关键发现

1. 场景特异性明显：FFIChecker 在 S3 中 Recall 达 68.75%，在 S1、S2、S4 中均为 0%；Rudra 在 S1、S2、S4 中表现较好，在 S3 中仅 12.50%；MirChecker 在 S3、S4 中 Recall 为 0%，在 S1、S2 中有少量检出。
2. 可运行性：除 MirChecker 在 `rust-in-c-uaf` 上失败外，其余工具均可成功运行全部或绝大多数用例。
3. 性能差异：FFIChecker 平均耗时约为 Rudra 的 5 倍、MirChecker 的 4 倍，在 FFI 与 LLVM IR 分析上开销较大。

## 6.4 分场景结果与误差分析

### 6.4.1 场景 S1：Drop 执行中途发生 panic

S1 共 4 个用例：`tests__unsafe-bugs__double-free`、`tests__unsafe_destructor__fp1`、`tests__unsafe_destructor__normal1`、`tests__unsafe_destructor__normal2`。

Rudra：检出 3 个（Recall 75%）。检出类型包括 `UnsafeDestructor`（unsafe block detected in drop）、`UnsafeDataflow` 等。部分用例中 Rudra 报告的是编译器警告（如 `field is never read`），被解析器计入检出，可能带来一定误报。

MirChecker：检出 1 个（Recall 25%）。在 `tests__unsafe-bugs__double-free` 中报告 `Possible error n visit return: double-free or use-after-free`，准确定位了 double free 风险。MirChecker 基于 MIR 的路径分析能够识别部分析构场景下的重复释放。

FFIChecker：未检出任何 S1 用例（Recall 0%）。FFIChecker 面向 FFI 边界，不涉及纯 Rust 析构路径，因此对 S1 无预期能力。

误差分析：S1 样例数少，统计波动较大。Rudra 的误报可能来自对非安全告警的泛化解析；MirChecker 对 S1 的覆盖有限，仅依赖 MIR 层 double free 模式，对更复杂的 Drop 链条中断场景可能漏报。

### 6.4.2 场景 S2：未初始化/部分初始化状态下 panic 中断

S2 共 66 个用例，涵盖 safe-bugs（除零、越界、溢出、类型转换）、unit-tests、trophy-case 等。

Rudra：检出 34 个（Recall 51.52%）。其中相当一部分为误报：包括 `cargo metadata` 依赖解析失败（如 `failed to get macros as a dependency`）、`unused variable`、`unused import`、`struct is never constructed` 等编译器警告。这些输出被解析器误判为“检出”，导致 Recall 虚高。真正与 panic safety 相关的检出如 `UnsafeDataflow`、`SendSyncVariance` 等仅占少数。

MirChecker：检出 13 个（Recall 19.70%）。MirChecker 的检出集中在 `[MirChecker] Provably/Possible error` 类型，包括：除零（`attempt to divide by zero`）、索引越界（`index out of bound`）、整数溢出（`attempt to compute ... which would overflow`）、panic 可达性（`run into panic code`）等。这些与 S2 的“部分初始化 + panic”语义高度相关，误报率较低。

FFIChecker：未检出任何 S2 用例（Recall 0%）。FFIChecker 不分析非 FFI 边界内的内存操作，对 S2 无预期能力。

误差分析：S2 用例来源多样，部分 unit-tests 本身并非设计用于触发 panic 相关漏洞，因此“真值标签”与工具能力存在错位。Rudra 的解析器对 `error`、`warning` 等关键词过于宽松，导致大量非安全告警被计入检出；若进行人工复核，其真实 Recall 应显著低于 51.52%。

### 6.4.3 场景 S3：panic 跨 FFI 边界传播

S3 共 16 个用例，来自 FFIChecker 的 examples 及部分 unsafe_destructor 相关测试。

Rudra：检出 2 个（Recall 12.50%）。检出来自 `examples__mix-box-free`（unused imports）、`examples__mix-mem-allocator`（variable does not need to be mutable）等，均为编译器风格警告，与 FFI 语义无关，属于误报。

MirChecker：检出 0 个（Recall 0%）。在 `rust-in-c-uaf` 上运行失败（error）。MirChecker 不建模 FFI 边界，对跨语言调用的资源所有权与异常传播缺乏分析能力。

FFIChecker：检出 11 个（Recall 68.75%）。FFIChecker 在多数 S3 用例中报告 UAF、double free、内存泄漏等，例如 `c_func: LLVM IR of C code is known. Possible bugs: Use After Free, Double Free, Taint source meets taint sink`。在 `examples__ffi-simplest`、`examples__rust-uaf-df`、`examples__rust-in-c-uaf` 等 5 个用例上未检出。

误差分析：FFIChecker 在 S3 中表现最佳，与其设计目标一致。未检出的用例可能涉及 C 代码未知（LLVM IR 不可用）、函数指针调用等复杂情形。Rudra 的 S3 检出均为误报，说明其解析逻辑需进一步过滤非安全相关输出。

### 6.4.4 场景 S4：自定义资源清理逻辑中 panic

S4 共 14 个用例，包括 `panic_double_free`、`panic_safe_guard`、`insertion_sort`、`order_unsafe` 等 panic safety 与手工清理相关样例。

Rudra：检出 8 个（Recall 57.14%）。部分检出为真实漏洞相关，如 `UnsafeDataflow`、`Potential unsafe dataflow issue in bad`、`Suspicious impl of Send/Sync` 等；部分为 `warning: function is never used`、`unused variable` 等误报。

MirChecker：检出 0 个（Recall 0%）。MirChecker 不针对 S4 的手工清理逻辑与 panic 顺序进行建模，对 scope guard、手动 free 等模式无检测能力。

FFIChecker：未检出任何 S4 用例（Recall 0%）。S4 不涉及 FFI，FFIChecker 无预期能力。

误差分析：S4 是 Rudra 的优势场景之一，其 panic safety 与 Send/Sync 规则能覆盖部分手工清理模式。但 Rudra 的误报（如未使用函数、未使用变量）仍会影响 Precision 评估。MirChecker 与 FFIChecker 对 S4 的结构性盲区符合其设计范围。

## 6.5 跨场景能力边界总结

### 6.5.1 能力边界图谱

基于上述分场景结果，可归纳出三款工具的能力边界：

| 能力维度 | Rudra | MirChecker | FFIChecker |
| :--- | :--- | :--- | :--- |
| S1 Drop 中 panic | ✓ 较强（UnsafeDestructor、UnsafeDataflow） | △ 较弱（double free 模式） | × 无 |
| S2 部分初始化 panic | △ 有检出但误报多 | ✓ 较强（溢出、越界、panic 可达） | × 无 |
| S3 跨 FFI panic | × 无实质能力（仅误报） | × 无 | ✓ 强（UAF、double free、泄漏） |
| S4 手工清理 panic | ✓ 较强（UnsafeDataflow、Send/Sync） | × 无 | × 无 |
| 可运行率 | 100% | 99% | 100% |
| 平均耗时 | 低 | 中 | 高 |

### 6.5.2 结构性限制与可改进点

1. Rudra：面向 unsafe 误用与 panic safety，在 S1、S4 上表现较好，但在 S3 上无实质能力。其输出解析器将 `error`、`warning` 等泛化关键词视为检出，导致大量误报，建议增加规则过滤（如排除 `cargo metadata`、`unused` 等非安全告警）。

2. MirChecker：基于 MIR 的数值与路径分析，在 S2 的溢出、越界、panic 可达性等子类上表现良好，但对 S1 的 Drop 链条、S3 的 FFI、S4 的手工清理均无建模。可考虑扩展 MIR 层对 unwind 路径与 Drop 调用顺序的建模。

3. FFIChecker：专为 FFI 设计，在 S3 中 Recall 达 68.75%，在 S1、S2、S4 中无能力。可考虑与 Rudra 或 MirChecker 组合使用，形成“FFI + 非 FFI”的互补覆盖。

4. 评测框架：当前 Recall 计算未区分真阳性与误报，建议引入人工标注或规则过滤，计算 Precision 与 F1，以更准确反映工具能力。同时，可增加 S1 样例数量，以提升统计稳定性。

## 6.6 本章小结

本章在前述场景分类与评测框架基础上，对 Rudra、MirChecker、FFIChecker 三款静态分析工具在 100 个非正常控制流相关用例上进行了系统评测。实验结果表明：

- 场景特异性显著：FFIChecker 在 S3（跨 FFI panic）中表现最佳（Recall 68.75%），Rudra 在 S1、S4 中领先，MirChecker 在 S2 的数值与路径分析类漏洞上有一定优势。
- 能力边界清晰：各工具在非目标场景下 Recall 多为 0%，符合其设计定位；Rudra 的解析器存在误报，需通过规则过滤提升 Precision。
- 可运行性良好：除 MirChecker 在 1 个用例上失败外，其余工具均可稳定运行；FFIChecker 平均耗时明显高于另外两款工具。

上述结论为理解 Rust 非正常控制流下静态分析工具的能力边界提供了实证依据，也为后续工具改进与评测框架优化指明了方向。
