# 🧪 Python Agents 测试

## 测试套件

### ✅ 实现测试

**`test_deepagents_implementation.py`** - DeepAgents 实现验证测试

测试内容：
- ✅ 模块导入
- ✅ DeepAgents 可用性
- ✅ 依赖配置
- ✅ 自定义工具创建
- ✅ Agent 创建和调用

运行：
```bash
cd extension/python_agents
.venv\Scripts\python.exe tests\test_deepagents_implementation.py
```

预期输出：
```
============================================================
Testing New DeepAgents Implementation
============================================================
[PASS] Imports
[PASS] DeepAgents Available
[PASS] PyProject Dependencies
[PASS] Custom Tools
[PASS] Agent Creation

Total: 5/5 tests passed

[SUCCESS] All tests passed!
```

### 🎮 交互式测试

**`quick_test.py`** - 交互式功能测试

功能：
1. **基础聊天测试** - 测试聊天 Agent
2. **代码生成测试** - 测试代码生成 Agent
3. **交互模式** - 与 Agent 实时对话

运行：
```bash
cd extension/python_agents
.venv\Scripts\python.exe tests\quick_test.py
```

选项：
```
1. 基础聊天测试
2. 代码生成测试
3. 交互模式
4. 运行所有测试
q. 退出
```

## 环境要求

### 必需

- Python 3.11+
- uv 包管理器
- 虚拟环境已激活

### 可选（用于真实 Agent 测试）

在 `extension/python_agents/.env` 中配置：

```env
DASHSCOPE_API_KEY=your_api_key_here
QWEN_MODEL=qwen-turbo
```

## 运行所有测试

```bash
# 激活虚拟环境
cd extension/python_agents
.venv\Scripts\Activate.ps1

# 运行实现测试
python tests\test_deepagents_implementation.py

# 运行交互测试（需要 API key）
python tests\quick_test.py
```

## 测试结构

```
tests/
├── README.md                          # 本文件（测试说明）
├── test_deepagents_implementation.py  # 实现验证测试
└── quick_test.py                      # 交互式测试
```

## 添加新测试

创建新测试文件时：
1. 放在 `tests/` 目录下
2. 文件名以 `test_` 开头
3. 包含清晰的文档字符串
4. 更新本 README

## 测试最佳实践

- ✅ 每个测试应该独立运行
- ✅ 提供清晰的成功/失败信息
- ✅ 避免依赖外部服务（除非明确标注）
- ✅ 使用 try-except 处理异常
- ✅ 输出易读的测试报告

