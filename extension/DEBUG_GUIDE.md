# 🐛 Vibe Coding 调试指南

## 📋 快速开始

### 方法 1：调试前端扩展（TypeScript）🚀

**最简单的方式，适合快速测试功能或调试前端代码**

#### 步骤：

1. **选择调试配置**：**"🚀 Run Extension"**
2. **按 F5 启动**
   - 会打开一个新的"扩展开发主机"窗口
   - Python 后端自动启动（开发模式）
   - 自动使用配置的 API Key
3. **在新窗口中测试功能**
   - 点击左侧活动栏的 🤖 图标打开聊天
   - 或按 `Ctrl+Shift+P` 输入 "Vibe Coding: Open Chat"
   - 发送消息测试 Agent 功能
4. **可以在 TypeScript 代码中设置断点**
   - 例如在 `extension/src/services/pythonProcessService.ts` 中

---

### 方法 2：调试 Python 后端（独立运行）🐛

**如果需要调试 Python 后端代码，使用独立的 Python 调试配置**

#### 步骤：

1. **选择调试配置**：**"🐛 Debug Python Backend"**
2. **按 F5 启动**
   - 直接启动 Python 后端（不启动扩展）
   - 在终端中运行
3. **在 Python 代码中设置断点**
   - 打开 `extension/python_agents/src/agent_server.py`
   - 在 `def chat(...)` 方法（约第 135 行）设置断点
   - 断点应该显示为 **红色实心圆** ✅
4. **手动触发代码**
   - 在终端中输入 JSON-RPC 请求来触发断点
   - 或使用测试脚本：`extension/python_agents/tests/quick_test.py`

#### 💡 适用场景：
- 调试 Python Agent 逻辑
- 调试 RPC 通信
- 测试 LLM 集成
- 开发新的工具或中间件

---

### 方法 3：运行 Python 测试 🧪

**使用测试脚本快速验证功能**

#### 步骤：

1. **选择调试配置**：**"🧪 Test Python Backend"**
2. **按 F5 启动**
3. **自动运行测试脚本**
   - 会执行 `extension/python_agents/tests/quick_test.py`
   - 可以在测试代码中设置断点
   - 查看测试输出

---

### 方法 4：调试当前 Python 文件 🔍

**快速调试任意 Python 文件**

#### 步骤：

1. **打开任意 Python 文件**
2. **选择调试配置**：**"🔍 Debug Current Python File"**
3. **按 F5 运行当前文件**
4. **可以设置断点调试**

---

## 🔍 调试界面详解

### 界面布局

```
┌─────────────────────────────────────────┐
│  New Chat [x]  Chat 2 [x]    [+]       │  ← 会话标签
├─────────────────────────────────────────┤
│                                         │
│  👤 User: Hello                        │
│                                         │
│  🤖 Assistant: Hi! How can I help?    │  ← 聊天消息
│                                         │
│  👤 User: Generate a Python function  │
│                                         │
│  🤖 Assistant:                         │
│     ```python                          │
│     def example():                     │
│         pass                           │
│     ```                                │
│     [Copy] [Insert]                    │  ← 代码工具栏
│                                         │
├─────────────────────────────────────────┤
│  Plan, @ for context, / for commands   │  ← 输入框
│                                         │
│  [Sonnet 4.5 ▼] ○ @ 📷 [↑]           │  ← 工具栏
└─────────────────────────────────────────┘
```

### 输入区域功能

| 元素 | 功能 | 说明 |
|------|------|------|
| **输入框** | 输入消息 | 支持多行文本 |
| **↑ 按钮** | 发送消息 | 或按 Enter |
| **@ 按钮** | 添加上下文 | 引用代码文件 |
| **📷 按钮** | 添加图片 | 上传截图 |
| **○ 按钮** | 上下文使用量 | Token 计数 |
| **Sonnet 4.5** | 模型选择 | 切换 LLM 模型 |

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Enter` | 发送消息 |
| `Shift + Enter` | 换行 |
| `Ctrl + Enter` | 强制发送 |
| `/` | 命令菜单 |
| `@` | 上下文菜单 |

---

## 🧪 调试流程

### 1. 启动调试

```bash
# 方式 A：VS Code 中按 F5（推荐）

# 方式 B：命令行编译后按 F5
cd E:\llm_project\vibe_coding\extension
pnpm run compile
# 然后按 F5
```

### 2. 观察启动日志

**在原 VS Code 窗口的"调试控制台"中**：

```
[vibe-coding] Extension activated
[vibe-coding] Python process starting...
[vibe-coding] Working directory: E:\llm_project\vibe_coding\extension\python_agents
[vibe-coding] Command: uv run python src/agent_server.py
[vibe-coding] Python process started (PID: xxxxx)
[vibe-coding] DEV_MODE: true                    ← ✅ 开发模式已启用
[vibe-coding] Waiting for server ready...
[vibe-coding] Server ready notification received ← ✅ 后端就绪
[vibe-coding] Agent server is ready!
```

**Python 后端日志（stderr）**：

```
[INFO] Settings loaded from environment
🔧 Development mode enabled - using test configuration  ← ✅ 开发模式
[INFO] ✓ Code generator agent created
[INFO] ✓ Chat agent created
[INFO] ✓ Code explainer agent created
[INFO] ✓ Refactoring agent created
[INFO] Agent server ready
```

### 3. 在新窗口中测试

**新窗口是"扩展开发主机"**，模拟用户环境：

1. **打开 AI Chat**
   - 点击左侧的 🤖 图标
   - 应该看到侧边栏打开

2. **测试输入**
   ```
   输入: "Hello, can you hear me?"
   预期: Agent 返回问候消息
   ```

3. **测试代码生成**
   ```
   输入: "Generate a Python function to calculate factorial"
   预期: Agent 返回带代码块的响应
   ```

4. **测试上下文**
   ```
   输入: "@" 然后选择文件
   预期: 显示文件选择菜单
   ```

### 4. 调试消息流

#### 前端 → 后端流程

```typescript
// 1. 用户在输入框输入消息
messageInput.value = "Hello"

// 2. 点击发送或按 Enter
sendMessage()

// 3. chat.js 发送消息到 TypeScript
vscode.postMessage({
    type: 'sendMessage',
    message: "Hello",
    conversationId: "xxx"
})

// 4. chatViewProvider.ts 处理消息
handleMessage(data)

// 5. 调用 agentBridge
agentBridge.chat({
    message: "Hello",
    conversationId: "xxx",
    context: {...},
    stream: true
})

// 6. agentBridge 发送 JSON-RPC 到 Python
{
    "jsonrpc": "2.0",
    "method": "chat",
    "params": {
        "message": "Hello",
        "conversation_id": "xxx"
    },
    "id": 1
}

// 7. Python 返回响应
{
    "jsonrpc": "2.0",
    "result": {
        "full_response": "Hi! How can I help?",
        "suggestions": []
    },
    "id": 1
}

// 8. 显示在 WebView
addMessage('assistant', "Hi! How can I help?")
```

---

## 🔧 调试技巧

### 1. 查看详细日志

**启用 DEBUG 日志**（自动在开发模式）：

在原 VS Code 窗口的调试控制台查看：
- TypeScript 日志（stdout）
- Python 日志（stderr）

### 2. 断点调试

#### TypeScript 断点

1. 在 `chatViewProvider.ts` 的 `sendMessage` 方法设置断点
2. 按 F5 启动调试
3. 在新窗口输入消息
4. 断点会触发，可以查看变量

**关键位置**：
```typescript
// chatViewProvider.ts
async sendMessage(message: string) {
    // 设置断点这里 ← 🔴
    if (!this.currentConversation) {
        this.newConversation();
    }
    // ...
}

// agentBridge.ts
async chat(params: ChatParams) {
    // 设置断点这里 ← 🔴
    const request = {
        jsonrpc: '2.0',
        method: 'chat',
        params: { /* ... */ }
    };
    // ...
}
```

#### Python 断点

1. 在 VS Code 中打开 `extension/python_agents/src/agent_server.py`
2. 在 `chat` 方法设置断点
3. 在终端手动启动 Python 调试：

```bash
cd extension/python_agents
$env:DEV_MODE="true"

# 使用 debugpy 启动
.venv\Scripts\python.exe -m debugpy --listen 5678 src\agent_server.py
```

4. 在 VS Code 中附加到进程（F5 → "Python: Attach"）

**关键位置**：
```python
# agent_server.py
def chat(self, params: dict) -> dict:
    # 设置断点这里 ← 🔴
    message = params.get("message", "")
    conversation_id = params.get("conversation_id", "default")
    # ...
```

### 3. 使用 Chrome DevTools 调试 WebView

1. 在"扩展开发主机"窗口中
2. 按 `Ctrl+Shift+P`
3. 输入 "Developer: Open Webview Developer Tools"
4. 选择 "Vibe Coding Chat"
5. 打开 DevTools，可以查看：
   - Console 日志
   - Network 请求
   - DOM 结构
   - JavaScript 断点

**关键 JavaScript 位置**：
```javascript
// chat.js
function sendMessage() {
    // 在 DevTools 中设置断点 ← 🔴
    const message = messageInput.value.trim();
    vscode.postMessage({
        type: 'sendMessage',
        message: message
    });
}
```

### 4. 监控 JSON-RPC 通信

**添加日志**：

```typescript
// agentBridge.ts
private async sendRequest(request: any): Promise<any> {
    console.log('[RPC Request]', JSON.stringify(request, null, 2));  // ← 添加
    this.pythonService.sendMessage(request);
    
    const response = await this.waitForResponse(request.id);
    console.log('[RPC Response]', JSON.stringify(response, null, 2)); // ← 添加
    return response;
}
```

```python
# agent_server.py
def handle_request(self, request: dict) -> dict:
    logger.debug(f"[RPC Request] {json.dumps(request, indent=2)}")  # ← 添加
    response = self._process_request(request)
    logger.debug(f"[RPC Response] {json.dumps(response, indent=2)}") # ← 添加
    return response
```

---

## 🐛 常见问题

### Q1: 输入框没有出现？

**检查**：
1. 是否看到侧边栏图标？
   - 查看左侧活动栏是否有 🤖 图标
2. 点击图标后是否打开侧边栏？
   - 应该看到 "AI CHAT" 标题

**解决**：
```typescript
// 检查 package.json 中的配置
"views": {
  "vibe-coding": [
    {
      "type": "webview",
      "id": "vibe-coding-chat",
      "name": "AI Chat"
    }
  ]
}
```

### Q2: 发送消息没有响应？

**检查步骤**：

1. **Python 进程是否启动？**
   ```
   在调试控制台查找: "Python process started"
   如果没有，查看错误消息
   ```

2. **是否收到 server.ready？**
   ```
   查找: "Server ready notification received"
   ```

3. **开发模式是否启用？**
   ```
   查找: "DEV_MODE: true"
   如果是 false，API Key 可能未设置
   ```

4. **LLM 是否连接？**
   ```
   Python 日志查找: "✓ Chat agent created"
   ```

5. **查看错误日志**
   ```
   - 调试控制台的红色错误
   - Python stderr 的 ERROR 日志
   ```

### Q3: 消息显示但没有 AI 响应？

**调试**：

1. 打开 WebView DevTools
2. 查看 Console 是否有错误
3. 检查 `window.addEventListener('message')` 是否收到响应

**添加日志**：
```javascript
// chat.js
window.addEventListener('message', event => {
    console.log('[WebView] Received:', event.data);  // ← 添加
    const message = event.data;
    // ...
});
```

### Q4: 代码块不显示？

**检查 Markdown 渲染**：

在 WebView DevTools Console 中测试：
```javascript
// 测试渲染
const testMarkdown = "```python\ndef hello():\n    pass\n```";
const rendered = renderMarkdown(testMarkdown);
console.log(rendered);
```

---

## 📊 调试检查清单

### 启动前

- [ ] Python 虚拟环境已创建 (`.venv`)
- [ ] 依赖已安装 (`uv sync`)
- [ ] TypeScript 已编译 (`pnpm run compile`)
- [ ] 没有编译错误

### 启动时

- [ ] 扩展激活成功
- [ ] Python 进程启动成功
- [ ] 收到 `server.ready` 通知
- [ ] 开发模式已启用 (`DEV_MODE: true`)
- [ ] 所有 Agent 创建成功

### 运行时

- [ ] 侧边栏图标显示
- [ ] AI Chat 面板打开
- [ ] 输入框可见并可用
- [ ] 发送按钮工作
- [ ] 消息显示在聊天区域
- [ ] Agent 响应正常显示

---

## 🎯 测试场景

### 场景 1：简单问候

```
输入: "Hello!"
预期响应: "Hello! How can I assist you today?"
```

### 场景 2：代码生成

```
输入: "Generate a Python function to calculate factorial"
预期响应: 包含 Python 代码块的响应
```

### 场景 3：代码解释

```
1. 选择一段代码
2. 输入: "Explain this code"
3. 预期: Agent 解释选中的代码
```

### 场景 4：多轮对话

```
1. 输入: "What's 2+2?"
2. 等待响应
3. 输入: "What about 3+3?"
4. 预期: Agent 记得上下文
```

---

## 📝 调试日志示例

### 成功的调试会话

```
[调试控制台]
[vibe-coding] Extension activated
[vibe-coding] Setup UI completed
[vibe-coding] Python process starting...
[vibe-coding] Python process started (PID: 12345)
[vibe-coding] DEV_MODE: true
[vibe-coding] Server ready notification received
[vibe-coding] Agent server is ready!

[用户输入] "Hello"

[vibe-coding] Sending chat request...
[RPC Request] {
  "jsonrpc": "2.0",
  "method": "chat",
  "params": {
    "message": "Hello",
    "conversation_id": "1699..."
  },
  "id": 1
}

[Python stderr]
[INFO] Processing chat request
[DEBUG] Message: Hello
[DEBUG] Calling chat agent...
[DEBUG] Agent response: Hello! How can I assist you today?

[vibe-coding] Chat response received
[RPC Response] {
  "jsonrpc": "2.0",
  "result": {
    "full_response": "Hello! How can I assist you today?",
    "suggestions": []
  },
  "id": 1
}

[WebView] Message displayed
```

---

## 🛠️ 高级调试

### 修改开发模式行为

编辑 `extension/python_agents/src/config/settings.py`：

```python
# 临时修改调试行为
dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"

# 添加更多调试信息
if dev_mode:
    logger.setLevel(logging.DEBUG)
    logger.info("=" * 60)
    logger.info("DEVELOPMENT MODE")
    logger.info(f"API Key: {dev_api_key[:20]}...")
    logger.info(f"Model: qwen-turbo")
    logger.info("=" * 60)
```

### 模拟慢速响应

测试加载状态：

```python
# agent_server.py
def chat(self, params: dict) -> dict:
    import time
    time.sleep(2)  # ← 添加延迟
    # ... 正常处理
```

### 测试错误处理

```python
# agent_server.py
def chat(self, params: dict) -> dict:
    # 模拟错误
    raise Exception("Test error")  # ← 测试错误显示
```

---

## 📚 相关文档

- [TEST_REPORT.md](python_agents/TEST_REPORT.md) - 测试报告
- [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md) - 集成状态
- [DEV_MODE.md](python_agents/DEV_MODE.md) - 开发模式说明

---

**准备好了吗？按 F5 开始调试！** 🚀



