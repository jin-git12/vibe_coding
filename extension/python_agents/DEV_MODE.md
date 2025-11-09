# 🔧 开发模式说明

## 什么是开发模式？

开发模式 (DEV_MODE) 是一个专为本地开发和调试设计的特殊模式，启用后会：

1. ✅ **自动使用测试 API Key** - 无需手动配置
2. ✅ **启用 DEBUG 日志** - 显示详细的调试信息
3. ✅ **使用 qwen-turbo 模型** - 更快的响应速度

## ⚠️ 重要警告

**开发模式仅用于本地开发调试，请勿在生产环境使用！**

原因：
- 使用硬编码的测试 API Key（可能会被滥用）
- DEBUG 日志会输出敏感信息
- 性能和安全检查可能被放宽

## 🚀 如何启用开发模式

### 方法 1：在 VS Code 中按 F5 调试（自动启用）

当你在 VS Code 中按 F5 启动扩展调试时，开发模式会**自动启用**。

### 方法 2：手动设置环境变量

```bash
# Windows PowerShell
cd extension/python_agents
$env:DEV_MODE="true"
python src/agent_server.py

# Linux/Mac
cd extension/python_agents
export DEV_MODE=true
python src/agent_server.py
```

### 方法 3：通过 .env 文件（不推荐提交）

在 `extension/python_agents/.env` 中设置：

```env
DEV_MODE=true
```

**注意**：`.env` 文件已被 `.gitignore` 排除，不会被提交到 Git。

## 📝 开发模式配置

启用开发模式后的默认配置：

```python
# API Key
DASHSCOPE_API_KEY=sk-3f1a10e54780416f939f2542b6abbad9  # 测试 Key

# 模型
QWEN_MODEL=qwen-turbo  # 更快的响应

# 日志
LOG_LEVEL=DEBUG  # 详细日志
```

## 🔒 安全建议

### ✅ 开发阶段

1. 使用开发模式快速测试
2. 不要将 `.env` 文件提交到 Git
3. 定期检查是否意外提交了敏感信息

### ✅ 发布阶段

1. 确保 `DEV_MODE=false` 或未设置
2. 使用用户自己的 API Key
3. 删除所有硬编码的凭证

### ❌ 不要这样做

```typescript
// ❌ 错误：在代码中硬编码 API Key
const apiKey = "sk-xxxxx";

// ❌ 错误：提交包含真实 API Key 的 .env 文件
git add .env
git commit -m "add config"

// ❌ 错误：在生产环境启用开发模式
DEV_MODE=true in production
```

## 🧪 测试开发模式

### 1. 启动测试

```bash
cd extension/python_agents

# 启用开发模式
export DEV_MODE=true  # Linux/Mac
# 或
$env:DEV_MODE="true"  # Windows

# 运行测试
python tests/quick_test.py
```

### 2. 检查日志

你应该看到：

```
[INFO] Settings loaded from environment
[DEBUG] Development mode enabled
[DEBUG] Using built-in test API key
[DEBUG] Model: qwen-turbo
```

### 3. 验证 API Key

```python
from config import get_settings

settings = get_settings()
print(f"Dev Mode: {settings.dev_mode}")
print(f"API Key set: {bool(settings.llm_api_key)}")
print(f"Model: {settings.llm_model}")
```

## 🔄 在开发和生产之间切换

### 开发 → 生产

```bash
# 1. 移除或禁用开发模式
export DEV_MODE=false
# 或删除环境变量
unset DEV_MODE

# 2. 设置真实的 API Key
export DASHSCOPE_API_KEY=your_real_api_key

# 3. 调整日志级别
export LOG_LEVEL=INFO
```

### 生产 → 开发

```bash
# 1. 启用开发模式（会自动设置 API Key）
export DEV_MODE=true

# 2. 日志会自动调整为 DEBUG
```

## 📚 相关文件

- `src/config/settings.py` - 开发模式逻辑
- `src/services/pythonProcessService.ts` - TypeScript 自动检测
- `.env.example` - 配置模板
- `.gitignore` - 排除敏感文件

## 💡 常见问题

### Q: 为什么我的 API Key 不工作？

A: 检查：
1. 是否启用了开发模式但使用了过期的测试 Key
2. 是否设置了正确的环境变量
3. 是否有 `.env` 文件覆盖了环境变量

### Q: 如何确认开发模式已启用？

A: 查看启动日志：
```
[DEBUG] Development mode enabled
```

### Q: 开发模式会影响打包后的扩展吗？

A: 不会。打包后的扩展默认 `DEV_MODE=false`，只有在 F5 调试时才会自动启用。

---

**版本**: 1.0.0  
**最后更新**: 2025-11-09

