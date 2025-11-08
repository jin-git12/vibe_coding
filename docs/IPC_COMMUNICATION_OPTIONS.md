# VS Code 扩展与 Python 子进程通信方式对比

## 背景

在方案 1 中，TypeScript（VS Code 扩展）需要与 Python 子进程通信。通信方式的选择直接影响：
- 🚀 性能（延迟、吞吐量）
- 🛠️ 开发复杂度
- 🔄 可靠性（错误处理、重连）
- 📦 打包和部署

---

## 方案对比

### 方案 A: JSON-RPC over stdin/stdout 🌟🌟🌟🌟🌟

**原理**：使用标准输入输出流，每行一个 JSON-RPC 请求/响应

#### 实现示例

**TypeScript 端**：
```typescript
// extension/src/services/pythonService.ts
import { spawn, ChildProcess } from 'child_process';
import * as readline from 'readline';

export class PythonAgentService {
    private process: ChildProcess;
    private requestId = 0;
    private pendingRequests = new Map<number, {
        resolve: (value: any) => void;
        reject: (error: any) => void;
    }>();
    
    async start() {
        this.process = spawn('uv', ['run', 'python', 'agent_server.py'], {
            cwd: this.pythonPath,
            stdio: ['pipe', 'pipe', 'pipe']
        });
        
        // 逐行读取输出
        const rl = readline.createInterface({
            input: this.process.stdout!,
            crlfDelay: Infinity
        });
        
        rl.on('line', (line) => {
            const response = JSON.parse(line);
            this.handleResponse(response);
        });
        
        this.process.stderr!.on('data', (data) => {
            console.error('Python stderr:', data.toString());
        });
    }
    
    async request(method: string, params: any): Promise<any> {
        const id = this.requestId++;
        const request = {
            jsonrpc: '2.0',
            method,
            params,
            id
        };
        
        return new Promise((resolve, reject) => {
            this.pendingRequests.set(id, { resolve, reject });
            
            // 发送请求（一行 JSON）
            this.process.stdin!.write(JSON.stringify(request) + '\n');
            
            // 超时处理
            setTimeout(() => {
                if (this.pendingRequests.has(id)) {
                    this.pendingRequests.delete(id);
                    reject(new Error('Request timeout'));
                }
            }, 30000);
        });
    }
    
    private handleResponse(response: any) {
        const { id, result, error } = response;
        const pending = this.pendingRequests.get(id);
        
        if (pending) {
            this.pendingRequests.delete(id);
            if (error) {
                pending.reject(new Error(error.message));
            } else {
                pending.resolve(result);
            }
        }
    }
}
```

**Python 端**：
```python
# python_agents/src/agent_server.py
import sys
import json
import logging
from typing import Any, Dict

class JSONRPCServer:
    def __init__(self):
        self.methods = {}
        self.setup_logging()
    
    def setup_logging(self):
        # 日志输出到 stderr，不干扰 stdout
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
        self.logger = logging.getLogger(__name__)
    
    def register(self, method_name: str, func):
        """注册 RPC 方法"""
        self.methods[method_name] = func
    
    def run(self):
        """主循环：读取 stdin，处理请求，输出到 stdout"""
        self.logger.info("JSON-RPC Server started")
        
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self.handle_request(request)
                # 输出响应（一行 JSON）
                print(json.dumps(response), flush=True)
            except Exception as e:
                self.logger.error(f"Error processing request: {e}")
                error_response = {
                    'jsonrpc': '2.0',
                    'error': {
                        'code': -32603,
                        'message': str(e)
                    },
                    'id': request.get('id') if 'request' in locals() else None
                }
                print(json.dumps(error_response), flush=True)
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个请求"""
        method_name = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')
        
        if method_name not in self.methods:
            return {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32601,
                    'message': f'Method not found: {method_name}'
                },
                'id': request_id
            }
        
        try:
            method = self.methods[method_name]
            result = method(**params)
            return {
                'jsonrpc': '2.0',
                'result': result,
                'id': request_id
            }
        except Exception as e:
            self.logger.exception(f"Error in method {method_name}")
            return {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32000,
                    'message': str(e)
                },
                'id': request_id
            }

# 使用示例
server = JSONRPCServer()

def generate_code(prompt: str, context: list) -> dict:
    # 使用 deepagents
    agent = get_code_agent()
    result = agent.run(prompt, context)
    return {'code': result}

server.register('generate_code', generate_code)
server.run()
```

#### 优点 ✅

1. **简单可靠**
   - 标准输入输出，跨平台兼容性好
   - 不需要端口，无端口占用问题
   - 不需要网络栈，减少依赖

2. **性能优秀**
   - 进程间通信，几乎零延迟
   - 无序列化开销（JSON 足够快）
   - 适合高频请求

3. **易于调试**
   - 可以直接看到请求/响应内容
   - 可以手动测试 Python 端（stdin 输入 JSON）
   - stderr 独立输出日志

4. **标准协议**
   - JSON-RPC 2.0 是标准协议
   - 有现成的库可用
   - 易于扩展和维护

5. **VS Code 友好**
   - Language Server Protocol 就基于 JSON-RPC
   - VS Code 生态中很常见
   - 有成熟的实践案例

#### 缺点 ❌

1. **双向通信复杂**
   - Python 主动推送通知需要特殊处理
   - 没有内置的流式响应支持

2. **调试需要技巧**
   - 必须将日志输出到 stderr
   - stdout 只能用于 JSON 响应

3. **缓冲问题**
   - 需要注意 flush，确保及时输出
   - 大数据传输可能有问题

#### 推荐指数：⭐⭐⭐⭐⭐

**最推荐！** 简单、可靠、高性能，VS Code 生态的标准做法。

---

### 方案 B: 简单 JSON over stdin/stdout 🌟🌟🌟🌟

**原理**：不用 JSON-RPC 协议，直接每行一个 JSON 对象

#### 实现示例

**TypeScript 端**：
```typescript
async request(method: string, data: any): Promise<any> {
    const message = { method, data, id: this.requestId++ };
    this.process.stdin!.write(JSON.stringify(message) + '\n');
    
    // 等待响应...
}
```

**Python 端**：
```python
for line in sys.stdin:
    message = json.loads(line)
    method = message['method']
    data = message['data']
    
    # 处理请求
    result = handle_method(method, data)
    
    # 返回响应
    response = {'id': message['id'], 'result': result}
    print(json.dumps(response), flush=True)
```

#### 优点 ✅

- ✅ 更简单，不需要遵循 JSON-RPC 规范
- ✅ 灵活，可以自定义协议
- ✅ 性能与 JSON-RPC 相同

#### 缺点 ❌

- ❌ 需要自己实现错误处理
- ❌ 不标准，难以与其他工具集成
- ❌ 缺少现成的库支持

#### 推荐指数：⭐⭐⭐⭐

适合快速原型，但长期维护不如 JSON-RPC。

---

### 方案 C: gRPC 🌟🌟🌟

**原理**：使用 gRPC 协议，基于 HTTP/2

#### 实现示例

**定义 Protocol Buffers**：
```protobuf
// agent.proto
syntax = "proto3";

service AgentService {
  rpc GenerateCode (GenerateRequest) returns (GenerateResponse);
  rpc StreamChat (stream ChatMessage) returns (stream ChatMessage);
}

message GenerateRequest {
  string prompt = 1;
  repeated string context = 2;
}

message GenerateResponse {
  string code = 1;
}
```

**TypeScript 端**：
```typescript
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';

const packageDef = protoLoader.loadSync('agent.proto');
const proto = grpc.loadPackageDefinition(packageDef);

const client = new proto.AgentService(
    'localhost:50051',
    grpc.credentials.createInsecure()
);

client.GenerateCode({ prompt, context }, (err, response) => {
    if (err) {
        console.error(err);
    } else {
        console.log(response.code);
    }
});
```

**Python 端**：
```python
import grpc
from concurrent import futures
import agent_pb2
import agent_pb2_grpc

class AgentService(agent_pb2_grpc.AgentServiceServicer):
    def GenerateCode(self, request, context):
        code = generate_code(request.prompt, request.context)
        return agent_pb2.GenerateResponse(code=code)

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
agent_pb2_grpc.add_AgentServiceServicer_to_server(AgentService(), server)
server.add_insecure_port('[::]:50051')
server.start()
```

#### 优点 ✅

- ✅ **高性能**：二进制协议，比 JSON 快
- ✅ **强类型**：Protocol Buffers 提供类型安全
- ✅ **流式支持**：原生支持双向流
- ✅ **工具链完善**：有代码生成、文档等

#### 缺点 ❌

- ❌ **复杂度高**：需要定义 .proto 文件，生成代码
- ❌ **调试困难**：二进制协议，不如 JSON 直观
- ❌ **依赖重**：需要 gRPC 库，增加打包大小
- ❌ **端口占用**：仍需要监听端口
- ❌ **过度设计**：对于本地进程通信来说太重了

#### 推荐指数：⭐⭐⭐

适合分布式系统，但对本地进程通信来说过于复杂。

---

### 方案 D: HTTP/WebSocket (localhost) 🌟🌟

**原理**：Python 启动一个 HTTP 服务器，TypeScript 通过 HTTP 请求通信

#### 实现示例

**Python 端**：
```python
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.post("/generate")
async def generate_code(request: GenerateRequest):
    code = generate_code(request.prompt)
    return {"code": code}

# 在随机端口启动
uvicorn.run(app, host="127.0.0.1", port=0)
```

**TypeScript 端**：
```typescript
const response = await fetch('http://localhost:8765/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
});
const result = await response.json();
```

#### 优点 ✅

- ✅ 熟悉的 HTTP API
- ✅ 易于调试（浏览器、Postman）
- ✅ WebSocket 支持双向通信

#### 缺点 ❌

- ❌ **端口占用问题**
- ❌ **启动复杂**：需要找空闲端口，通知扩展
- ❌ **性能较差**：HTTP 开销大
- ❌ **依赖重**：需要 web 框架

#### 推荐指数：⭐⭐

开发简单但不适合本地进程通信。

---

### 方案 E: Named Pipes / Unix Sockets 🌟🌟🌟

**原理**：使用操作系统的命名管道或 Unix Socket

#### 实现示例

**Python 端**：
```python
import socket
import os

socket_path = '/tmp/vibe-coding.sock'
if os.path.exists(socket_path):
    os.remove(socket_path)

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(socket_path)
server.listen(1)

while True:
    conn, _ = server.accept()
    data = conn.recv(1024)
    # 处理请求...
    conn.send(response)
```

**TypeScript 端**：
```typescript
import * as net from 'net';

const client = net.connect('/tmp/vibe-coding.sock');
client.write(JSON.stringify(request));
client.on('data', (data) => {
    const response = JSON.parse(data.toString());
});
```

#### 优点 ✅

- ✅ 高性能（比 HTTP 快）
- ✅ 无端口占用

#### 缺点 ❌

- ❌ **跨平台问题**：Windows 的 Named Pipes 不同
- ❌ **复杂度高**：需要处理底层 socket
- ❌ **难以调试**

#### 推荐指数：⭐⭐⭐

性能好但跨平台麻烦，不如 stdin/stdout 简单。

---

### 方案 F: Message Queue (ZeroMQ) 🌟🌟

**原理**：使用消息队列库

#### 实现示例

**Python 端**：
```python
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://127.0.0.1:5555")

while True:
    message = socket.recv_json()
    result = process(message)
    socket.send_json(result)
```

#### 优点 ✅

- ✅ 高性能
- ✅ 支持多种模式（REQ/REP, PUB/SUB）

#### 缺点 ❌

- ❌ 需要额外依赖
- ❌ 过于复杂
- ❌ 端口占用

#### 推荐指数：⭐⭐

过度设计。

---

## 综合对比表

| 特性 | JSON-RPC | 简单JSON | gRPC | HTTP | Named Pipes | ZeroMQ |
|-----|----------|---------|------|------|-------------|--------|
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **简单性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **调试性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **标准化** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **跨平台** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **依赖少** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **双向通信** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **流式支持** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **无端口占用** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |

---

## 🏆 最终推荐：JSON-RPC over stdin/stdout

### 为什么？

1. **VS Code 生态的标准**
   - Language Server Protocol 基于 JSON-RPC
   - Python、Pylance、TypeScript Server 都用这种方式
   - 有大量成熟案例

2. **完美平衡**
   - 性能足够好（进程通信）
   - 足够简单（JSON + stdio）
   - 标准化（JSON-RPC 2.0）
   - 易于调试（文本协议）

3. **无外部依赖**
   - 不需要端口
   - 不需要额外的库
   - 跨平台兼容

4. **可扩展**
   - 支持通知（单向消息）
   - 支持批量请求
   - 可以轻松添加新方法

### 实际案例

**VS Code 中使用 JSON-RPC 的扩展**：
- Python Extension (Pylance)
- TypeScript Language Server
- Rust Analyzer
- C/C++ Extension

这些都是高质量、成熟的扩展，证明这种方式可靠。

---

## 替代建议

### 如果需要流式响应

**问题**：JSON-RPC 不太适合流式输出（如 AI 逐字生成）

**解决方案 1**：Server-Sent Events (SSE) 模拟

```python
# Python 端：发送多个通知
for chunk in stream_generate():
    notification = {
        'jsonrpc': '2.0',
        'method': 'stream_chunk',
        'params': {'chunk': chunk}
    }
    print(json.dumps(notification), flush=True)

# 最后发送完成通知
final = {
    'jsonrpc': '2.0',
    'result': {'done': True},
    'id': request_id
}
print(json.dumps(final), flush=True)
```

```typescript
// TypeScript 端：监听通知
rl.on('line', (line) => {
    const msg = JSON.parse(line);
    if (msg.method === 'stream_chunk') {
        // 处理流式数据
        onChunk(msg.params.chunk);
    } else if (msg.id !== undefined) {
        // 处理响应
        this.handleResponse(msg);
    }
});
```

**解决方案 2**：混合方案

- 使用 JSON-RPC 处理请求/响应
- 使用 WebSocket 处理流式数据（可选）

```typescript
// 主通信：JSON-RPC
const result = await pythonService.request('analyze', params);

// 流式数据：WebSocket（Python 端可选启动）
const ws = new WebSocket('ws://localhost:8766');
ws.on('message', (chunk) => {
    // 处理流式数据
});
```

---

## 建议

### 阶段 1: MVP
- ✅ 使用 **JSON-RPC over stdin/stdout**
- ✅ 实现基本的请求/响应
- ✅ 不用流式，等待完整结果

### 阶段 2: 优化
- 🔄 如果需要流式，添加通知机制
- 🔄 如果性能不够，考虑 Named Pipes

### 阶段 3: 高级功能
- 📡 如果需要复杂的双向通信，考虑混合方案
- 📡 对特定功能（如大文件传输）使用专门优化

---

## 结论

**JSON-RPC over stdin/stdout** 是最佳选择，因为：
1. ✅ 简单可靠
2. ✅ VS Code 生态标准
3. ✅ 高性能
4. ✅ 易于调试
5. ✅ 无外部依赖

**其他方案的适用场景**：
- **简单 JSON**：快速原型，不在意标准
- **gRPC**：分布式系统，需要强类型
- **HTTP**：需要远程访问，或已有 web 后端
- **Named Pipes**：极致性能，愿意处理跨平台问题

**我的建议**：从 JSON-RPC 开始，99% 的场景它都够用！

