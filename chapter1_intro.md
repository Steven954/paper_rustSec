# 1 绪论

## 1.1 研究背景及意义

近年来，信息技术的快速发展推动了底层操作系统、数据库以及各类关键基础设施的广泛部署与应用。过去数十年间，C与C++作为现代软件工程的基石，主导了这些底层系统的开发。然而，这些语言依赖开发者手动管理内存的编程范式，直接导致了诸如缓冲区溢出、释放后使用等严重的内存安全漏洞。伴随着网络攻击手段的日益复杂，这些内存漏洞常引发未定义行为，为针对关键基础设施的攻击提供了可乘之机。考虑到全球已披露的软件漏洞中内存安全问题占据主导地位，单纯依赖传统的漏洞扫描与打补丁方式成本过高且已不再现实。因此，美国国家网络总监办公室（ONCD）与国防高级研究计划局（DARPA）等权威机构强调，软件工程界必须从根本上向“内存安全语言”（Memory Safe Languages）进行范式转型 。

为了解决上述底层系统的安全隐患，研究者与工业界提出并广泛采纳了一种新的系统级编程语言：Rust。Rust语言的核心思路是在不引入垃圾回收机制且不牺牲运行时性能的前提下，通过编译期的严格检查来提供保障。其独创的所有权模型、借用检查器与生命周期语义，有效减少了内存与数据竞争类错误。在这一机制下，代码在编译阶段经过初步的静态分析与处理，生成具备强类型与生命周期约束的中间表示，进而转化为安全的底层机器码。这种将严格内存安全检查与极致性能融合的模式，已经在操作系统内核、浏览器引擎等领域取得了广泛应用，有效降低了底层系统开发的漏洞产出率，提高了软件的整体可靠性。

在Rust安全体系中，由于编译器能够有效拦截大多数常规错误，人们往往容易对其安全性产生过度依赖，从而忽视了其潜在的安全与可靠性风险。为了满足底层系统对硬件控制、性能极致优化以及与外部C代码库交互的需求，Rust妥协性地提供了非安全（unsafe）代码块，允许开发者绕过编译器的安全检查。同时，在安全代码领域，Rust奉行“快速失败”的异常处理理念，在遇到诸如数组越界或算术溢出等不可恢复错误时会触发Panic异常控制流。深度实证研究表明，unsafe块中微小的语义违规会将隐蔽的内存漏洞隐式地编码进系统中，而Panic机制则在阻断潜在内存破坏的同时，在大型分布式系统中引入了严重的拒绝服务（DoS）和运行时可靠性问题 。不幸的是，这一特性同样存在于基于Rust重构的关键基础系统中，为现代底层软件的安全性和稳定性带来了全新的挑战。因此，针对Rust内存安全边界与Panic异常控制流的漏洞挖掘与分析成为了一个迫切需要研究的课题。

目前，针对Rust语言的安全研究主要可分为内存安全边界分析与Panic异常控制流分析两大类。其中，内存安全分析重点关注unsafe代码与安全代码交互边界的漏洞挖掘，而异常控制流分析则主要针对由错误处理滥用引发的意外崩溃。在传统的C/C++场景中，漏洞挖掘往往旨在发现典型的内存破坏漏洞；而在Rust场景下，研究者的目标往往是穿透编译器插入的密集安全检查屏障，定位深层的逻辑缺陷或由于未处理异常导致的拒绝服务节点。与其他安全问题相比，Panic触发的异常控制流和复杂的中间表示（MIR）使得程序执行路径难以静态预测，因而可能造成较隐蔽的系统级失效，对软件生态构成重要威胁。同时，目前针对Rust的模糊测试等动态分析手段大多沿用了传统方法，缺乏针对其密集运行时安全检查的改进，导致在实际执行中遭遇严重的“状态空间墙”，暴露出覆盖率低下和假阳性过高等问题 。因此，针对Rust特殊内存模型和异常控制流的安全问题展开深入研究，不仅具有重要的理论意义，同时也对提升关键系统底座的安全性具有较高的应用价值。

另一方面，为了应对Rust生态中的安全挑战，多种防御与验证策略被相继提出，并在底层内核、分布式框架等领域均有落地应用的探索。这些策略根据技术类型可分为基于静态数据流分析的启发式扫描（如Rudra、Yuga）、基于动态测试的跨层漏洞挖掘（如PanicKiller），以及基于分离逻辑和有界模型检查的形式化验证技术（如RustBelt、Prusti、Verus、Kani）。但上述策略也有相应的局限性和挑战，在复杂的现实系统中仍面临落地挑战。例如，完备的形式化验证会给开发者带来巨大的标注成本和人工推导开销，使得其在大规模设备的驱动层或庞大操作系统内核上的部署难以接受；而传统的静态启发式扫描工具虽然对计算开销要求较小，但面对复杂生命周期和高级并发原语时无法有效解决漏报与误报的问题。因此，基于大语言模型（LLM）的代码自动转译方案（如TRACTOR计划）以及基于资源隔离视角的操作系统架构级防御（如Framekernel）相继被提出，旨在保证底层代码极致性能的同时，提高系统的整体防御能力。但上述方法同样面临语言语义鸿沟、可用性与安全性权衡的难题，因此针对Rust复杂生态场景设计更可靠、高效的安全验证与防御策略，仍然是需要解决的重要问题。

综上所述，作为新兴的安全系统编程范式和未来基础设施的重要发展方向，Rust在应用过程中仍面临严峻的安全边界与异常控制流挑战，尤其是unsafe漏洞与Panic引发的拒绝服务风险。因此，深入研究该语言特性下漏洞触发的边界，开发更具针对性和高效性的跨中间表示分析与自动化验证手段，以及探索对系统可用性影响较小且更可靠的架构级防御策略，均具有重要的理论与实践意义。

## 1.2 国内外研究现状

### 1.2.1 宏观安全背景

在过去的数十年中，软件系统的复杂性呈指数级增长，而内存安全漏洞始终是系统安全领域面临的最核心威胁。根据美国国家安全局（NSA）、网络安全和基础设施安全局（CISA）以及 Google、Microsoft 等行业巨头的持续追踪与统计，在基于 C/C++ 等非内存安全语言（Memory-Unsafe Languages）编写的底层系统软件中，约 70% 的严重高危漏洞（CVE）均直接根源于内存安全问题[2][7][8]。2024 年初，美国白宫国家网络总监办公室（ONCD）发布报告，正式呼吁全球软件供应商向内存安全语言（Memory-Safe Languages, MSL）迁移，这标志着内存安全已从单纯的工程技术问题上升为国家级的网络安全战略[1]。学术界与工业界通常将内存安全违规划分为两大核心类别：空间内存安全（Spatial Memory Safety）与时间内存安全（Temporal Memory Safety）[4][10]。空间内存安全漏洞主要发生于程序在访问内存对象时，突破了合法的物理或逻辑边界（如经典的缓冲区溢出、越界读写）；时间内存安全漏洞则涉及对内存对象生命周期的非法访问（如释放后使用 UAF、二次释放、悬挂指针）。传统防御机制（如 ASLR、DEP、Stack Canary）主要依赖于概率性或运行时的缓解，无法从根源上消除漏洞[4]。在这一背景下，Rust 语言作为一门注重安全性、并发性和高性能的系统级编程语言应运而生[3][6]。Rust 通过其独创的“所有权（Ownership）”模型、严格的“借用检查器（Borrow Checker）”以及生命周期（Lifetime）推导机制，在编译期强制实现了别名与可变性的互斥（Aliasing XOR Mutability, AXM），从而在零运行时开销（Zero-cost Abstraction）的前提下，从数学和语义层面根除了安全 Rust（Safe Rust）代码中的空间与时间内存漏洞以及数据竞争。然而，为了满足底层系统编程对硬件操控、性能优化以及与 C/C++ 遗留生态互操作的需求，Rust 引入了“不安全（unsafe）”关键字。unsafe 块允许开发者绕过编译器的借用检查，执行解引用裸指针、调用外部函数接口（FFI）等高危操作。大量实证研究表明，Rust 项目中绝大多数的内存安全漏洞和系统崩溃，均直接或间接源于对 unsafe 机制的滥用或封装不当[5][9]。因此，针对 Rust（尤其是 unsafe 边界与 FFI）的自动化程序分析与漏洞检测，已成为当前国内外系统安全领域最前沿的研究热点。

### 1.2.2 静态分析技术

静态应用程序安全测试（SAST）是在不执行目标代码的情况下，通过分析源代码或中间表示（IR）来发现潜在缺陷的技术。静态分析的根本优势在于其能够实现安全左移，但其不可避免地受到经典停机问题的限制，难以在声音性（不漏报）与完备性（不误报）之间取得完美平衡。静态分析的核心算法瓶颈在于指针分析（Pointer Analysis）与别名分析的精度。在 C/C++ 时代，指针分析的理论基石主要由 Andersen 算法与 Steensgaard 算法奠定。1994 年提出的 Andersen 算法采用基于子集包含的约束模型，保留了数据流的单向性，精度较高，但其最坏时间复杂度高达 $O(n^3)$，难以扩展至超大型代码库[11]。为了解决性能瓶颈，Steensgaard 在 1996 年提出基于等价类统一的算法，利用并查集将复杂度降至接近线性时间 $O(n\alpha(n))$，但双向合并导致大量虚假别名，误报率极高[12]。在此基础上，现代静态分析框架不断演进，如基于分离逻辑的 Facebook Infer[14][15]、基于 Datalog 查询图的 CodeQL，以及澳大利亚新南威尔士大学提出的 SVF（Static Value-Flow）框架[13]，后者通过构建稀疏值流图（Sparse Value-Flow Graph）实现了高精度、按需的跨过程指针分析。此外，结合归纳综合消除中间数据结构[23]以及嵌套属性图的自动化检测[22]也在不断发展。

随着 Rust 的普及，传统的 C/C++ 静态分析工具无法直接理解 Rust 的所有权和生命周期语义。Rust 编译器前端将源代码先后降级为高级中间表示（HIR）、类型化高级中间表示（THIR）以及中级中间表示（MIR）。其中，MIR 去除了语法糖，显式化了控制流和借用检查生命周期，成为 Rust 静态漏洞挖掘的最佳介入层。针对 Rust 的静态分析研究在近几年取得了突破性进展：Rudra（SOSP 2021）：这是韩国科研团队提出的一款面向 Rust 生态系统级别的静态分析器。Rudra 工作在 HIR 和 MIR 层，创新性地定义了三种 Rust 特有的 unsafe 漏洞模式：Panic 安全漏洞、高阶不变量漏洞以及 Send/Sync 型变漏洞。Rudra 扫描了全网数万个 Crate，发现了上百个 CVE 和 RustSec 漏洞[16]。MirChecker（CCS 2021）：香港中文大学团队开发的 MirChecker 是基于抽象解释（Abstract Interpretation）理论的 Rust 静态检测工具。它在 MIR 层构建了数值与符号的约束求解模型，专门用于追踪数值溢出、越界访问以及部分生命周期破坏问题[17]。SafeDrop（TOSEM 2023）：针对 Rust 特有的基于所有权的资源管理（OBRM）机制带来的提前释放（UAF）和二次释放隐患，复旦大学和南方科技大学研究团队提出了 SafeDrop。该工具基于路径敏感的数据流分析，利用优化的 Tarjan 算法提取控制流图中的数据流别名，有效检测了由复杂分支或 Panic 解卷（Unwinding）引发的内存释放错误[18]。TYPEPULSE（USENIX Security 2025）：针对 Rust 中 `as` 和 `transmute` 等类型转换操作被滥用导致的类型混淆漏洞，清华大学与乔治梅森大学联合提出了 TYPEPULSE。该算法通过类型转换分析与指针别名分析构建属性图，能够精准检测内存对齐错误（Misalignment）、布局不一致（Inconsistent Layout）等深层内存破坏[19]。尽管静态分析在 Rust 漏洞挖掘中成果丰硕，但由于 Rust 高度依赖泛型、闭包与宏，且 unsafe 块的上下文高度复杂，辅助符号执行等混合架构以缓解路径爆炸仍是未来的重点方向[20]。

### 1.2.3 动态检测技术

与静态分析基于规则近似推演不同，动态程序分析（Dynamic Analysis）在代码实际执行过程中监控内存与指令流，具有极低的误报率。在内存检测器（Sanitizers）的发展史上，技术架构经历了从重量级二进制翻译到轻量级编译期插桩的深刻演变。1992 年问世的 Purify 开创了直接在目标代码中插入检测指令的先河，用于捕捉未初始化读取与内存泄漏[24]。随后，基于动态二进制插桩（DBI）的 Valgrind（其核心工具 Memcheck）成为业界标准，通过在虚拟机沙箱中维护影子状态实现高度精确的检测，但其粗粒度翻译带来了极高的性能开销，仅限于轻量级测试[25][30]。为了突破性能瓶颈，Google 于 2012 年推出了基于 LLVM 编译器后端的 AddressSanitizer (ASan)。ASan 通过编译期 IR 插桩，结合高效的影子内存（Shadow Memory）映射与红区（Redzone）隔离机制，将性能开销骤降至约 73%，成为现代软件工程持续集成的标配[26]。此后，HWASan（基于硬件指针标签）、MSan（未初始化检测）等相继问世，构成了庞大的 Sanitizer 生态[28][31]。近年来，清华大学张超教授团队在 USENIX Security 2023 上提出了 MTSan，通过渐进式对象恢复与定制化重写，为无源码的二进制模糊测试提供了实用的内存消毒器，弥补了 C/C++ 闭源组件的检测空白[27]；此外，针对 ARM 平台提出的 PACSan 通过硬件指针认证实现了更低开销的运行期防护[29]。在 Rust 语言生态中，由于 Safe Rust 在编译期已经保证了严格的内存安全，传统 ASan 在 Rust 中的应用主要集中于审计 unsafe 代码以及 FFI 链接的 C/C++ 底层库。然而，Rust 社区自身发展出了更符合语言语义的动态解释器——Miri。Miri 不仅是一个工具，更是 Rust 形式化语义演进的核心试验场。它直接工作在 Rust 的 MIR 中间表示层，通过拦截并解释每条 MIR 指令，不仅能够检测传统的越界、UAF 和内存泄漏，更重要的是，Miri 内建了对 Rust 借用规则的动态验证引擎。任何违反 Rust 独占可变性原则的别名操作，都会被 Miri 精确捕捉为“未定义行为（Undefined Behavior, UB）”[32]。然而，Miri 作为解释器的本质决定了其执行速度极慢，未来如何加速此类运行时内存隔离检查机制，仍是当前的重要研究课题。

### 1.2.4 模糊测试技术

模糊测试（Fuzzing）作为一种自动化的软件测试方法，通过高频次向目标程序输入变异或随机数据来诱发崩溃，极大地弥补了代码审计的不足。自 AFL 确立了覆盖率引导的灰盒模糊测试（CGF）范式以来，Fuzzing 技术在过去十年经历了飞速发展[35]。在国内，清华大学张超教授领导的团队在 Fuzzing 理论及工程上做出了世界级贡献：例如针对 AFL 哈希碰撞问题的 CollAFL（IEEE S&P 2018）[36]、解决状态空间盲区的 StateFuzz（USENIX Security 2022）[37]、基于数据流敏感的 GREYONE（USENIX Security 2020）[38]，以及目标驱动的定向模糊测试 SDFUZZ（USENIX Security 2024）[39]等，极大提升了对深层逻辑和状态机的探索能力。此外，以 xFUZZ 和 IDFUZZ 为代表的混合自适应调度框架也在最新的学术界会议（如 USENIX Security 2025, ISSTA 2025）中被广泛提出[40][41]。针对特定场景，Sysyphuzz 与 EAGLEYE 分别攻克了内核深层压力覆盖与物联网设备隐藏路由发现的难题[42][43]。在 Rust 生态中，Fuzzing 技术也得到了迅速普及，以 cargo-fuzz（基于 libFuzzer）和 afl.rs 为代表的工具已成为 Rust 开发者验证库安全性的常用手段。然而，面向 Rust 的模糊测试面临着一个核心的语义悖论：由于 Safe Rust 本身防范了内存崩溃，Fuzzer 在纯安全代码中通常只能触发安全的 Panic 或逻辑死循环，难以轻易获得可利用的段错误（Segfault）。因此，国内外研究人员开始将 Rust 模糊测试的焦点转向“定向挖掘”与大模型（LLM）增强。利用 LLM 理解 Rust 复杂的 Trait 特征与泛型约束，自动生成能够覆盖深层 unsafe API 调用的测试线束，正成为当前提升 Rust 漏洞挖掘覆盖率的有效手段。

### 1.2.5 形式验证技术

当模糊测试遭遇严格的校验和约束时极易陷入探索停滞。此时，符号执行（Symbolic Execution）技术展现出了无可替代的严谨性。符号执行的经典理论可追溯至 King 的开创性工作[45]；以 KLEE（基于 LLVM IR）和 Angr（基于二进制 VEX IR）为代表的现代符号执行引擎，为系统级程序的深层路径探索奠定了基础[46][47]。在 Rust 语言安全领域，单纯的漏洞检测已无法满足高安全核心系统（如航空航天、内核）的要求，学术界正致力于通过形式化验证（Formal Verification）从数学上证明 Rust 代码的绝对正确性。该领域的奠基性工作是发表于 POPL 2018 的 RustBelt 项目。RustBelt 在 Coq 交互式定理证明器中，利用分离逻辑框架，首次从数学上证明了 Rust 的核心类型系统以及关键 unsafe API 封装的声音性[48]。为了准确规范编译器可以对 Rust 代码进行何种优化，研究者提出了 Stacked Borrows（POPL 2020）别名模型，严格规定了借用指针的生命周期与访问权限[49]。然而，Stacked Borrows 过于严格，否定了实际工程中许多合理的指针重排优化。为此，最新的 Tree Borrows（PLDI 2025）模型将栈结构升级为树形拓扑，支持更细粒度的权限演化，成功减少了 54% 的合规代码误报[50]。在工程自动化验证工具方面，发表于 PLDI 2024 的 RefinedRust 系统将精化类型与 RustBelt 分离逻辑相结合，实现了针对安全与不安全混合 Rust 代码的半自动化底层证明生成[51]。而发表于 SOSP 2024 的 Verus 平台，则采用线性幽灵类型与底层 SMT 自动化求解相结合，其验证速度比传统工具快数倍，极大地降低了系统程序员编写形式化证明的门槛[52]。

### 1.2.6 边界防护技术

工业界在短期内无法完全重写庞大的 C/C++ 历史遗产，这导致现代软件系统普遍演变为混合语言架构。在这一架构下，Rust 与 C/C++ 进行通信的唯一桥梁是外部函数接口（FFI）。然而，FFI 成为了整个系统安全链条中最脆弱的环节，通过 FFI 实施的“跨语言攻击”能够轻易击穿系统防御。为应对跨语言边界带来的内存违规，国内外的研究主要集中于以下技术路径：静态 FFI 协议检查：香港中文大学发表的 FFIChecker 工具，通过在 LLVM IR 层执行跨语言的抽象解释，专门追踪从 Rust 传递到 C 侧的指针生命周期，成功发现了包括 FFI 悬挂指针在内的多种内存错误[53]。混合语言动态 Sanitizer 优化：传统 Sanitizer 在插桩混合应用时会引入巨大的性能损耗。发表于 USENIX Security 2025 的 SafeFFI 系统提出了一种轻量级的插桩机制：仅在 Rust 的安全与不安全边界处动态插入断言检查，将编译与运行开销骤降至 2.64 倍[54]。硬件能力（Capability）隔离：新加坡国立大学提出的 CapsLock 机制（CCS 2025），借助基于能力的硬件架构，引入“使用即撤销（Revoke-on-use）”抽象，当不安全的 C/C++ 代码试图非法使用已回收的能力句柄时，硬件层直接触发异常，实现零软件开销的跨语言内存保护[55]。此外，浙江大学团队在 ISSTA 2025 发表的 Safe4U 工具则创造性地结合了静态分析与大语言模型（LLM），用于自动识别 Rust 中对 unsafe FFI 调用的“不健全安全封装”，弥补了语义理解鸿沟[56]。

### 1.2.7 系统重构实践

操作系统内核是计算机科学的皇冠，近年来，伴随 Rust 的成熟，以 Rust 重构底层操作系统的浪潮正在席卷全球。在 Linux 内核的渐进式演进中，Rust-for-Linux (RFL) 项目允许开发者使用 Rust 编写设备驱动。然而，发表在 USENIX ATC 2024 上的实证研究剖析了 RFL 的阵痛：Linux 内核中充斥着 C 风格的侵入式双向链表和复杂的引用计数，这与 Rust 的独占别名规则存在严重的阻抗失配。因此，RFL 不得不在 Rust 和 C 之间构建一层厚重的绑定层，有时甚至需要牺牲开发效率[57]。为了彻底摆脱历史包袱，国内外研究团队开始探索基于 Rust 的全新 OS 架构设计。在顶会前沿，由南方科技大学、北京大学、清华大学及蚂蚁集团联合在 USENIX ATC 2025 发表的 Asterinas 内核架构，提出了革命性的 Framekernel（框架内核） 理念。Asterinas 将传统宏内核拆分为两个层级：底层的特权操作系统框架（OSTD）与上层的非特权操作系统服务。OSTD 承担了与 MMU、中断处理交互的必须使用 unsafe Rust 的核心职责，并封装为高级 API；而上层服务完全采用 Safe Rust 编写。这一设计实现了极小且可证的“可信计算基（TCB）”（TCB 仅占代码量的 14.0%）。目前 Asterinas 不仅完美兼容了 Linux 的 210 多个系统调用，且在吞吐量与性能上媲美原生 Linux C 代码，展示了软硬件隔离与语言级隔离相融合的巨大潜力[58]。

### 1.2.8 未来发展展望

综上所述，当前国内外在系统级内存安全领域的研究正处于技术范式的跨越期。从针对 C/C++ 的传统静态审计、模糊测试与动态检测，全面演变为以 Rust 为核心的新一代形式化语义约束与混合测试融合体系。未来的内存安全技术演进呈现出两大核心趋势：第一，跨语言与边界融合分析。在向全内存安全生态迁移的漫长过渡期内，面向 Rust-C/C++ FFI 边界的静态/动态协同检测技术（如 SafeFFI 与 CapsLock）将成为防御重心[54][55]。第二，软硬件协同防御的常态化。随着硬件架构的创新（如 ARM MTE 内存标签与基于微体系架构的 CHERI 处理器）走向商用，高昂的漏洞检测开销将被下沉至硅片级执行，使得实时、全局的内存安全验证不仅在应用层，更在现代 Rust 重构的操作系统内核中成为现实[59][60]。

本节参考文献

1. ONCD. *Back to the Building Blocks: A Path Toward Secure and Measurable Software.* 2024.
2. CISA, NSA, FBI, et al. *The Case for Memory Safe Roadmaps.* 2023.
3. Watson, R. N. M., et al. "It Is Time to Standardize Principles and Practices for Software Memory Safety." *Communications of the ACM*, 2025.
4. Szekeres, L., et al. "SoK: Eternal war in memory." *IEEE S&P*, 2013.
5. Evans, A. N., et al. "Is Rust used safely by software developers?." *ICSE*, 2020.
6. 胡双, 华保健, 欧阳万容, 樊起亮. "Rust语言安全研究综述." *密码学报*, 2023.
7. Microsoft. "Windows 11: The journey to security by default." *BlueHat IL*, 2023.
8. NSA. "Software Memory Safety." *Cybersecurity Information Sheet*, 2022.
9. Qin, B., et al. "Understanding memory and thread safety practices and issues in real-world rust programs." *PLDI*, 2020.
10. Dietz, W., et al. "The Meaning of Memory Safety." 2018.
11. Andersen, L. O. *Program Analysis and Specialization for the C Programming Language.* 1994.
12. Steensgaard, B. "Points-to analysis in almost linear time." *POPL*, 1996.
13. Sui, Y., et al. "SVF: interprocedural static value-flow analysis in LLVM." *CC*, 2016.
14. Calcagno, C., et al. "Compositional Shape Analysis by means of Bi-Abduction." *J. ACM*, 2011.
15. Distefano, D., et al. "Scaling static analyses at facebook." *CACM*, 2019.
16. Bae, Y., Kim, Y., Askar, A., et al. "Rudra: Finding Memory Safety Bugs in Rust at the Ecosystem Scale." *SOSP*, 2021.
17. Li, Z., Wang, J., Sun, M., et al. "MirChecker: Detecting Bugs in Rust Programs via Static Analysis." *ACM CCS*, 2021.
18. Cui, M., Chen, C., Xu, H., et al. "SafeDrop: Detecting Memory Deallocation Bugs of Rust Programs via Static Data-Flow Analysis." *TOSEM* 32, 4. 2023.
19. Chen, H. M., He, X., Wang, S., et al. "TYPEPULSE: Detecting Type Confusion Bugs in Rust Programs." *USENIX Security Symposium*, 2025.
20. Aslanyan, H., et al. "Combining Static Analysis With Directed Symbolic Execution for Scalable and Accurate Memory Leak Detection." *IEEE*, 2024.
21. Hassler, K., et al. "A Comparative Study of Fuzzers and Static Analysis Tools for Finding Memory Unsafety in C and C++." 2025.
22. Yan, X., et al. "Automated Data Binding Vulnerability Detection for Java Web Frameworks via Nested Property Graph." *ISSTA*, 2024.
23. Xiong, Y., et al. "Superfusion: Eliminating Intermediate Data Structures via Inductive Synthesis." *PLDI*, 2024.
24. Hastings, R., et al. "Purify: Fast detection of memory leaks and access errors." *USENIX Winter*, 1992.
25. Nethercote, N., et al. "Valgrind: A framework for heavyweight dynamic binary instrumentation." *PLDI*, 2007.
26. Serebryany, K., et al. "AddressSanitizer: A Fast Address Sanity Checker." *USENIX ATC*, 2012.
27. Chen, X., Shi, Y., Jiang, Z., et al. "MTSan: A Feasible and Practical Memory Sanitizer for Fuzzing COTS Binaries." *USENIX Security Symposium*, 2023.
28. Vintila, E. Q., et al. "Evaluating the Effectiveness of Memory Safety Sanitizers." *IEEE S&P*, 2025.
29. Li, Y., et al. "PACMem: Enforcing spatial and temporal memory safety via arm pointer authentication." *ACM CCS*, 2022.
30. D'Elia, D. C., et al. "SoK: Using dynamic binary instrumentation for security." *ASIACCS*, 2019.
31. Song, D., et al. "SoK: Sanitizing for Security." *IEEE S&P*, 2019.
32. Jung, R. "Miri: Practical Undefined Behavior Detection for Rust." *ICOOOLPS*, 2024.
33. Lipp, S., et al. "An Empirical Study on the Effectiveness of Static C Code Analyzers for Vulnerability Detection." 2022.
34. Wang, J., et al. "A Comprehensive Memory Safety Analysis of Bootloaders." *NDSS*, 2025.
35. Böhme, M., et al. "Coverage-based Greybox Fuzzing as Markov Chain." *IEEE TSE*, 2019.
36. Gan, S., Zhang, C., et al. "CollAFL: Path Sensitive Fuzzing." *IEEE S&P*, 2018.
37. Zhao, B., Li, Z., Qin, S., et al. "StateFuzz: System Call-Based State-Aware Linux Driver Fuzzing." *USENIX Security Symposium*, 2022.
38. Gan, S., Zhang, C., et al. "GREYONE: Data Flow Sensitive Fuzzing." *USENIX Security Symposium*, 2020.
39. Li, P., Meng, W., Zhang, C. "SDFUZZ: Target States Driven Directed Fuzzing." *USENIX Security Symposium*, 2024.
40. Yu, D., et al. "xFUZZ: A Flexible Framework for Fine-Grained, Runtime-Adaptive Fuzzing Strategy Composition." *ISSTA*, 2025.
41. Chen, Y., et al. "IDFUZZ: Intelligent Directed Grey-box Fuzzing." *USENIX Security Symposium*, 2025.
42. Ren, Z., et al. "Sysyphuzz: the Pressure of More Coverage." *NDSS*, 2026.
43. Liu, H., et al. "EAGLEYE: Exposing Hidden Web Interfaces in IoT Devices via Routing Analysis." *NDSS*, 2025.
44. Chen, H., et al. "Hawkeye: Towards a Desired Directed Grey-Box Fuzzer." *ACM CCS*, 2018.
45. King, J. C. "Symbolic Execution and Program Testing." *Communications of the ACM*, 1976.
46. Cadar, C., et al. "KLEE: Unassisted and automatic generation of high-coverage tests for complex systems programs." *OSDI*, 2008.
47. Baldoni, R., et al. "A Survey of Symbolic Execution Techniques." *ACM Comput. Surv.*, 2018.
48. Jung, R., Jourdan, J. H., Krebbers, R., Dreyer, D. "RustBelt: Securing the Foundations of the Rust Programming Language." *POPL*, 2018.
49. Jung, R., Dang, H. H., Kang, J., Dreyer, D. "Stacked Borrows: An Aliasing Model for Rust." *POPL*, 2020.
50. Villani, N., Hostert, J., Dreyer, D., Jung, R. "Tree Borrows." *PLDI*, 2025.
51. Gäher, L., Sammler, M., Jung, R., et al. "RefinedRust: A Type System for High-Assurance Verification of Rust Programs." *PLDI*, 2024.
52. Lattuada, A., Hance, T., Bosamiya, J., et al. "Verus: A Practical Foundation for Systems Verification." *SOSP*, 2024.
53. Li, Z., Wang, J., Sun, M., et al. "FFIChecker: A Static Analysis Tool For Detecting Memory Management Bugs Between Rust and C/C++." *ESORICS*, 2022.
54. Braunsdorf, O., Lange, T., Hohentanner, K., et al. "SafeFFI: Efficient Sanitization at the Boundary Between Safe and Unsafe Code in Rust and Mixed-Language Applications." *USENIX Security Symposium*, 2025.
55. Yu, J. Z., Han, F., Choudhury, K., et al. "Securing Mixed Rust with Hardware Capabilities (CapsLock)." *ACM CCS*, 2025.
56. Li, H., Wang, B., Hu, X., Xia, X. "Safe4U: Identifying Unsound Safe Encapsulations of Unsafe Calls in Rust using LLMs." *ISSTA*, 2025.
57. Li, H., Guo, L., Yang, Y., et al. "An Empirical Study of Rust-for-Linux: The Success, Dissatisfaction, and Compromise." *USENIX ATC*, 2024.
58. Peng, Y., Tian, H., Zhang, J., et al. "ASTERINAS: A Linux ABI-Compatible, Rust-Based Framekernel OS with a Small and Sound TCB." *USENIX ATC*, 2025.
59. Watson, R. N. M., et al. "CHERI: A Hybrid Capability-System Architecture for Scalable Software Compartmentalization." *IEEE S&P*, 2015.
60. Xia, H., et al. "ARM MTE Performance in Practice." 2026.

## 1.3 本文主要研究内容与创新点

本文研究 Rust 在 panic 与栈展开（unwinding）语义下的内存不安全行为，并关注静态检测工具在该类异常路径上的适用边界。现有工作仍缺少与展开语义对齐的根因级分类与解释，以及可复现、可对比的场景化评测范式，结论易停留在“检出数量”层面的笼统比较。基于此，本文工作分两部分展开：

（1）针对异常控制流相关讨论难以刻画 panic 触发的状态演化、分类表述难与工具评测对齐等局限，本文提出根因驱动的场景分类与解释方法：以状态碎片化理论与三阶段演进模型突出 panic 的关键节点角色，按触发位置、资源状态与隔离边界划分 S1–S4，贯通各场景机理、后果及与传统漏洞标签的映射，为风险分析与后续评测提供统一语义锚点。

（2）针对 panic 命题下基准固化困难、工具输出异构、指标缺乏场景感知、复现成本偏高等评测瓶颈，本文构建基于场景分类的静态分析评测框架：双轨基准构建与构建语义锁定，配合归一化管线与真值判定；在常规度量外引入场景感知指标与多维度能力归因，在场景语境下揭示工具能力分化与结构性短板，并沉淀可复用的评测组织方式，以支撑多工具组合与工程上的可用性—安全性权衡。

## 1.4 章节结构与安排

全文共分五章，章节结构如图 1.1 所示（图待绘制），详细安排如下。

第 1 章 绪论。 首先，介绍 Rust 在 异常控制流下的内存风险，说明围绕该类命题开展机理与风险边界分析、静态工具能力评估及相关安全实践研究的背景与意义。其次，梳理并分析国内外相关研究现状：从静态分析、动态检测与消毒、模糊测试、形式化验证及跨语言边界防护等角度对相关方法进行归类与对照，并特别关注与 MIR/unwind 语义、工具评测及能力边界相关的进展。然后，归纳现有研究在异常控制流场景分类、可复现场景化评测范式、静态工具在隐式清理与跨边界语义上的适用边界等方面仍存在的不足。最后，阐述本文的两项核心研究内容与对应创新点，并给出全书的章节结构安排。

第 2 章 相关概念和技术基础。 阐述 Rust 内存安全模型与资源管理（所有权、借用、生命周期、RAII 与 `Drop`、`unsafe` 与编译器保证边界）；说明 `panic` 的触发来源、unwind 与 abort 策略及其对分析与复现的影响；介绍 panic 安全性（panic safety）相关语义及标准库中的防护性机制（如毒化、`UnwindSafe` 等）；最后从 MIR 与显式清理路径出发简述静态分析评测的常见维度，并界定本文选取 Rudra、MirChecker、FFIChecker 作为评测对象的理由与范围。

第 3 章 基于异常控制流的内存安全场景分类（创新点一）。 在从“症状驱动”到“根因驱动”的问题表述下，给出异常控制流与内存破坏的威胁模型；提出状态碎片化理论与三阶段威胁演进模型；设计由触发位置、资源状态与隔离边界构成的多维分类空间，并定义 S1–S4 场景、分析其机理及与传统漏洞标签的映射关系；基于与第 4 章共享的 100 例数据集给出分类有效性与分工具召回的实证推演，归纳对后续工具设计与评测具有指导意义的三类启发式洞见，并说明与第 4 章的衔接方式。

第 4 章 基于场景分类的静态分析评测框架（创新点二）。 在引言中明确评测目标、研究问题与核心假设；系统阐述基准构建策略、自动化评测管线与结果归一化方法；给出基础指标、场景感知指标与边界归因方法；报告实验环境、100 例数据集中 S1–S4 的分布及三款工具的总体与分场景结果，结合 unwind/Drop 隐式路径、跨语言建模与状态机语义等维度解释方法反差；讨论有效性威胁与缓解措施，并对本章工作进行小结。

第 5 章 总结与展望。 归纳本文在场景分类、评测框架与工具能力边界方面的主要结论；客观分析样例规模与分布、真实漏洞复现难度及静态分析范式等局限；从扩大基准、引入动态/符号方法、增强 unwind 与 FFI 联合建模及工具链集成等方向展望未来工作。
