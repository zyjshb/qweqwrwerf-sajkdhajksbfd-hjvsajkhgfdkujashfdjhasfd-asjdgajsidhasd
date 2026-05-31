# 纱希 (Saki) — 病娇心理恐怖文字冒险 RPG

> "亲爱的……你终于醒了。纱希一直在看着你哦。"

**纱希** 是一款 AI 驱动的心理恐怖病娇（Yandere）文字冒险游戏。你被困在地牢中，与粉发赤瞳的少女**纱希**展开对话——每一句话都会影响她对你的**好感**、**疑心**和**逃脱率**。温柔待她，她会融化；试图逃跑，她会让你永远留下。

采用 **Vue 3 前端 + FastAPI WebSocket 后端**，接入 LLM API 实时生成对话，支持中/英/日三语，带 30+ 种心理恐怖视觉特效。

---

## 快速开始（5 分钟）

### 前提

- **Python 3.10+**
- **Node.js 18+**（[下载](https://nodejs.org)）
- **DeepSeek API Key**（[注册获取](https://platform.deepseek.com)，新用户有免费额度）

### 1. 克隆项目

```bash
git clone https://github.com/zyjshb/qweqwrwerf-sajkdhajksbfd-hjvsajkhgfdkujashfdjhasfd-asjdgajsidhasd.git
cd qweqwrwerf-sajkdhajksbfd-hjvsajkhgfdkujashfdjhasfd-asjdgajsidhasd
```

### 2. 安装后端依赖

```bash
cd backend
pip install fastapi uvicorn websockets requests Pillow
```

### 3. 安装前端依赖

```bash
cd ../frontend
npm install
```

### 4. 配置 API Key

在项目根目录的 `yandere_config.json` 中填入你的 DeepSeek API Key，或在启动后通过游戏界面配置。

> 支持任何兼容 OpenAI API 格式的服务（GPT-4o、Mistral、Groq、本地 Ollama 等），修改 `api_base` 和 `model_name` 即可。

### 5. 启动

**终端 1 — 后端：**
```bash
cd backend
python main.py
```

**终端 2 — 前端：**
```bash
cd frontend
npm run dev
```

### 6. 打开浏览器

访问 **http://localhost:5173** 进入游戏。

---

## 启动流程速查

```bash
# 终端1: 后端
cd backend && pip install fastapi uvicorn websockets requests Pillow && python main.py

# 终端2: 前端
cd frontend && npm install && npm run dev

# 浏览器打开 http://localhost:5173
```

---

## 怎么玩

1. 启动后进入**启动器**界面，选择纱希的语言（中文 / English / 日本語），填入 API Key
2. 点击**进入游戏**，纱希会说出第一句问候
3. 在底部输入框打字，按 **Enter** 发送
4. 纱希用你选择的语言回复，如果你的输入语言不同，**下方会自动显示翻译**

### 数值系统

| 数值 | 范围 | 说明 |
|------|------|------|
| 好感度 | 0-100 | 纱希对你的信任与依恋 |
| 疑心度 | 0-100 | 纱希对你的怀疑与警觉 |
| 逃脱率 | 0-100% | 你逃跑的准备程度 |

疑心度升高会触发不同级别的**心理恐怖特效**（CRT 扫描线、血溅、屏幕撕裂、假报错弹窗等）。

### 结局

- **好感 ≤ -25** 或 **疑心 ≥ 96** → BAD END
- AI 也可以在对话高潮自主宣告结局（GOOD / BAD / NEUTRAL）

---

## 可选：GPT-SoVITS 语音合成

纱希的每句话都可以用病娇声线朗读。

```bash
# 1. 克隆并启动 GPT-SoVITS（另开终端）
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
pip install -r requirements.txt
python api_v2.py
# 默认监听 http://127.0.0.1:9880

# 2. 在游戏设置面板中填入 TTS Base URL 和模型路径即可
```

参考音频和预训练权重见 `models/` 目录（花火中文 / 米塔日文）。

> TTS 是可选的，不配置也能正常玩游戏。没开 TTS 时 8 秒后输入自动解锁。

---

## 兼容的 API 服务

| 服务 | api_base | model_name 示例 |
|------|----------|----------------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` / `deepseek-v4-pro` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` / `gpt-4o-mini` |
| Mistral | `https://api.mistral.ai/v1` | `mistral-large-latest` |
| 本地 Ollama | `http://localhost:11434/v1` | `llama3` / `qwen` |

> 建议使用非推理模型（如 `deepseek-chat`、`gpt-4o`），翻译功能兼容性更好。

---

## 操作

| 操作 | 方式 |
|------|------|
| 发送消息 | Enter |
| 打开设置 | 点击顶部 `[ 展开配置通道 ]` |
| 存档 / 读档 | 顶部 `[ 记忆存取 ]` 或按 Escape |
| 重新开始 | 结局画面点击按钮 |

---

## 项目结构

```
├── backend/                     # FastAPI WebSocket 后端
│   ├── main.py                  # 入口，启动 Uvicorn
│   ├── websocket/
│   │   ├── game_ws.py           # WebSocket 会话处理、翻译管线
│   │   └── protocol.py          # 消息协议定义
│   ├── core/
│   │   ├── game_state.py        # 游戏状态机、System Prompt 构建
│   │   └── config.py            # JSON 配置读写
│   ├── ai/
│   │   ├── api_client.py        # LLM API 后台请求
│   │   ├── prompt_builder.py    # System Prompt 组装
│   │   └── translator.py        # 响应解析
│   ├── audio/
│   │   └── tts_client.py        # GPT-SoVITS 语音合成
│   └── resources/               # 常量、翻译映射、离线回复库
├── frontend/                    # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── App.vue              # 主应用（WebSocket、TTS、心跳音效）
│   │   ├── components/
│   │   │   ├── GameTerminal.vue # 游戏主界面（打字机、聊天区、ECG）
│   │   │   ├── Launcher.vue     # 启动器（语言选择、API 配置）
│   │   │   ├── GlitchOverlay.vue    # 21 种故障特效叠加层
│   │   │   └── GlitchTextOverlay.vue # 病娇文字散布特效
│   │   └── composables/         # useWebSocket / useGameState
│   └── index.html
├── models/                      # TTS 预训练模型
│   ├── hua/                     # 花火（中文）
│   └── mi/                      # 米塔（日文）
└── yandere_config.json          # 配置文件
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 (Composition API) + Vite + Tailwind CSS |
| 后端 | FastAPI + Uvicorn + WebSocket |
| AI | DeepSeek / OpenAI 兼容 API |
| 音频 | GPT-SoVITS + Web Audio API（前端心跳合成） |
| 视觉 | CSS 动画 + Canvas（ECG 波形、粒子） |

---

## License

MIT
