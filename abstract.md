# 摘要 (Abstract)

## 中文摘要

Rust 语言（Rust Language）作为一种新型系统级编程范式，通过所有权与借用检查，有效解决了底层系统开发中内存安全受限的问题，在众多关键基础设施领域得到了广泛应用。在 Rust 程序运行系统中，与底层资源生命周期关联的清理操作在发生恐慌（Panic）与栈展开（Unwinding）时被强行触发，其中存在显著的内存违规风险。异常控制流（Abnormal Control Flow）能通过打断隐式析构或突破不安全边界，直接破坏程序状态的一致性，对 Rust 系统构成了细粒度的内存安全威胁。本文通过研究上述领域现有静态分析工具的检测边界，总结了当前研究在语义分类和评测框架上的不足，并提出了更有针对性的场景划分与评测策略。旨在量化异常路径下内存破坏的风险范围，为静态漏洞挖掘技术的发展提供方向指引。本文具体研究内容如下：

（1）由于现有异常控制流安全研究存在语义缺失和场景约束不足的问题，其对漏洞根因的刻画准确性会随着复杂跨界交互的增加而显著下降。针对上述问题，提出了一种基于状态碎化理论（State Fragmentation Theory）的异常控制流多维场景分类体系。该体系均通过引入触发位置边界、资源所处状态与隔离跨越度三个维度来填补现有理论对隐式展开路径的描述空白。在此基础上，将异常问题精准划分为析构异常重入（S1）、局部初始化逃逸（S2）、跨越语言边界盲区（S3）以及并发状态孤儿化（S4）四大典型场景，从而实现对漏洞演化过程的有效约束与映射。分析表明，上述分类体系均显著提升了对目标漏洞触发机理的系统性刻画效果。

（2）现有静态分析工具的评测方法采用单一召回率与无差别基准集的评估策略，导致其出现极端场景被掩盖和统计指标失真的问题。针对上述问题，提出了一种基于场景分类的分层静态分析评测框架。利用混淆矩阵与宏平均（Macro-averaging）的特性保护少数类高危漏洞的权重评估，无需修改现有工具的底层架构，从而避免了样本不平衡对其效能评估的影响。通过在 100 个非正常控制流用例上对 Rudra、MirChecker 和 FFIChecker 开展深度实验，在多维场景条件下实现了对工具处理隐式分支与跨界传递等技术瓶颈的有效剖析。实验结果表明，本框架能够在客观反映工具可用性的情况下，有效指导 Rust 安全分析工具明确能力盲区并免受单一场景的数据干扰。

关键词：Rust，异常控制流，恐慌（Panic），栈展开（Unwinding），状态碎化理论，场景分类，静态分析，混淆矩阵，宏平均，内存安全，漏洞挖掘

---

## English Abstract

As a modern systems programming paradigm, Rust (the Rust language) addresses memory-safety limitations in low-level development through ownership and borrowing checks, and has been widely adopted in critical infrastructure. In the Rust runtime, cleanup tied to the lifetimes of low-level resources is forcibly triggered on panic and during stack unwinding, which entails substantial risks of memory violations. Abnormal control flow can break program-state consistency by interrupting implicit destruction or breaching unsafe boundaries, posing fine-grained memory-safety threats to Rust systems. By examining the detection boundaries of existing static analysis tools in this area, this thesis summarizes gaps in current research on semantic classification and evaluation frameworks, and proposes more targeted scenario partitioning and evaluation strategies, aiming to quantify the scope of memory-corruption risk along exceptional paths and to orient advances in static vulnerability discovery. The specific research contents are as follows:

(1) Because prior work on abnormal-control-flow security lacks sufficient semantics and scenario constraints, root-cause characterization degrades markedly as complex cross-boundary interactions grow. To address this, this thesis proposes a multi-dimensional scenario taxonomy for abnormal control flow grounded in state fragmentation theory. The taxonomy fills descriptive gaps regarding implicit unwinding paths by introducing three dimensions: the boundary of the trigger site, the state of the affected resources, and the degree of isolation crossing. On this basis, abnormal issues are mapped into four archetypal scenarios—S1: abnormal destructor re-entrancy; S2: partial-initialization escape; S3: blind spots across language boundaries; and S4: concurrent state orphaning—thereby constraining and tracing vulnerability evolution. Analysis shows that this taxonomy substantially improves systematic characterization of how target vulnerabilities are triggered.

(2) Evaluations of static analyzers often rely on a single recall metric and undifferentiated benchmarks, which hides extreme scenarios and distorts statistics. This thesis therefore proposes a layered static-analysis evaluation framework driven by scenario classification. By leveraging confusion matrices and macro-averaging, the framework preserves the weight of rare but high-severity defect classes without altering tools’ internals, mitigating the impact of class imbalance on effectiveness assessment. Deep experiments on 100 abnormal-control-flow cases with Rudra, MirChecker, and FFIChecker dissect tool bottlenecks—such as handling implicit branches and cross-boundary propagation—under multi-dimensional scenarios. Results indicate that the framework objectively reflects tool utility, helps Rust security analyzers clarify capability blind spots, and reduces interference from dominance of any single scenario in the metrics.

Keywords: Rust, abnormal control flow, panic, unwinding, state fragmentation theory, scenario classification, static analysis, confusion matrix, macro-averaging, memory safety, vulnerability mining
