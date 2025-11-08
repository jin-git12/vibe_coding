# Examples 调试指南

本指南介绍如何调试 `examples` 文件夹中的文件。

## 方法 1: 使用 VS Code 调试器（推荐）

### 步骤：

1. **打开要调试的文件**（如 `research_agent.py` 或 `run_research_agent.py`）

2. **设置断点**：
   - 在代码行号左侧点击，会出现红点
   - 或者按 `F9` 切换断点

3. **选择调试配置**：
   - 按 `F5` 或点击调试按钮
   - 在调试配置下拉菜单中选择：
     - `Python: Current File (Examples)` - 调试当前打开的文件
     - `Python: Run Research Agent` - 调试 run_research_agent.py
     - `Python: Test Research Agent` - 调试 test_research_agent.py

4. **开始调试**：
   - 程序会在断点处暂停
   - 可以查看变量值、调用栈等
   - 使用调试工具栏：
     - `F10` - 单步跳过（Step Over）
     - `F11` - 单步进入（Step Into）
     - `Shift+F11` - 单步跳出（Step Out）
     - `F5` - 继续（Continue）

### 调试配置说明：

- **Python: Current File (Examples)** - 调试当前打开的文件，自动设置工作目录
- **Python: Run Research Agent** - 专门用于调试 `run_research_agent.py`
- **Python: Test Research Agent** - 专门用于调试 `test_research_agent.py`
- **Python: Debug with uv run** - 使用 uv 环境运行

## 方法 2: 使用 breakpoint() 函数

在代码中直接添加 `breakpoint()` 函数：

```python
def internet_search(query: str, ...):
    """Run a web search"""
    breakpoint()  # 程序会在这里暂停，进入调试器
    search_docs = tavily_client.search(...)
    return search_docs
```

然后运行：
```bash
uv run python examples/run_research_agent.py
```

程序会在 `breakpoint()` 处暂停，进入 Python 调试器（pdb）。

### pdb 常用命令：
- `n` (next) - 执行下一行
- `s` (step) - 进入函数内部
- `c` (continue) - 继续执行
- `l` (list) - 显示当前代码
- `p <variable>` - 打印变量值
- `pp <variable>` - 美化打印变量
- `q` (quit) - 退出调试器

## 方法 3: 使用命令行调试

### 使用 pdb 模块：

```bash
# 方式 1: 在代码中导入 pdb
uv run python -m pdb examples/run_research_agent.py

# 方式 2: 使用 python -m pdb
uv run python -m pdb examples/research_agent.py
```

### 使用 ipdb（更友好的调试器）：

首先安装：
```bash
uv add --dev ipdb
```

然后使用：
```python
import ipdb; ipdb.set_trace()  # 在代码中插入
```

## 方法 4: 打印调试

在代码中添加打印语句：

```python
def internet_search(query: str, ...):
    """Run a web search"""
    print(f"[DEBUG] Query: {query}")  # 打印调试信息
    print(f"[DEBUG] Max results: {max_results}")
    search_docs = tavily_client.search(...)
    print(f"[DEBUG] Results: {search_docs}")  # 打印结果
    return search_docs
```

## 调试技巧

### 1. 查看变量值
在 VS Code 调试器中：
- 左侧"变量"面板显示所有局部和全局变量
- 鼠标悬停在变量上查看值
- 在"调试控制台"中输入变量名查看

### 2. 监视表达式
在 VS Code 中：
- 添加"监视"表达式，实时查看表达式值
- 例如：`len(search_docs)`、`type(agent)`

### 3. 条件断点
- 右键点击断点，设置条件
- 例如：只在 `query == "test"` 时暂停

### 4. 日志点（Logpoint）
- 右键点击行号，选择"添加日志点"
- 不暂停执行，只输出日志
- 例如：`Query: {query}, Results: {len(search_docs)}`

## 常见问题

### 问题 1: 导入错误
如果遇到 `ModuleNotFoundError`，确保：
- `.vscode/launch.json` 中 `PYTHONPATH` 包含 `examples` 目录
- `cwd` 设置为正确的目录

### 问题 2: 环境变量未加载
确保 `.env` 文件在项目根目录，且包含：
```
TAVILY_API_KEY=your_key
DASHSCOPE_API_KEY=your_key
```

### 问题 3: 虚拟环境未激活
确保 VS Code 使用正确的 Python 解释器：
- `Ctrl+Shift+P` → `Python: Select Interpreter`
- 选择 `.venv/Scripts/python.exe`

## 示例：调试 research_agent.py

1. 打开 `examples/research_agent.py`
2. 在第 24 行（`search_docs = tavily_client.search(...)`）设置断点
3. 按 `F5`，选择 `Python: Current File (Examples)`
4. 程序会在断点处暂停
5. 可以查看 `query`、`max_results` 等变量值
6. 使用 `F10` 单步执行，观察 `search_docs` 的值

## 示例：调试 run_research_agent.py

1. 打开 `examples/run_research_agent.py`
2. 在第 40 行（`result = agent.invoke(...)`）设置断点
3. 按 `F5`，选择 `Python: Run Research Agent`
4. 程序运行后，输入一个问题
5. 程序会在断点处暂停
6. 可以查看 `user_input`、`result` 等变量

