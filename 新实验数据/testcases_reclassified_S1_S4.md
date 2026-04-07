# testcases_core.md 重新分类结果

## 统计概览
- 总样例数：100
- S1：44
- S2：27
- S3：20
- S4：9
- 漏洞/风险样例：60
- 边界/非漏洞样例：31
- 工具/语法校验样例：9

## 说明
- 本表按论文第3章的“最大机理覆盖”原则归类。
- 对明显安全样例、误报样例和工具内部 utility 样例，仍给出“最接近的主导风险场景”，但建议不要直接并入论文中的 100 个正样本统计。

## 明细表

| 序号 | 样例名 | 重新分类 | 样例属性 | 归类说明 |
|---:|---|:---:|---|---|
| 1 | examples__c-in-rust-doublefree | S2 | 漏洞/风险样例 | FFI 释放 Rust 管理对象后继续在 Rust 侧使用，主导机理是跨语言生命周期断裂。 |
| 2 | examples__c-in-rust-memleak | S3 | 漏洞/风险样例 | Box::into_raw 交给 C 后未对称释放，主导后果是资源泄漏/枯竭。 |
| 3 | examples__c-in-rust-uaf | S2 | 漏洞/风险样例 | C 侧提前 free，Rust 侧后续写入形成跨界 UAF。 |
| 4 | examples__cstring-test | S2 | 漏洞/风险样例 | CString 所有权跨 FFI 后由 C 直接 free，属于跨界分配/释放契约错位。 |
| 5 | examples__ffi-simplest | S2 | 边界/非漏洞样例 | 仅有 FFI 边界而无真实漏洞；若强制归类，最接近 S2。 |
| 6 | examples__function-pointer-test | S2 | 漏洞/风险样例 | 经函数指针回调跨界释放，再回到 Rust 侧使用，跨越度高于局部块。 |
| 7 | examples__mix-box-free | S4 | 漏洞/风险样例 | 将 malloc 得到的未初始化区域直接视作 Rust 对象，属于构造期状态违例。 |
| 8 | examples__mix-mem-allocator | S3 | 漏洞/风险样例 | 绕过 Rust 析构直接 free 导致内部资源未释放，主导后果是资源泄漏。 |
| 9 | examples__rc-test | S2 | 漏洞/风险样例 | Rc/Box 资源经 FFI 释放后仍受 Rust 引用管理，属于生命周期错乱。 |
| 10 | examples__return-value-test | S2 | 漏洞/风险样例 | 返回值跨函数后再经 FFI 释放，最终表现为跨边界 UAF。 |
| 11 | examples__rust-in-c-uaf | S2 | 漏洞/风险样例 | Rust 端以 Box 接管 C 指针后自动释放，C 端再次 free 属于跨语言所有权冲突。 |
| 12 | examples__rust-uaf-df | S2 | 漏洞/风险样例 | from_raw_parts 与原 Vec 共享底层缓冲区，返回后形成 UAF/Double Free。 |
| 13 | examples__side-effects-test | S2 | 漏洞/风险样例 | 指针经副作用函数逃逸后再由 C 释放并继续使用，主导机理是跨函数生命周期断裂。 |
| 14 | examples__string-test | S2 | 漏洞/风险样例 | String 缓冲区被 C 侧 free 后仍在 Rust 中 clear。 |
| 15 | examples__vec-test | S2 | 漏洞/风险样例 | Vec 缓冲区被 C 侧 free 后仍在 Rust 中 clear。 |
| 16 | tests__safe-bugs__division-by-zero | S1 | 漏洞/风险样例 | 论文第3章已将该例作为 S1 典型，属于局部算术异常。 |
| 17 | tests__safe-bugs__incorrect-boundary-check | S1 | 漏洞/风险样例 | 越界索引在单一函数内直接触发，属局部内存破坏。 |
| 18 | tests__safe-bugs__incorrect-cast | S1 | 漏洞/风险样例 | 错误数值转换/溢出停留在局部算术路径内。 |
| 19 | tests__safe-bugs__integer-overflow | S1 | 漏洞/风险样例 | 整数下溢/上溢在局部基本块中触发。 |
| 20 | tests__safe-bugs__out-of-bound-index | S1 | 漏洞/风险样例 | 局部数组访问越界。 |
| 21 | tests__safe-bugs__unreachable | S1 | 漏洞/风险样例 | unreachable! 触发点位于局部匹配分支。 |
| 22 | tests__unit-tests__alloc-test | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 23 | tests__unit-tests__annotation | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 24 | tests__unit-tests__arith | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 25 | tests__unit-tests__array | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 26 | tests__unit-tests__assignment | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 27 | tests__unit-tests__big-loop | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 28 | tests__unit-tests__cast | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 29 | tests__unit-tests__crate-bin-test | S1 | 工具/语法校验样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 30 | tests__unit-tests__crate-lib-test | S1 | 工具/语法校验样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 31 | tests__unit-tests__empty | S1 | 工具/语法校验样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 32 | tests__unit-tests__enum-test | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 33 | tests__unit-tests__function-call | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 34 | tests__unit-tests__index | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 35 | tests__unit-tests__input-type | S1 | 工具/语法校验样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 36 | tests__unit-tests__iterator | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 37 | tests__unit-tests__loop-test | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 38 | tests__unit-tests__method-test | S1 | 工具/语法校验样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 39 | tests__unit-tests__negation | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 40 | tests__unit-tests__recursion | S3 | 边界/非漏洞样例 | 样例主题是递归分析与潜在栈耗尽，更接近 S3。 |
| 41 | tests__unit-tests__size-of | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 42 | tests__unit-tests__struct-test | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 43 | tests__unit-tests__vector | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 44 | tests__unit-tests__widen-narrow | S1 | 边界/非漏洞样例 | 单函数/单模块内的局部算术、索引或控制流校验，按 S1 处理。 |
| 45 | tests__unsafe-bugs__double-free | S2 | 漏洞/风险样例 | from_raw_parts 复用外部缓冲区，跨函数返回后双重释放。 |
| 46 | tests__unsafe-bugs__gmath | S2 | 漏洞/风险样例 | 函数返回已在局部 Vec drop 时释放的裸指针，属于跨函数 UAF。 |
| 47 | tests__unsafe-bugs__offset | S1 | 漏洞/风险样例 | 裸指针 offset(5) 直接越界，属 S1。 |
| 48 | tests__unsafe-bugs__spglib-rs | S2 | 漏洞/风险样例 | 对外部指针重复取得所有权，属于跨边界生命周期错位。 |
| 49 | tests__unsafe-bugs__use-after-free(CVE-2019-15551) | S2 | 漏洞/风险样例 | 被调函数内部提前释放调用者持有的 Vec 缓冲区，属 S2。 |
| 50 | tests__unsafe-bugs__use-after-free(CVE-2019-16140) | S2 | 漏洞/风险样例 | 返回值与局部 Vec 共享底层内存，函数返回即产生 UAF。 |
| 51 | trophy-case__bitvec-test | S1 | 漏洞/风险样例 | 主导问题停留在局部算术、边界检查或单点 panic，按 S1 处理。 |
| 52 | trophy-case__brotli-test | S1 | 漏洞/风险样例 | 主导问题停留在局部算术、边界检查或单点 panic，按 S1 处理。 |
| 53 | trophy-case__brotli-test2 | S1 | 漏洞/风险样例 | 主导问题停留在局部算术、边界检查或单点 panic，按 S1 处理。 |
| 54 | trophy-case__brotli-test3 | S1 | 漏洞/风险样例 | 主导问题停留在局部算术、边界检查或单点 panic，按 S1 处理。 |
| 55 | trophy-case__bytemuck-test | S1 | 漏洞/风险样例 | 主导问题停留在局部算术、边界检查或单点 panic，按 S1 处理。 |
| 56 | trophy-case__byte-unit-test | S1 | 漏洞/风险样例 | 主导问题停留在局部算术、边界检查或单点 panic，按 S1 处理。 |
| 57 | trophy-case__executable-memory-test | S4 | 漏洞/风险样例 | 超大尺寸在对象创建阶段就破坏初始化前提，更接近 S4。 |
| 58 | trophy-case__executable-memory-test2 | S4 | 漏洞/风险样例 | 可执行内存对象构造与访问前提失配，属于初始化/环境违例。 |
| 59 | trophy-case__gmath-test | S2 | 漏洞/风险样例 | 调用返回悬空裸指针后继续写入，属于跨函数生命周期逃逸。 |
| 60 | trophy-case__qrcode-generator-test | S4 | 漏洞/风险样例 | 极端尺寸参数在构造/分配前提层面失配，更接近 S4。 |
| 61 | trophy-case__r1cs-test | S4 | 漏洞/风险样例 | 矩阵/构建器初始化前提不满足，主导机理是 S4。 |
| 62 | trophy-case__r1cs-test2 | S4 | 漏洞/风险样例 | 空矩阵直接触发初始化契约违例。 |
| 63 | trophy-case__runes-test | S1 | 漏洞/风险样例 | 主导问题停留在局部算术、边界检查或单点 panic，按 S1 处理。 |
| 64 | trophy-case__runes-test2 | S4 | 漏洞/风险样例 | Sampler::new(0,0) 属于构造期前置条件违例。 |
| 65 | trophy-case__safe-transmute-test | S4 | 漏洞/风险样例 | 零大小类型触发 API 前置条件/构造契约问题。 |
| 66 | trophy-case__scriptful-test | S4 | 漏洞/风险样例 | 状态机在初始/前置状态不满足时 unwrap(None)，更接近 S4。 |
| 67 | trophy-case__spglib-test | S2 | 漏洞/风险样例 | 同一 FFI 返回指针被两次接管所有权，主导机理为 S2。 |
| 68 | cases__panic_double_free | S2 | 漏洞/风险样例 | 论文第3章已将该例作为 S2 典型，异常展开打断 forget 导致双重释放。 |
| 69 | cases__panic_safe_guard | S2 | 边界/非漏洞样例 | 是 panic-safe 对照样例；若强制归类，其风险主题最接近 S2。 |
| 70 | tests__panic_safety__insertion_sort.rs | S2 | 漏洞/风险样例 | 排序过程中复制/移动元素，比较或写入一旦 panic 会破坏对象生命周期。 |
| 71 | tests__panic_safety__order_safe.rs | S1 | 漏洞/风险样例 | 仅对 Copy 值做局部 read，不形成跨边界所有权错乱。 |
| 72 | tests__panic_safety__order_safe_if.rs | S1 | 漏洞/风险样例 | 局部 Copy read，风险未越过生命周期边界。 |
| 73 | tests__panic_safety__order_safe_loop.rs | S1 | 漏洞/风险样例 | 循环中的局部 Copy read 更接近 S1。 |
| 74 | tests__panic_safety__order_unsafe.rs | S2 | 漏洞/风险样例 | 对 Box 做 ptr::read 后再调用可能 panic 的逻辑，属于典型 S2。 |
| 75 | tests__panic_safety__order_unsafe_loop.rs | S2 | 漏洞/风险样例 | 非 Copy 对象在循环内被 read，panic 时会暴露跨边界生命周期错乱。 |
| 76 | tests__panic_safety__order_unsafe_transmute.rs | S1 | 漏洞/风险样例 | 主导问题是局部 unsafe cast，本身不形成所有权跨界逃逸。 |
| 77 | tests__panic_safety__pointer_to_ref.rs | S1 | 漏洞/风险样例 | 从裸指针直接构造引用，属局部非法访问。 |
| 78 | tests__panic_safety__vec_push_all.rs | S2 | 漏洞/风险样例 | set_len 后 clone 可能 panic，展开路径会让部分初始化状态跨出局部块。 |
| 79 | tests__send_sync__no_generic.rs | S3 | 边界/非漏洞样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 80 | tests__send_sync__okay_channel.rs | S3 | 边界/非漏洞样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 81 | tests__send_sync__okay_imm.rs | S3 | 边界/非漏洞样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 82 | tests__send_sync__okay_negative.rs | S3 | 边界/非漏洞样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 83 | tests__send_sync__okay_phantom.rs | S3 | 边界/非漏洞样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 84 | tests__send_sync__okay_ptr_like.rs | S3 | 边界/非漏洞样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 85 | tests__send_sync__okay_transitive.rs | S3 | 边界/非漏洞样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 86 | tests__send_sync__okay_where.rs | S3 | 边界/非漏洞样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 87 | tests__send_sync__sync_over_send_fp.rs | S3 | 漏洞/风险样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 88 | tests__send_sync__wild_channel.rs | S3 | 漏洞/风险样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 89 | tests__send_sync__wild_phantom.rs | S3 | 漏洞/风险样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 90 | tests__send_sync__wild_send.rs | S3 | 漏洞/风险样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 91 | tests__send_sync__wild_sync.rs | S3 | 漏洞/风险样例 | 主题是 Send/Sync 及跨线程共享状态，按并发/资源状态域归入 S3。 |
| 92 | tests__unsafe_destructor__copy_filter.rs | S1 | 边界/非漏洞样例 | Copy 类型 read 不引入所有权断裂，按局部样例处理。 |
| 93 | tests__unsafe_destructor__ffi.rs | S2 | 边界/非漏洞样例 | 析构中发生 FFI 调用；代码本身安全，但主题最接近跨界析构路径。 |
| 94 | tests__unsafe_destructor__fp1.rs | S3 | 漏洞/风险样例 | Drop 中 set_len(0) 的主导后果是资源泄漏，不是直接越界。 |
| 95 | tests__unsafe_destructor__normal1.rs | S1 | 边界/非漏洞样例 | 纯安全 Drop，对应边界/非漏洞样例，最近似 S1。 |
| 96 | tests__unsafe_destructor__normal2.rs | S2 | 漏洞/风险样例 | Drop 中 from_raw 重新接管裸指针所有权，属于生命周期错乱。 |
| 97 | tests__utility__generic_param_ctxts.rs | S3 | 工具/语法校验样例 | 工具内部用于 Send/Sync 泛型索引验证，若强制归类更接近并发状态域 S3。 |
| 98 | tests__utility__identify_generic_params.rs | S3 | 工具/语法校验样例 | 工具内部用于 Send/Sync 参数识别，强制归类为 S3。 |
| 99 | tests__utility__report_handle_macro.rs | S3 | 工具/语法校验样例 | 宏展开后生成 Send/Sync 与 FFI 包装类型，最近似并发/资源域 S3。 |
| 100 | tests__utility__rudra_paths_discovery.rs | S1 | 工具/语法校验样例 | 集中覆盖裸指针/from_raw_parts/set_len 等局部 unsafe 原语，最近似 S1。 |