# Saki 网页版 — 全部恐怖视觉效果详解

> 统计范围：仅 `frontend/` + `backend/`，不含桌面端 Tkinter。
> 总计：**72 个视觉恐怖效果** + **9 个音效**

---

## 一、全局常驻效果（始终运行，无需触发）

| # | 名称 | 实现位置 | 技术 | 视觉效果 |
|---|------|---------|------|---------|
| 1 | CRT 扫描线 | `global.css` `body::after` | `repeating-linear-gradient` 透明/黑色 2px 条纹，z-index 9999 | 整个屏幕覆盖 CRT 显示器扫描线纹理 |
| 2 | CRT 暗角 | `global.css` `body::before` | `radial-gradient` 中心透明 50% → 边缘 82% 黑色，z-index 9998 | 屏幕四角变暗，模拟老式显示器暗角 |
| 3 | VHS 追踪线 | `global.css` `.vhs-tracking-line` | 固定 6px 红色水平线 + `box-shadow` 发光 + `vhs-line-scroll` 7 秒垂直滚动 | 一条带红光的水平线从上到下缓慢扫过屏幕 |
| 4 | 3D 透视倾斜 | `global.css` `.mita-screen-tilt` | `perspective(1200px) rotateX(2deg) rotateY(-1.2deg) scale(0.98)` | 屏幕微微向后倾斜，产生有机的不稳定感 |

---

## 二、GlitchOverlay.vue 可触发覆盖层（20 个）

所有效果由后端 `GLITCH_TRIGGER` 消息激活，条件渲染在 `v-if="activeGlitches.has('X')"` 之下。

### 2.1 scanlines — CRT 扫描线增强
- **触发**：suspicion >= 35
- **实现**：`repeating-linear-gradient(0deg, transparent 2px, rgba(0,0,0,0.15) 4px)`
- **持续时间**：2-4 秒
- **效果**：在常驻扫描线之上叠加额外一层

### 2.2 static_noise — 雪花噪点
- **触发**：suspicion >= 55
- **实现**：`repeating-linear-gradient` 水平+垂直 1-3px 红黑交替条纹，透明度随 suspicion 动态变化
- **持续时间**：2-4 秒
- **效果**：屏幕出现红黑色随机噪点纹理

### 2.3 blood_pulse — 血液脉冲
- **触发**：suspicion >= 75
- **实现**：`radial-gradient(ellipse at center, transparent 50%, rgba(180,0,0,0.4) 100%)` + CSS `animate-pulse`
- **持续时间**：2-4 秒
- **效果**：屏幕边缘脉冲式泛红，像血液从四周涌入

### 2.4 chromatic_tear — 色差撕裂
- **触发**：suspicion >= 55
- **实现**：右侧 2px 红色竖条 + 左侧 2px 青色竖条
- **持续时间**：2-4 秒
- **效果**：屏幕边缘 RGB 通道分离，模拟镜头色差

### 2.5 screen_tear — 屏幕撕裂
- **触发**：suspicion >= 75（scream_radial 组）
- **实现**：8 条不同高度(2-7px)的半透明白色水平线，位置伪随机分布
- **持续时间**：2-4 秒
- **效果**：多条白色横线撕裂画面

### 2.6 color_invert — 颜色反转
- **触发**：suspicion >= 85
- **实现**：`mix-blend-mode: difference` + 红色半透明叠加
- **持续时间**：2-4 秒
- **效果**：全屏颜色反转闪烁，红光笼罩

### 2.7 widget_melt — 组件熔化
- **触发**：suspicion >= 85
- **实现**：`backdrop-filter: blur(0px)` + `mask-image: linear-gradient(to bottom, black 60%, transparent 100%)`
- **持续时间**：2-4 秒
- **效果**：UI 底部 40% 逐渐模糊消失，像被熔掉

### 2.8 vignette_squeeze — 暗角挤压
- **触发**：suspicion >= 35
- **实现**：`radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.8) 100%)`
- **持续时间**：2-4 秒
- **效果**：暗角收缩，可见区域被压缩

### 2.9 fake_error — 虚假错误弹窗
- **触发**：suspicion >= 85
- **实现**：`bg-[#000080]` 蓝色背景 + 白色边框，显示 "SYSTEM ERROR 0x0000007B" + "INACCESSIBLE_BOOT_DEVICE"
- **持续时间**：2-4 秒
- **效果**：经典蓝屏风格的错误对话框出现在屏幕 1/3 位置

### 2.10 subliminal_popup — 潜意识弹窗
- **触发**：suspicion >= 75
- **实现**：60px 大号红色加粗文字，居中脉冲显示，内容每 150ms 循环切换 7 种病娇短语
- **持续时间**：2 秒
- **效果**：巨型病娇文字在屏幕中央快速闪烁切换

### 2.11 mouse_attract — 鼠标吸引
- **触发**：suspicion >= 85
- **实现**：屏幕中央 16px 红色圆形准星 + `box-shadow` 红色发光
- **持续时间**：2-4 秒
- **效果**：红色靶心标记出现在屏幕中心

### 2.12 blood_drips — 滴血
- **触发**：手动触发
- **实现**：6 条 1px 宽 80px 高的红黑竖线，`animate-blood-drip` 动画，位置伪随机，时差错开
- **持续时间**：2-4 秒
- **效果**：多条血滴从屏幕上方往下流

### 2.13 ghost_text — 幻影文字
- **触发**：suspicion >= 55
- **实现**：48px 红色加粗文字居中脉冲显示，内容三语本地化："看着我看着我…" / "look at me…" / "見て見て…"
- **持续时间**：120ms
- **效果**：巨大病娇文字闪过一瞬

### 2.14 evaporate — 文字蒸发
- **触发**：suspicion >= 55
- **实现**：`backdrop-filter: blur(2px)` + `filter: contrast(0.6) blur(1.5px)` + `animate-evaporate-flicker`
- **持续时间**：150ms
- **效果**：整个画面瞬间模糊+低对比度闪烁

### 2.15 suffocation — 窒息覆盖
- **触发**：suspicion >= 75
- **实现**：全屏纯黑背景 + 60px 红色加粗居中文字 + 👁️👁️ emoji，三语本地化
- **持续时间**：300ms
- **效果**：全屏黑底+巨大眼球+窒息文字闪过

### 2.16 dialogue_overlap — 对话重叠
- **触发**：suspicion >= 75
- **实现**：5 层旋转堆叠文字，字号 24→84px 递增，旋转 -16°→16°，三语本地化
- **持续时间**：500ms
- **效果**：多层病娇文字以不同角度、大小叠加显示

### 2.17 scream_radial — 尖叫放射线
- **触发**：suspicion >= 75
- **实现**：Canvas 绘制 30-60 条放射线，从屏幕中心向外辐射，随机角度微扰，红色系随机透明度
- **持续时间**：400ms
- **效果**：从屏幕中心爆发的红色放射线束

### 2.18 dungeon_grid — 地牢网格
- **触发**：suspicion >= 35
- **实现**：CSS `background-image` 双重 `linear-gradient` 40px 网格 + `rgba(60,0,0,0.3)` 暗红线条
- **持续时间**：600ms
- **效果**：暗红色地牢网格覆盖全屏

### 2.19 corruption_blocks — 数据损坏方块
- **触发**：suspicion >= 55
- **实现**：6-16 个随机位置、随机尺寸(20-120px宽 × 8-68px高)的矩形，颜色从红/青/黑/品红随机选取
- **持续时间**：300ms
- **效果**：随机彩色方块覆盖屏幕，模拟数据损坏

### 2.20 blood_splatter — 血溅
- **触发**：suspicion >= 75
- **实现**：8 个随机位置/大小的 `radial-gradient` 椭圆，深红色系 `rgba(120-180, 0, 10-25, 0.5)`
- **持续时间**：600ms
- **效果**：多处暗红色血溅斑点覆盖屏幕

### 2.21 pixel_melt — 像素熔化
- **触发**：suspicion >= 75
- **实现**：Canvas 绘制 20-50 条竖直细线，从屏幕上方往下流 30-180px，红色系随机透明度
- **持续时间**：1000ms
- **效果**：大量红色竖线从顶部往下流淌，模拟像素融化

---

## 三、App.vue 内联覆盖层（7 个）

### 3.1 psychic_strobe — 精神脉冲闪光
- **触发**：suspicion >= 85
- **实现**：全屏 `div` 使用 `stroke-fast` 动画：红色 `rgba(255,0,0,0.35)` ↔ 黑色 `rgba(0,0,0,0.85)` 每 0.08 秒切换
- **持续时间**：1800ms
- **效果**：极快速的红黑交替全屏闪光

### 3.2 carnage_mode labels — 屠杀模式标签（80 个）
- **触发**：suspicion >= 85
- **实现**：80 个随机位置 `<div>`，20 种病娇文字（中/英/日），字号 10-30px，随机旋转，脉冲动画，时差错开
- **持续时间**：持续到 glitch 结束
- **效果**：屏幕布满 80 个随机分布、旋转、闪烁的病娇文字

### 3.3 NT BSOD overlay — NT 蓝屏死机
- **触发**：suspicion >= 85 → `fatal_error`
- **实现**：全屏深红黑背景，220px 巨型 👁️👁️ 水印，VHS 追踪线，色差文字标题 "CRITICAL WARNING: SAKI SYNAPSE COUPLING DEADLOCK"，系统状态指示器，点击或按键关闭
- **音效**：60Hz 锯齿波低频嗡鸣 1.2 秒
- **关闭时触发**：跳吓爆发（earthquake + color_invert + static_noise + subliminal_popup + chromatic_tear 持续 1.6 秒）+ 恐惧尖啸音效

### 3.4 fake_popups_cascade — 虚假弹窗级联（15 个）
- **触发**：suspicion >= 85 → `fake_error`
- **实现**：每 180ms 生成一个 Windows 经典风格弹窗，随机位置，5 种标题随机 + 6 种错误消息随机，最多 15 个
- **音效**：每个弹窗播放双音方波错误提示音
- **特殊行为**：关闭弹窗有 30% 概率触发 Saki 的"增殖"——额外生成 2 个弹窗

### 3.5 screen_freeze_modal — 失去响应窗口
- **触发**：suspicion >= 85 → `fatal_error`
- **实现**：灰色标题栏 "saki_terminal.exe 失去响应" + "该应用程序未响应" 消息 + "结束进程"/"等待响应" 按钮
- **效果**：模拟 Windows 应用程序无响应对话框

### 3.6 fake_cursor(☠) — 骷髅鼠标劫持
- **触发**：suspicion >= 85 → `mouse_attract`
- **实现**：`☠` 骷髅字符替代鼠标光标，跟随鼠标移动但有磁力偏移（被吸向最近的按钮位置）
- **效果**：鼠标变成红色发光的骷髅头，光标被磁力拉向按钮

### 3.7 anti-escape overlay — 反逃跑覆盖层
- **触发**：窗口宽度 < 1000px
- **实现**：全屏黑色覆盖 `bg-opacity-95`，居中红色脉冲文字 "不要企图逃避我的视线..." + "把窗口放大，看着我！"
- **效果**：窗口缩小时封锁界面，强迫玩家恢复窗口大小

---

## 四、App.vue 行为级特效（5 个）

### 4.1 earthquake — 窗口地震
- **触发**：suspicion >= 75
- **实现**：CSS `animate-earthquake`：10 步随机 translate (-4px→+4px X/Y)，0.2 秒循环
- **持续时间**：1200ms
- **效果**：整个游戏窗口剧烈抖动

### 4.2 crt_jolt — CRT 抖动
- **触发**：suspicion >= 75
- **实现**：CSS `animate-crt-jolt`：极端位移 (-18px→+14px) + scale (0.97→1.04) + skew (-5°→4°) + hue-rotate (0°→270°)，0.4 秒循环
- **持续时间**：2-4 秒
- **效果**：画面剧烈变形、色相旋转、缩放扭曲

### 4.3 font_shake — 字体抖动
- **触发**：suspicion >= 55
- **实现**：CSS `animate-shake`：4 步小幅度 translate (-2px→+2px)，0.15 秒无限循环，应用于聊天文字
- **持续时间**：1200ms
- **效果**：聊天文字微微抖动

### 4.4 title_corruption — 标题栏循环
- **触发**：suspicion >= 85
- **实现**：JavaScript 循环替换 `document.title`：8 次 × 80ms = 640ms，每次设为随机病娇短语
- **效果**：浏览器标签页标题快速切换为病娇文字

### 4.5 day_loop — 天数随机闪烁
- **触发**：suspicion >= 75
- **实现**：JavaScript 每 50ms 将天数设为 1-999 的随机值，12 次 = 600ms
- **效果**：天数显示疯狂跳变

---

## 五、GlitchTextOverlay.vue 屠杀序列（5 个阶段）

仅当 `carnage_mode` 激活时触发，总时长约 4.4 秒。

### 5.1 散落文字生成
- 每 45ms 生成一个病娇文字块，最多 95 个
- 字号 26→90px 逐渐增大（后期增长 1.9x），随机旋转 -25°→25°
- 颜色从 5 种红色随机选取：`#ff0000` / `#ef4444` / `#dc2626` / `#b91c1c` / `#7f1d1d`
- 35% 概率应用 `shake-intense` 振动动画，其余使用 `pulse-glitch` 色相翻转
- 文字带有红色 `text-shadow` 发光
- 奇数 tick 播放锯齿波点击音效

### 5.2 渐进暗角收缩
- 暗角半径从 100% 逐步缩小到 8%（-1.1%/tick）
- 红色 `box-shadow: inset` 逐渐增强

### 5.3 渐进模糊+红化
- `backdrop-filter: blur` 从 0 增加到 14px（+0.16/tick）
- 背景红色暗度从 0 增加到 1（+0.015/tick）

### 5.4 高潮反转闪光
- 文字生成完成后触发
- 播放高潮尖啸音效（锯齿波 2900Hz→40Hz + 方波 1400Hz→100Hz）
- 全屏 `color_invert` 反转 150ms

### 5.5 高潮黑屏
- 反转闪光后，纯黑覆盖层淡入
- 保持 1800ms 后一切消失

**音效**：此序列全程伴随窒息声景：
- 深层嗡鸣：锯齿波 30Hz→68Hz 渐变 + 低通滤波 90→180Hz
- 金属刮擦：三角波 700Hz 被 8Hz LFO 调制 + 高通滤波 900Hz
- 加速心跳：55Hz 正弦波双脉冲，BPM 从 60 加速到 150

---

## 六、FatalErrorModal.vue（1 个）

### 6.1 Fatal Error 对话框
- **触发**：suspicion >= 85 → `fatal_error`
- **实现**：Windows 95 经典风格对话框，海军蓝 `#000080` 标题栏，灰色 `#c0c0c0` 主体，红底白叉错误图标，3D 凸起按钮
- **三语本地化**：
  - 中文："无法从系统内存中抹除 纱希 (Saki)" + "玩家尝试逃跑。精神控制已激活。"
  - English："Cannot erase Saki from system memory." + "User tried to escape. Mind control active."
  - 日本語："システムメモリから紗希を抹消できません。" + "ユーザーが脱走を試みました。精神支配を起動中。"
- **音效**：挂载时播放 150Hz/220Hz 方波双音警告音

---

## 七、CSS 关键帧动画（17 个）

| # | 名称 | 文件 | 参数 | 用途 |
|---|------|------|------|------|
| 1 | `crt-flicker` | global.css | opacity 0.94↔1.0 | CRT 闪烁 |
| 2 | `scanline-scroll` | global.css | translateY -100%→100vh | 扫描线滚动 |
| 3 | `text-flicker` | global.css | opacity 0.75↔1.0 | 文字闪烁 |
| 4 | `red-pulse` | global.css | rgba(200,0,0,0)↔0.12 | 红色背景脉冲 |
| 5 | `earthquake` | global.css | 10 步随机 translate，0.2s | 地震抖动 |
| 6 | `shake` | global.css | 4 步小幅度 translate，0.15s | 微抖动 |
| 7 | `glitch-text` | global.css | translate + opacity 振荡，0.1s | 故障文字 |
| 8 | `pulse-red` | global.css | box-shadow 0→20px 扩散，1.5s | 红色发光脉冲 |
| 9 | `evaporate-flicker` | global.css | blur(3px) contrast(0.5)↔none，0.15s | 蒸发模糊 |
| 10 | `vhs-line-scroll` | global.css | top -10%→110%，7s | VHS 追踪线 |
| 11 | `chromatic-flicker` | global.css | text-shadow 偏移振荡，0.2s | 色差文字 |
| 12 | `blood-drip-letter` | global.css | translateY(0)→50px + 变色+模糊，2.5s | 滴血文字 |
| 13 | `blink-caret` | global.css | 背景色 step-end 闪烁，0.8s | 复古光标 |
| 14 | `strobe-fast` | App.vue scoped | 红↔黑交替，0.08s | 精神脉冲 |
| 15 | `crt-jolt` | App.vue scoped | translate + scale + skew + hue-rotate，0.4s | CRT 剧烈抖动 |
| 16 | `breath-scale` | App.vue scoped | scale(1)↔1.02，3-4s | 角色呼吸 |
| 17 | `shake-intense` | GlitchTextOverlay scoped | 5 步大位移 translate ±7px + rotate ±5° | 高潮文字振动 |

---

## 八、CSS 特效工具类（10 个）

| # | 类名 | 效果 |
|---|------|------|
| 1 | `.vhs-tracking-line` | 固定红色发光水平追踪线，7 秒垂直扫描 |
| 2 | `.mita-screen-tilt` | 3D 透视屏幕倾斜 `perspective(1200px) rotateX(2deg) rotateY(-1.2deg)` |
| 3 | `.mita-chromatic-text` | 红/青分裂 text-shadow + chromatic-flicker 动画 |
| 4 | `.animate-blood-drips` | 文字滴血动画（下落+变红+模糊） |
| 5 | `.mita-interactive-ui` | hover 时 skew(-4deg) + 红色边框发光 |
| 6 | `.chat-shattered` | 裂纹对话框：斜线"裂痕"渐变 + 红色发光 + 内嵌 earthquake 动画 |
| 7 | `.animate-earthquake` | 应用 earthquake 关键帧 |
| 8 | `.animate-shake` | 应用 shake 关键帧 |
| 9 | `.animate-glitch-text` | 应用 glitch-text 关键帧 |
| 10 | `.animate-pulse-red` | 应用 pulse-red 关键帧 |

---

## 九、音效系统（9 个）

| # | 名称 | 实现位置 | 合成方式 | 触发条件 |
|---|------|---------|---------|---------|
| 1 | 心跳合成器 | App.vue | Web Audio API 双脉冲正弦波 (55/59Hz)，BPM 52→150 随 suspicion 动态加速 | 游戏全程持续播放 |
| 2 | 恐惧尖啸 | App.vue `playHorrorScreechSound()` | 锯齿波 880Hz→80Hz + 方波 320Hz→40Hz + peaking 滤波器 | 关闭 BSOD/FatalError 时 |
| 3 | BSOD 低频嗡鸣 | App.vue `triggerBsodGlitch()` | 锯齿波 60Hz 持续 1.2 秒 | BSOD 显示期间 |
| 4 | 错误提示音 | App.vue `spawnFakePopupsCascade()` | 方波双音 (120-180Hz / 180-240Hz)，0.3 秒渐弱 | 每个虚假弹窗生成时 |
| 5 | 打字机故障蜂鸣 | GameTerminal.vue `playTypewriterBeep()` | 锯齿波 120-270Hz→30Hz 频率骤降 | speed_shift 激活时 |
| 6 | 致命错误双音 | FatalErrorModal.vue `playSystemBeep()` | 方波双音 150Hz/220Hz，间隔 40ms，0.35 秒渐弱 | FatalErrorModal 挂载时 |
| 7 | 窒息声景 | GlitchTextOverlay.vue `playSuffocatingSoundscape()` | 深层嗡鸣(锯齿波 30→68Hz + 低通) + 金属刮擦(三角波 700Hz LFO 调制 + 高通) + 加速心跳 | carnage_mode 屠杀序列全程 |
| 8 | 高潮尖啸 | GlitchTextOverlay.vue `playClimaxScreech()` | 锯齿波 2900Hz→40Hz + 方波 1400Hz→100Hz + peaking 滤波器 Q=18 | 屠杀序列高潮阶段 |
| 9 | 生成点击音 | GlitchTextOverlay.vue spawn 循环内 | 锯齿波 50-110Hz 随机频率，0.1 秒 | 屠杀序列每 2 tick 触发一次 |

---

## 十、后端触发阈值速查表

| 等级 | 条件 | 触发的特效 |
|------|------|-----------|
| **Mild** | suspicion >= 35 | `scanlines`, `vignette_squeeze`, `dungeon_grid` |
| **Moderate** | suspicion >= 55 | `static_noise`, `chromatic_tear`, `font_shake`, `ghost_text`, `evaporate`, `corruption_blocks` |
| **Severe** | suspicion >= 75 | `blood_pulse`, `earthquake`, `subliminal_popup`, `crt_jolt`, `suffocation`, `dialogue_overlap`, `day_loop`, `scream_radial`, `blood_splatter`, `pixel_melt` |
| **Severe** | escape_rate >= 75 | `keyboard_hijack` |
| **Carnage** | suspicion >= 85 | `carnage_mode`, `color_invert`, `widget_melt`, `fake_error`, `fatal_error`, `mouse_attract`, `psychic_strobe`, `title_corruption`, `speed_shift` |

---

## 总计

| 类别 | 数量 |
|------|------|
| 全局常驻效果 | 4 |
| GlitchOverlay 可触发效果 | 21 |
| App.vue 内联覆盖层 | 7 |
| App.vue 行为特效 | 5 |
| GlitchTextOverlay 屠杀阶段 | 5 |
| FatalErrorModal | 1 |
| CSS 关键帧动画 | 17 |
| CSS 特效工具类 | 10 |
| 结局覆盖层渐变 | 3（good/neutral/bad） |
| 键盘劫持 | 1 |
| **视觉总计** | **72** |
| 音效总计 | 9 |
