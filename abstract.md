# 摘要 (Abstract)

## 中文摘要

Rust 语言通过编译期所有权与借用检查在默认情况下保障内存安全，但在程序发生恐慌（panic）并触发栈展开（unwinding）时，异常控制流与析构（Drop）、不安全代码（unsafe）及外部函数接口（FFI）的交互会引入双重释放、释放后使用与跨边界未定义行为等隐蔽风险。现有研究在 panic/展开语义下仍存在分类标准不统一、评测方法不系统、工具能力边界不清晰等问题。本文围绕上述问题，提出面向 Rust 非正常控制流内存安全问题的场景化分析与评测方法，旨在刻画漏洞触发机理与工具适用边界，为 Rust 安全分析工具的选型与改进提供依据。本文具体研究内容如下：
（1）针对现有研究对 panic 相关内存安全问题描述分散、机制解释不足的问题，提出了基于触发点、资源状态与边界位置三维度的场景化分类体系。该体系将典型问题归纳为四类场景：Drop 执行中途发生 panic（S1）、未初始化或部分初始化状态下 panic 中断（S2）、panic 跨 FFI 边界传播（S3）、自定义资源清理逻辑中发生 panic（S4），并系统分析各场景的触发机制、状态演化与典型后果。
（2）针对现有工具评测缺乏场景语义支撑、结果可比性不足的问题，构建了基于场景分类的静态分析评测框架。该框架设计了包含检出率、精确率、漏报率、可运行率及场景感知指标的评测体系，并在 100 个非正常控制流相关用例上对 Rudra、MirChecker、FFIChecker 进行系统评测。实验结果表明，三者总体 Recall 分别为 47.00%、14.00%、11.00%；在跨 FFI 场景（S3）中，FFIChecker 的 Recall 达到 68.75%，而通用工具在该场景存在明显盲区。上述结果揭示了现有工具在异常路径建模、Drop 链处理与跨语言边界语义上的互补优势与结构性不足。

关键词：Rust，恐慌（panic），非正常控制流，Drop，unsafe，FFI，静态分析，能力边界，漏洞挖掘

---

## English Abstract

Rust provides memory safety by default through compile-time ownership and borrowing checks. However, when a program panics and triggers stack unwinding, the interaction among abnormal control flow, destructors (Drop), unsafe code, and the Foreign Function Interface (FFI) can still introduce hidden risks such as double free, use-after-free, and cross-boundary undefined behavior. Existing studies still suffer from non-unified classification criteria, non-systematic evaluation methods, and unclear capability boundaries of analysis tools under panic/unwinding semantics. To address these issues, this thesis proposes a scenario-oriented analysis and evaluation approach for memory safety under abnormal control flow in Rust, aiming to characterize vulnerability triggering mechanisms and tool applicability boundaries, and to provide guidance for tool selection and improvement. The specific research contents are as follows:
(1) To address the fragmented descriptions and insufficient mechanism explanations in existing studies, this thesis proposes a scenario-based classification framework along three dimensions: trigger point, resource state, and boundary location. Typical issues are categorized into four scenarios: panic during Drop execution (S1), panic interruption in uninitialized or partially initialized states (S2), panic propagation across FFI boundaries (S3), and panic in custom resource-cleanup logic (S4). For each scenario, triggering mechanisms, state evolution, and typical consequences are systematically analyzed.
(2) To address the lack of scenario-semantic support and limited comparability in existing tool evaluations, this thesis constructs a static-analysis evaluation framework based on the above classification. The framework defines metrics including detection rate, precision, false negative rate, executability, and scenario-awareness indicators, and conducts a systematic evaluation of Rudra, MirChecker, and FFIChecker on 100 abnormal-control-flow-related test cases. Results show that the overall recall values are 47.00%, 14.00%, and 11.00%, respectively. In the cross-FFI scenario (S3), FFIChecker achieves a recall of 68.75%, while general-purpose tools show clear blind spots. These findings reveal both complementary strengths and structural limitations of existing tools in exception-path modeling, Drop-chain handling, and cross-language boundary semantics.

Keywords: Rust, panic, abnormal control flow, Drop, unsafe, FFI, static analysis, capability boundary, vulnerability mining
