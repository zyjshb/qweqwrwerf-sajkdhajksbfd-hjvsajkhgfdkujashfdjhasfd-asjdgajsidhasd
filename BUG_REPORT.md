# Saki 病娇模拟器 — 全面 Bug 审计报告

> 审计日期: 2026-05-30
> 审计范围: 全项目所有源码文件 (后端/前端/桌面端/资源/Agent)
> 审计标准: 大厂级全球发布品质

---

## 目录

1. [第一轮: 代码逻辑 Bug (91个)](#第一轮-代码逻辑-bug)
2. [第二轮: 翻译系统深度审计 (16个)](#第二轮-翻译系统深度审计)
3. [第二轮: 聊天界面 UI/UX 审计 (59个)](#第二轮-聊天界面-uiux-审计)
4. [第二轮: 遗漏代码 Bug (23个)](#第二轮-遗漏代码-bug)
5. [合并去重汇总](#合并去重汇总)
6. [修复优先级路线图](#修复优先级路线图)

---

# 第一轮: 代码逻辑 Bug

## CRITICAL (致命) — 9个

| # | 模块 | 文件 | 行号 | Bug 描述 |
|---|------|------|------|----------|
| 1 | 后端 | `backend/websocket/game_ws.py` | 303 | **`spoken_for_history` 未定义** — 每次对话回复触发 `NameError`，CHAT_APPEND 永远无法发送，游戏不可玩 |
| 2 | 后端 | `backend/websocket/protocol.py` | 27-45 | **`REQUEST_FILE_PICKER` 未注册** — 文件选择器请求被 ValueError 拒绝 |
| 3 | 后端 | `backend/websocket/protocol.py` | 64-105 | **`FILE_PICKER_RESULT` 未注册** — 文件选择结果无法发送回前端 |
| 4 | 安全 | `yandere_config.json` | 2 | **API Key 明文提交** — `sk-d2bcaec50a704001a8b64d037ecbfdff` 泄露到仓库 |
| 5 | 安全 | `backend/websocket/game_ws.py` | 492-521 | **Agent 接管无认证** — 任何 WebSocket 客户端可触发屏幕截图+鼠标键盘接管 |
| 6 | 后端 | `backend/core/game_state.py` | 403 | **好感度坏结局不可达** — `favorability` clamp 到 `[0,100]`，条件 `<= -25` 永假 |
| 7 | 后端 | `backend/audio/tts_client.py` | 142-145 | **TTS 路径解析空操作** — 循环 `p = os.path.abspath(p)` 只重绑局部变量 |
| 8 | 桌面端 | `ui/ecg_canvas.py` | 54 | **ECG 每帧清除粒子引擎** — `delete("all")` 每30ms销毁所有画布元素 |
| 9 | 前端 | `frontend/src/composables/useWebSocket.js` | 7 | **硬编码 `ws://`** — HTTPS 部署时浏览器拒绝连接 |

## HIGH (高危) — 22个

| # | 模块 | 文件 | 行号 | Bug 描述 |
|---|------|------|------|----------|
| 10 | 后端 | `backend/core/game_state.py` | 427-443 | 日期推进关键词子串匹配误触发 ("morning"/"awake") |
| 11 | 后端 | `backend/ai/api_client.py` | 117-119 | 后台线程竞态: `game_state.last_user_input` 无同步读写 |
| 12 | 后端 | `backend/ai/translator.py` | 52-58 | `||` 分隔符解析: 多个 `||` 时 `parts[1]` 不是 JSON |
| 13 | 后端 | `backend/ai/prompt_builder.py` | 59-70 | 自定义角色名替换顺序错误，双重替换损坏文本 |
| 14 | 后端 | `backend/audio/tts_client.py` | 80-85 | 临时 WAV 文件永不删除，长期累积数百MB |
| 15 | 后端 | `backend/websocket/game_ws.py` | 616-617 | 阻塞式 `requests.post()` 冻结 async 事件循环15秒 |
| 16 | 后端 | `backend/resources/game_constants.py` | 1516 | 日文翻译 key 混入中文字符 `的` (应为 `の`) |
| 17 | 后端 | `backend/resources/game_constants.py` | 1534 | 日文文本错放在 English 翻译字典中 |
| 18 | 后端 | `backend/websocket/game_ws.py` | 161,314,504,764 | 使用废弃 `asyncio.get_event_loop()` (Python 3.12+ 异常) |
| 19 | 桌面端 | `visual_fx/procedural_pillow.py` | 58,85,115,284 | Pillow 10+ 不兼容: `Image.BILINEAR`/`Image.NEAREST` 已移除 |
| 20 | 桌面端 | `audio/sound_manager.py` | 108-113 | `play_beep` Sound 对象被 GC 回收，哔声中断 |
| 21 | 桌面端 | `audio/sound_manager.py` | 29-50 | 心跳音频叠加: 多次调用导致多层循环同时播放 |
| 22 | 桌面端 | `ui/main_window.py` | 1436 | 后台线程访问 Tkinter 控件，可能 segfault |
| 23 | 后端 | `backend/agent/action_executor.py` | 47 | `pyautogui.typewrite()` 不支持中日文输入 |
| 24 | 后端 | `backend/agent/action_executor.py` | 40-41 | 无坐标边界检查，可能点击系统 UI |
| 25 | 前端 | `frontend/src/composables/useGameState.js` | 92-95 | `applyDelta` 完全忽略 payload，属性变动丢弃 |
| 26 | 前端 | `frontend/src/App.vue` | 709 | `request-file-picker` 事件监听器永不清理 |
| 27 | 前端 | `frontend/src/App.vue` | 886-901 | `title_corruption` setInterval 泄漏 |
| 28 | 前端 | `frontend/src/App.vue` | 904-919 | `day_loop` setInterval 泄漏 |
| 29 | 前端 | `frontend/src/App.vue` | 872-883 | `mouse_attract` 事件监听器未清理 |
| 30 | 前端 | `frontend/src/components/Terminal.vue` | 134,148-163 | 打字机定时器未清理 |
| 31 | 前端 | `frontend/src/components/GlitchTextOverlay.vue` | 324-336 | AudioContext 爆炸: 每45ms创建新实例，约47个 |

## MEDIUM (中等) — 35个

| # | 模块 | 文件 | 行号 | Bug 描述 |
|---|------|------|------|----------|
| 32 | 后端 | `backend/core/game_state.py` | 452-464 | `reset()` 未重置 `cycle_id` |
| 33 | 后端 | `backend/core/config.py` | 23-27 | 非原子写入，崩溃时配置损坏 |
| 34 | 后端 | `backend/ai/api_client.py` | 144-163 | 重试循环对 401/403 也重试 |
| 35 | 后端 | `backend/ai/api_client.py` | 174-175 | API 响应结构异常被静默吞掉 |
| 36 | 后端 | `backend/ai/translator.py` | 62 | 正则回退不支持嵌套 JSON |
| 37 | 后端 | `backend/ai/translator.py` | 88-90 | 未闭合 `<think>` 导致台词为空 |
| 38 | 后端 | `backend/ai/prompt_builder.py` | 43 | `custom_characters.json` 相对路径依赖 CWD |
| 39 | 后端 | `backend/ai/prompt_builder.py` | 87-90 | VLM 模块导入无 try/except |
| 40 | 后端 | `backend/resources/game_constants.py` | 1219-1245 | 日语否定检测回溯窗口仅3字符 |
| 41 | 后端 | `backend/resources/game_constants.py` | 1093-1105 | `same_language()` 子串匹配误判 |
| 42 | 后端 | `backend/resources/game_constants.py` | 1431-1435 | `glitch_text()` 未处理 KeyError |
| 43 | 后端 | `backend/websocket/game_ws.py` | 409,429,454 | `int(slot)` 无错误处理 |
| 44 | 后端 | `backend/websocket/game_ws.py` | 521 | Agent 循环任务引用丢失 |
| 45 | 后端 | `backend/websocket/game_ws.py` | 766-779 | tkinter 文件选择器线程不安全 |
| 46 | 后端 | `backend/websocket/game_ws.py` | 300 | 原始 LLM 回复存入聊天历史 |
| 47 | 后端 | `backend/resources/expanded_content.py` | 7-189 | 重复定义 `INTENT_RULES` |
| 48 | 后端 | `backend/resources/game_constants.py` | 799 vs 1471 | `EXACT_SPOKEN_TRANSLATIONS` 导入后立即被覆盖 |
| 49 | 后端 | `backend/main.py` | 37 | CORS `*` + credentials |
| 50 | 后端 | `backend/websocket/game_ws.py` | 81 | traceback 泄露给客户端 |
| 51 | 后端 | `backend/websocket/game_ws.py` | 56 | 存档写入 CWD |
| 52 | 后端 | `backend/main.py` | 113 | `uvicorn.run("main:app")` 字符串导入 |
| 53 | 桌面端 | `main.py` | 9 | 引用已移除的 tkinter 模块 |
| 54 | 桌面端 | `visual_fx/effects_system.py` | 512-536 | `physical_shake` 线程未捕获 cycle_id |
| 55 | 桌面端 | `visual_fx/effects_system.py` | 299-367 | 假错误弹窗无自动销毁 |
| 56 | 桌面端 | `visual_fx/effects_system.py` | 589-591 | 极端打字机速度乘数 (10x) |
| 57 | 桌面端 | `visual_fx/effects_system.py` | 439-506 | 重叠文本标签无上限 |
| 58 | 桌面端 | `visual_fx/particle_engine.py` | 52-84 | 画布销毁后异常刷屏 |
| 59 | 桌面端 | `audio/sound_manager.py` | 45 | pygame mixer 线程初始化 |
| 60 | 桌面端 | `audio/tts_client.py` | 46-52 | TTS 探测下载完整音频后丢弃 |
| 61 | 桌面端 | `ui/main_window.py` | 931-1100 | 后台线程直接写属性竞态 |
| 62 | 桌面端 | `ui/main_window.py` | — | 无 WM_DELETE_WINDOW 处理 |
| 63 | 桌面端 | `ui/main_window.py` | 1262-1268 | pulse_anim 动画循环累积 |
| 64 | 前端 | `frontend/src/App.vue` | 721,804,943 | 多处创建新 AudioContext |
| 65 | 前端 | `frontend/src/App.vue` | 360-372 | LAUNCH_GAME 在连接前发送 |
| 66 | 前端 | `frontend/src/App.vue` | 389-397 | LOAD_SLOT 在连接前发送 |
| 67 | 前端 | `frontend/src/App.vue` | 860-870 | mouse_attract 点击错误按钮 |
| 68 | 前端 | `frontend/src/App.vue` | 589-606 | playTTS 未处理 suspended AudioContext |
| 69 | 前端 | `frontend/src/components/GameTerminal.vue` | 749 | 打字机速度创建后固定不变 |
| 70 | 前端 | `frontend/src/components/GameTerminal.vue` | 794-813 | 三个 watcher 竞态 |
| 71 | 前端 | `frontend/src/components/GameTerminal.vue` | 301-304 | v-html XSS 风险 |
| 72 | 前端 | `frontend/src/assets/global.css` | 22-51 | z-index 9999/9998 覆盖所有弹窗 |
| 73 | 前端 | `frontend/src/composables/useWebSocket.js` | 92-98 | 重连无指数退避 |
| 74 | 前端 | `frontend/src/components/GlitchOverlay.vue` | 208-217 | subliminal_popup 定时器未清理 |

## LOW (低危) — 25个

| # | 模块 | 文件 | 行号 | Bug 描述 |
|---|------|------|------|----------|
| 75-104 | 各模块 | — | — | (详见第一轮完整列表: 配置异常吞掉、代理硬编码、`||` 过度清除、语言回退、WAV阈值、heartbeat重定义、game_over无反馈、CRUD异常吞掉、硬编码路径、死文档、window_name未用、空字符串、VLM结果丢弃、对话重叠永久文本、pady元组、chat_shake重复、glitch_block越界、文件I/O阻塞、chat_history竞态、未用导入、模板随机、激进替换、未导入onUnmounted、computed无依赖、border-inset错误) |

---

# 第二轮: 翻译系统深度审计

## 翻译管线 CRITICAL — 1个

| # | 文件 | 行号 | Bug 描述 |
|---|------|------|----------|
| T1 | `backend/websocket/game_ws.py` | 303 | **`spoken_for_history` 崩溃是翻译不显示的根因** — CHAT_APPEND 从未发送，翻译永远无法到达前端 (与 #1 重复) |

## 翻译管线 HIGH — 5个

| # | 文件 | 行号 | Bug 描述 |
|---|------|------|----------|
| T2 | `frontend/src/components/GameTerminal.vue` | 312-314 | **翻译显示双层括号** — `（ {{msg.translation}} ）`，但 translation 已含括号，渲染为 `（ （text） ）` |
| T3 | `frontend/src/App.vue` | 527-531 | **`translationText` 在打字机完成前被清空** — typewriter 读取时值已为空，翻译截断 |
| T4 | `backend/websocket/game_ws.py` | 543-588 | **初始问候语不发送 TRANSLATION_CHUNK** — 跨语言玩家看不到第一条消息的翻译 |
| T5 | `backend/ai/api_client.py` | 178-185 | **推理模型回复完全跳过翻译** — deepseek-v4-pro 的回复不经自愈翻译检查 |
| T6 | `backend/resources/expanded_content.py` | 449-555 | **EXACT_SPOKEN_TRANSLATIONS 仅映射到中文** — 日→英、英→日 离线翻译缺失 |

## 翻译管线 MEDIUM — 5个

| # | 文件 | 行号 | Bug 描述 |
|---|------|------|----------|
| T7 | `backend/resources/game_constants.py` | 799 vs 1471 | **EXACT_SPOKEN_TRANSLATIONS 被覆盖** — 100+ 精确翻译条目成为死代码 (与 #48 重复) |
| T8 | `backend/resources/game_constants.py` | 1686 | **`build_offline_translation_line` 对不支持的语言崩溃** — KeyError |
| T9 | `frontend/src/components/GameTerminal.vue` | 432-442 | **`injectSystemUsername` 破坏翻译文本** — 高怀疑度时替换"你"影响所有文本 |
| T10 | `backend/resources/game_constants.py` | 1700 | **半角括号翻译被误判为非翻译** — 重复追加翻译行 |
| T11 | `frontend/src/components/GameTerminal.vue` | 794-813 | **打字机 watcher 可能在动画中重启序列** |

## 翻译管线 LOW — 5个

| # | 文件 | 行号 | Bug 描述 |
|---|------|------|----------|
| T12 | `frontend/src/App.vue` | 437 | CHAT_HISTORY 正则不匹配双层括号 |
| T13 | `backend/resources/game_constants.py` | 1063-1087 | 混合语言回退消息语言检测错误 |
| T14 | `backend/ai/api_client.py` + `game_ws.py` | 201, 228 | `parse_api_response` 被调用两次 |
| T15 | `backend/resources/game_constants.py` | 1750 | 台词末尾括号被误提取为翻译 |
| T16 | `backend/ai/api_client.py` | 278 | 自愈翻译重建回复与 #1 崩溃叠加 |

---

# 第二轮: 聊天界面 UI/UX 审计

## UI/UX CRITICAL — 8个

| # | 文件 | 行号 | 问题描述 |
|---|------|------|----------|
| U1 | `GameTerminal.vue` | 4 | **固定 1100x800px 无响应式** — 笔记本/平板溢出，超宽屏浪费空间 |
| U2 | `GameTerminal.vue` | 9 | **角色立绘覆盖聊天内容** — absolute 定位遮挡左35%消息 |
| U3 | `GameTerminal.vue` | 262-314 | **7种字体大小无统一比例** — 12px/13px/14px/17px/18px/19px 混用 |
| U4 | `tailwind.config.js` | 14 | **`#550000` 对比度 1.7:1** — WCAG AA 要求 4.5:1，几乎不可见 |
| U5 | `GameTerminal.vue` | 374 | **placeholder `red-950/30` 不可见** — 有效颜色约 `#1a0303` |
| U6 | `GameTerminal.vue` | 274-277 | **用户消息无视觉容器** — 无背景/边框/内边距，与助手消息混为一体 |
| U7 | 全项目 | — | **零响应式设计** — 无媒体查询、无视口单位、无断点 |
| U8 | 全项目 | — | **三种视觉语言共存** — 终端风 + Win95 风 + 启动器风，不统一 |

## UI/UX HIGH — 19个

| # | 文件 | 行号 | 问题描述 |
|---|------|------|----------|
| U9 | `GameTerminal.vue` | 49 | 设置面板 3列 grid 在 1100px 内过于拥挤 |
| U10 | `GameTerminal.vue` | 366 | 输入框仅 48px 高，点击目标过小 (WCAG 要求 44px+) |
| U11 | `GameTerminal.vue` | 274,293 | 用户 18px/助手 19px 过大，终端风应 14-16px |
| U12 | `GameTerminal.vue` | 多处 | `font-mono` 在 class 和 inline style 重复定义 |
| U13 | `GameTerminal.vue` | 282-314 | think/speech/translation 视觉权重相同，无层级 |
| U14 | `GameTerminal.vue` | 287,326 | "COGNITIVE ANALYSIS" 标签硬编码未本地化 |
| U15 | `GameTerminal.vue` | 374 | 输入框禁用状态无 CSS 反馈 |
| U16 | `GameTerminal.vue` | 381-387 | 发送按钮 hijack/normal 状态切换突兀 |
| U17 | `GameTerminal.vue` | 576-591 | Unicode 方块字符跨平台渲染不一致 |
| U18 | `GameTerminal.vue` | 199-223 | 三种进度条风格共存 |
| U19 | `GameTerminal.vue` | 749 | 打字机 setInterval 不同步 requestAnimationFrame |
| U20 | `GameTerminal.vue` | 816-821 | 每个字符触发 scrollTop，布局引擎开销大 |
| U21 | `GameTerminal.vue` | 254-256 | 140px 眼睛水印与内容竞争注意力 |
| U22 | `GameTerminal.vue` + `Launcher.vue` + `FatalErrorModal.vue` | 多处 | 三处独立 LOCALIZATION 字典，添加语言需改3个文件 |
| U23 | `global.css` | 122-130 | `mita-interactive-ui` hover 偏斜 -4deg 过于激进 |
| U24 | `global.css` | — | 无 `-webkit-font-smoothing`/`text-rendering` 设置 |
| U25 | `GameTerminal.vue` | 285,310,355 | 每条助手消息都有 text-shadow，降低清晰度 |
| U26 | `App.vue` | 26-39 | 断线连接覆盖层无法返回启动器 |
| U27 | 全项目 | — | 无 CSS 自定义属性 (颜色主题变量) |

## UI/UX MEDIUM — 22个

| # | 文件 | 行号 | 问题描述 |
|---|------|------|----------|
| U28 | `GameTerminal.vue` | 20 | 标题栏 32px 过薄 |
| U29 | `GameTerminal.vue` | 235 | ECG 45px 占用宝贵垂直空间 |
| U30 | `GameTerminal.vue` | 264,269,274 | `leading-relaxed` 对等宽字体过宽 |
| U31 | `GameTerminal.vue` | 287 | `tracking-widest` 对等宽大写字母过宽 |
| U32 | `GameTerminal.vue` | 23 | `text-green-700` 在黑色背景对比度 3.2:1 |
| U33 | `GameTerminal.vue` | 310-311 | 翻译 text-shadow 半径 10px 造成光晕 bleed |
| U34 | `GameTerminal.vue` | 284 | think 块背景 `#080101` 与 `#000000` 几乎不可区分 |
| U35 | `global.css` | 69-72 | 选择色纯红黑，可读性差 |
| U36 | `GameTerminal.vue` | 309 | 翻译分隔线 `border-red-950/40` 几乎不可见 |
| U37 | `GameTerminal.vue` | 280 | think/speech/translation 间距不一致 |
| U38 | `GameTerminal.vue` | 367 | `>` 提示符 `text-red-900` 对比度 2.1:1 |
| U39 | `GameTerminal.vue` | 289,313,358 | 英文模式也用全角括号 `（）` |
| U40 | `global.css` | 53-66 | 自定义滚动条仅 WebKit 有效 |
| U41 | `GlitchOverlay.vue` | 2-189 | 多特效同时激活导致掉帧 |
| U42 | `Launcher.vue` | 20 | `animate-pulse` 持续分散注意力 |
| U43 | `global.css` | 15-16 | 纯黑 `#000000` 造成 OLED 拖影和眼疲劳 |
| U44 | `global.css` | 37-38 | 扫描线 z-index 9999 破坏堆叠 |
| U45 | `global.css` | 41-51 | 暗角影响所有页面 (不仅是游戏) |
| U46 | `GameTerminal.vue` | 47 | 配置面板与聊天区域间距不一致 |
| U47 | `GameTerminal.vue` | 255 | 眼睛 emoji 跨平台渲染不一致 |
| U48 | `GameTerminal.vue` | 多处 | 混用 emoji 和文字符号 |
| U49 | `GameTerminal.vue` | 5 | `select-none` 阻止复制聊天内容 |

## UI/UX LOW — 10个

| # | 文件 | 行号 | 问题描述 |
|---|------|------|----------|
| U50 | `global.css` | 17 | CJK 等宽字体 Consolas 全角/半角不一致 |
| U51 | `GameTerminal.vue` | 262 | `mb-4` 统一间距，无角色切换额外间距 |
| U52 | `GameTerminal.vue` | 280 | `gap-1.5` 与 `mb-3` 间距不一致 |
| U53 | `StatusBar.vue` | — | 死代码组件未使用 |
| U54 | `SaveSlotsModal.vue` | 155-158 | `border-inset` 实为 `solid` |
| U55 | `global.css` | 53-66 vs 259-275 | 两套冲突的滚动条样式 |
| U56 | `global.css` | 118 | 血滴动画无限循环 GPU 压力 |
| U57 | `FatalErrorModal.vue` | — | 弹窗无过渡动画 |
| U58 | `GameTerminal.vue` | 285,310,355 | 内联样式应移至 CSS 类 |
| U59 | `GameTerminal.vue` | 1090-1097 + `Launcher.vue` + `App.vue` | `breath-scale` 重复定义三次 |

---

# 第二轮: 遗漏代码 Bug

## 遗漏 HIGH — 4个

| # | 文件 | 行号 | Bug 描述 |
|---|------|------|----------|
| B1 | `frontend/src/components/GameTerminal.vue` | 1015 | **TTS URL 保存用错 key** — 前端发 `gpt_sovits_url`，后端白名单只有 `tts_base`，配置不保存 |
| B2 | `backend/resources/game_constants.py` | 1534 | **翻译 key 错字** — `痛よ` 应为 `痛いよ`，精确翻译永远匹配不到 |
| B3 | `frontend/src/composables/useGameState.js` | 92-95 | **`applyDelta` 不应用增量** — 仅同步 ECG，不更新 state (与 #25 部分重复但更详细) |
| B4 | `backend/resources/game_constants.py` | 1219-1245 | **日语否定回溯窗口太短** — `ではない`(4字符) 超出3字符窗口 |

## 遗漏 MEDIUM — 7个

| # | 文件 | 行号 | Bug 描述 |
|---|------|------|----------|
| B5 | `frontend/src/App.vue` | 998-1003 | 重启不清理 fakePopups/bsodActive/screenFreezeActive |
| B6 | `backend/resources/game_constants.py` | 1063-1087 | 纯汉字日文被误检测为中文 |
| B7 | `frontend/src/App.vue` | 324-333 | `carnageStyle()` Math.random() 每次渲染抖动 |
| B8 | `frontend/src/App.vue` | 886-919 | day_loop/title_corruption 定时器无法取消 |
| B9 | `backend/websocket/game_ws.py` | 131-148 | 快速发消息导致 LLM 上下文孤立用户消息 |
| B10 | `backend/websocket/game_ws.py` | 336-384 | `_schedule_glitch` 永不移除 scanlines 等效果 |
| B11 | `backend/websocket/game_ws.py` | 543-588 | `_send_initial_plot` 用本地问候语，忽略 INITIAL_GREETINGS 常量 |

## 遗漏 LOW — 5个

| # | 文件 | 行号 | Bug 描述 |
|---|------|------|----------|
| B12 | `frontend/src/components/GameTerminal.vue` | 611-615 | `inputPlaceholder` computed 死代码 |
| B13 | `backend/resources/game_constants.py` | 1660-1680 | 自定义正则匹配模式死代码 |
| B14 | `frontend/src/App.vue` | 1036-1045 | 退出不清理 activeGlitches |
| B15 | `frontend/src/components/GameTerminal.vue` | 432-442 | "你"全局替换破坏语法 (与 T9 重复) |
| B16 | `backend/ai/api_client.py` | 178-185 | 推理模型跳过自愈翻译 (与 T5 重复) |

---

# 合并去重汇总

| 严重程度 | 第一轮 | 翻译系统 | UI/UX | 遗漏Bug | **去重总计** |
|----------|--------|----------|-------|---------|-------------|
| **Critical** | 9 | 1 | 8 | 0 | **13** |
| **High** | 22 | 5 | 19 | 4 | **42** |
| **Medium** | 35 | 5 | 22 | 7 | **55** |
| **Low** | 25 | 5 | 10 | 5 | **38** |
| **合计** | 91 | 16 | 59 | 16 | **~148** |

> 注: 部分 bug 跨分类重复 (如 `spoken_for_history` 同时出现在代码逻辑和翻译系统)，去重后实际独立 bug 约 **120-130 个**。

---

# 修复优先级路线图

## Phase 0: 紧急修复 (阻断性 Bug)

这些 bug 导致游戏完全不可玩，必须首先修复：

1. **`spoken_for_history` NameError** (`game_ws.py:303`) → 改为 `spoken`
2. **API Key 泄露** (`yandere_config.json`) → 移除 key，加入 `.gitignore`
3. **Agent 无认证接管** (`game_ws.py:492`) → 添加 localhost 校验
4. **EXACT_SPOKEN_TRANSLATIONS 被覆盖** (`game_constants.py:799`) → 移除重复导入
5. **REQUEST_FILE_PICKER 未注册** (`protocol.py:27`) → 添加到 CLIENT_TYPES + SERVER_TYPES

## Phase 1: 核心功能修复 (翻译 + TTS)

6. **翻译双层括号** (`GameTerminal.vue:312`) → 移除外层 `（）`
7. **translationText 提前清空** (`App.vue:527`) → 延迟到打字机完成后
8. **初始问候语无翻译** (`game_ws.py:543`) → 发送 TRANSLATION_CHUNK
9. **推理模型跳过翻译** (`api_client.py:178`) → 合并自愈翻译逻辑
10. **TTS 路径解析空操作** (`tts_client.py:142`) → 直接重赋值原始变量
11. **TTS URL 保存 key 不匹配** (`GameTerminal.vue:1015`) → 统一为 `tts_base`
12. **applyDelta 不应用增量** (`useGameState.js:92`) → 先更新 state 再同步 ECG

## Phase 2: 前端 UI 大改版

13. **响应式容器** → `max-w-[1100px] w-full max-h-[90vh]`
14. **CSS 自定义属性** → `:root` 定义 `--color-primary` 等
15. **字体比例统一** → 最多 4 级: Caption 11px, Body 14px, Message 16px, Emphasis 18px
16. **消息容器设计** → 用户/助手消息添加背景、边框、内边距
17. **think/speech/translation 层级** → think 最小最暗，speech 最亮，translation 次之
18. **z-index 体系** → Content 0-10, UI 10-20, Overlay 30-40, Modal 50-60, Critical 100, CRT 200
19. **共享 i18n** → 提取所有 LOCALIZATION 到 `composables/useI18n.js`
20. **去除内联样式** → 移至 scoped CSS 类

## Phase 3: 稳定性 + 质量

21. **AudioContext 共享** → 全局单例 provide/inject
22. **事件监听器清理** → 所有 addEventListener 配对 removeEventListener
23. **定时器清理** → 所有 setInterval 存储 ref，onUnmounted 清除
24. **竞态条件** → cycle_id 快照、消息队列、线程安全读写
25. **Pillow 10+ 兼容** → `Image.Resampling.BILINEAR` 回退
26. **日语否定检测** → 回溯窗口扩大到 6 字符
27. **语言检测** → 纯汉字日文特殊处理

## Phase 4: 抛光 (大厂品质)

28. **自定义字体加载** → 加载等宽 CJK 字体 (如 Sarasa Mono)
29. **背景纹理/噪声** → 添加微妙噪点增加质感
30. **状态过渡动画** → 弹窗/特效入场退场
31. **键盘焦点样式** → `focus-visible:ring-2 ring-red-500`
32. **字体渲染** → `-webkit-font-smoothing: antialiased`
33. **空状态/加载态** → 引导文本、连接倒计时
34. **滚动条 Firefox 支持** → `scrollbar-width: thin; scrollbar-color`
35. **近黑色背景** → `#0a0a0a` 替代纯黑 `#000000`
