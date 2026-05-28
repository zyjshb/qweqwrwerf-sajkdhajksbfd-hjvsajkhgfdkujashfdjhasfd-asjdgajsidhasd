# Saki 项目修改文档

## 修改日期
2026-05-28

## 修改目标
1. 让 `deepseek-v4-pro` 推理模型正确工作（内心独白 + 数值更新）
2. 网页版继承桌面版缺失的功能（12 个故障特效 + 翻译显示 + 消息处理）

---

## 修改文件清单（共 8 个文件）

### 1. `backend/ai/api_client.py` — 推理模型支持（核心修复）

**修改位置**：第 171-266 行 `if response.status_code == 200:` 块

**修改内容**：
- 获取 API 响应后，检查 `message.get("reasoning_content")` 字段
- 如果存在（推理模型如 deepseek-v4-pro）：
  - 用 `reasoning_content` 包裹为 `<think>...</think>` 块
  - 用 `content` 作为台词正文
  - 调用 `classify_player_intent()` + `roll_delta_for_intent()` 自动生成 JSON delta
  - 拼接为标准格式：`<think>{RC}</think>\n{content}\n||{json_delta}||`
- 如果不存在（标准模型）：保持原有流程不变

### 2. `ai/api_client.py` — 同上修改（桌面版）

与上一个文件完全相同的修改，确保桌面版也能使用推理模型。

### 3. `backend/websocket/game_ws.py` — 翻译提取 + 新特效调度

**修改位置 1**：第 28-32 行导入
- 新增导入 `extract_terminal_parenthetical_translation`, `strip_terminal_parenthetical_translation`

**修改位置 2**：`_process_reply` 方法（第 233-238 行）
- 从 spoken 文本中提取括号翻译 `（）`，单独发送 `TRANSLATION_CHUNK`
- 为聊天记录剥离翻译，避免重复显示

**修改位置 3**：`_schedule_glitch` 方法（第 341-366 行）
- Mild (s>=35)：新增 `dungeon_grid`
- Moderate (s>=55)：新增 `ghost_text`, `evaporate`, `corruption_blocks`
- Severe (s>=75)：新增 `suffocation`, `dialogue_overlap`, `day_loop`, `scream_radial`, `blood_splatter`, `pixel_melt`
- Carnage (s>=85)：新增 `title_corruption`, `speed_shift`

### 4. `frontend/src/components/GlitchOverlay.vue` — 12 个新故障特效

**模板部分**：在 `</template>` 前新增 12 个特效组件：
- `ghost_text` — 全屏大号红色文字，120ms 闪烁
- `evaporate` — 聊天区 CSS blur + contrast 闪动，150ms
- `suffocation` — 全屏黑色覆盖 + "看着 我！" 大号文字，300ms
- `dialogue_overlap` — 5 层旋转堆叠的重叠文字，500ms
- `scream_radial` — Canvas 绘制的放射线覆盖，400ms
- `dungeon_grid` — CSS 网格图案覆盖，600ms
- `corruption_blocks` — 6-15 个随机位置/颜色的方块覆盖，300ms
- `blood_splatter` — CSS 径向渐变模拟血溅，600ms
- `pixel_melt` — Canvas 绘制的垂直融化线，1000ms

**脚本部分**：
- 新增 `subliminalTexts` 多语言支持
- 新增 `ghostTextContent`, `suffocationText`, `overlapText` computed
- 新增 `corruptionBlocks` 响应式数组
- 新增 `bloodSplatterStyle` computed
- 新增 `screamCanvas`, `meltCanvas` ref + Canvas 绘制 watcher
- 新增 `language` prop

### 5. `frontend/src/components/GameTerminal.vue` — 翻译显示 + speed_shift

**修改位置 1**：Props（第 327 行）
- 新增 `translationText` prop

**修改位置 2**：聊天记录显示（第 270 行之后）
- assistant 消息下方新增翻译文本渲染（斜体浅红色 15px）

**修改位置 3**：流式打字机区域（第 295 行之后）
- 新增 `translationTypewriterDisplay` 翻译打字机流式显示

**修改位置 4**：Script 部分
- 新增 `translationTypewriterDisplay` ref
- 新增 `translationTypewriterTimer` ref
- 新增 `speedMultiplier` ref（默认 1.0）
- 新增 `speed_shift` watcher：随机选择 0.02x/0.05x/5x/10x 倍率，1.2s 后恢复
- 新增 `runTranslationTypewriter()` 函数（快速 15ms/字）
- 打字机速度应用 `speedMultiplier`
- 清理逻辑包含翻译打字机

### 6. `frontend/src/App.vue` — 新消息处理器 + title_corruption + day_loop

**修改位置 1**：GameTerminal 组件（第 51 行）
- 新增 `:translation-text` prop 传递

**修改位置 2**：GlitchOverlay 组件（第 80 行）
- 新增 `:language` prop 传递

**修改位置 3**：GLITCH_TRIGGER 处理器（第 320 行）
- 新增 12 个特效名到 `tempGlitches` 列表
- 每个特效指定正确的持续时间

**修改位置 4**：新增特效 watcher
- `title_corruption`：循环替换 `document.title`（8 次，80ms 间隔）
- `day_loop`：天数值随机闪烁（12 次，50ms 间隔）

**修改位置 5**：新增消息处理器
- `ECG_PARAMS`：同步心跳波形参数
- `API_TEST_RESULT`：存储后端 API 测试结果
- `CUSTOM_CHAR_DATA`：合并或追加自定义角色数据

**修改位置 6**：CHAT_APPEND 处理器
- 消息对象新增 `translation` 字段

### 7. `frontend/src/composables/useGameState.js` — apiTestResult ref

- 新增 `apiTestResult` ref（默认 null）
- 在 `return` 中导出

### 8. `frontend/src/assets/global.css` — evaporate 动画

- 新增 `@keyframes evaporate-flicker` 动画
- 新增 `.animate-evaporate-flicker` 类

---

## 涉及的技术决策

1. **推理模型 delta 生成**：使用意图分类器（`classify_player_intent` + `roll_delta_for_intent`）而非二次 API 调用，保证速度
2. **翻译显示**：从 spoken 文本中提取括号翻译 `（）`，前后端分离：后端提取 + 发送独立消息，前端独立渲染
3. **故障特效**：优先使用 CSS（性能好），Canvas 用于需要动态绘制的效果（scream_radial, pixel_melt）
4. **特效持续时间**：每种特效有合理的持续时间，避免过短（不感知）或过长（影响交互）

---

## 验证方法

1. 启动后端：`cd backend && python main.py --port 9876`
2. 启动前端：`cd frontend && npm run dev`
3. 在 Launcher 中配置 `deepseek-v4-pro`，点击测试连接
4. 发送对话，确认：
   - 内心独白显示（紫色文字 `<think>` 块）
   - 数值条更新（好感度/疑心度/逃脱率变化）
   - 翻译正常显示（如果选择日语+中文输入）
   - 随着疑心度升高，新的故障特效逐渐触发
