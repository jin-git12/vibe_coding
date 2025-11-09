"""
JSON-RPC 服务器核心
通过 stdin/stdout 与 VS Code 扩展通信
"""
import sys
import json
import logging
from typing import Callable, Dict, Any
from .protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCErrorResponse,
    JSONRPCNotification
)
from .errors import (
    JSONRPCError,
    ParseError,
    InvalidRequest,
    MethodNotFound,
    InternalError
)


logger = logging.getLogger(__name__)


def sanitize_for_json(obj):
    """
    清理对象中的无效 Unicode 字符，确保可以安全地进行 JSON 序列化
    
    处理孤立的代理字符（surrogate），这些字符在 UTF-8 编码中是无效的
    """
    if isinstance(obj, str):
        # 使用 'ignore' 错误处理器清理无效字符
        return obj.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_for_json(item) for item in obj)
    else:
        return obj


class JSONRPCServer:
    """JSON-RPC 服务器"""
    
    def __init__(self):
        self.methods: Dict[str, Callable] = {}
        self.running = False
    
    def register_method(self, name: str, handler: Callable):
        """注册 RPC 方法"""
        self.methods[name] = handler
        logger.info(f"Registered method: {name}")
    
    def send_response(self, response: JSONRPCResponse):
        """发送响应到 stdout"""
        data = response.to_dict()
        # 清理无效的 Unicode 字符
        data = sanitize_for_json(data)
        json_str = json.dumps(data, ensure_ascii=False)
        sys.stdout.write(json_str + '\n')
        sys.stdout.flush()
        logger.debug(f"Sent response: {json_str[:100]}...")
    
    def send_error(self, error: JSONRPCError, request_id: int = None):
        """发送错误响应"""
        response = JSONRPCErrorResponse(
            jsonrpc="2.0",
            error=error.to_dict(),
            id=request_id
        )
        data = response.to_dict()
        # 清理无效的 Unicode 字符
        data = sanitize_for_json(data)
        json_str = json.dumps(data, ensure_ascii=False)
        sys.stdout.write(json_str + '\n')
        sys.stdout.flush()
        logger.error(f"Sent error: {error.message}")
    
    def send_notification(self, method: str, params: Dict[str, Any]):
        """发送通知（无需响应）"""
        notification = JSONRPCNotification(
            jsonrpc="2.0",
            method=method,
            params=params
        )
        data = notification.to_dict()
        # 清理无效的 Unicode 字符
        data = sanitize_for_json(data)
        json_str = json.dumps(data, ensure_ascii=False)
        sys.stdout.write(json_str + '\n')
        sys.stdout.flush()
        logger.debug(f"Sent notification: {method}")
    
    def handle_request(self, request: JSONRPCRequest) -> Any:
        """处理请求"""
        method_name = request.method
        
        # 查找处理器
        if method_name not in self.methods:
            raise MethodNotFound(method_name)
        
        handler = self.methods[method_name]
        
        # 调用处理器
        try:
            result = handler(request.params)
            return result
        except JSONRPCError:
            raise
        except Exception as e:
            logger.exception(f"Error in handler {method_name}")
            raise InternalError(str(e), {"traceback": str(e)})
    
    def process_message(self, line: str):
        """处理单条消息"""
        request_id = None
        
        try:
            # 解析 JSON
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise ParseError(f"Invalid JSON: {str(e)}")
            
            # 验证请求格式
            if not isinstance(data, dict):
                raise InvalidRequest("Request must be an object")
            
            if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
                raise InvalidRequest("Invalid jsonrpc version")
            
            if "method" not in data:
                raise InvalidRequest("Missing method field")
            
            # 创建请求对象
            request = JSONRPCRequest.from_dict(data)
            request_id = request.id
            
            # 处理请求
            result = self.handle_request(request)
            
            # 发送响应（如果不是通知）
            if not request.is_notification():
                response = JSONRPCResponse(
                    jsonrpc="2.0",
                    result=result,
                    id=request.id
                )
                self.send_response(response)
        
        except JSONRPCError as e:
            self.send_error(e, request_id)
        except Exception as e:
            logger.exception("Unexpected error")
            self.send_error(InternalError(str(e)), request_id)
    
    def run(self):
        """启动服务器主循环"""
        self.running = True
        logger.info("JSON-RPC server starting...")
        
        # 发送就绪通知
        self.send_notification("server.ready", {
            "version": "1.0.0",
            "capabilities": list(self.methods.keys())
        })
        
        logger.info("Server ready, waiting for requests on stdin...")
        
        # 确保 stdin 是阻塞模式
        import os
        if hasattr(sys.stdin, 'fileno'):
            try:
                # 设置为阻塞模式
                fd = sys.stdin.fileno()
                flags = os.get_blocking(fd)
                if not flags:
                    os.set_blocking(fd, True)
                    logger.info("Set stdin to blocking mode")
            except Exception as e:
                logger.warning(f"Could not set stdin blocking mode: {e}")
        
        try:
            # 从 stdin 逐行读取
            while self.running:
                try:
                    # 使用阻塞读取
                    line = sys.stdin.readline()
                    
                    # 如果读到空字符串且不是空行，说明 stdin 关闭
                    if line == '':
                        logger.info("stdin closed (empty string), shutting down...")
                        break
                    
                    line = line.strip()
                    if not line:
                        # 空行，继续读取
                        continue
                    
                    logger.debug(f"Received: {line[:100]}...")
                    self.process_message(line)
                
                except EOFError:
                    logger.info("EOF on stdin, shutting down...")
                    break
                except KeyboardInterrupt:
                    raise
        
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.exception("Server error")
        finally:
            self.running = False
            logger.info("Server stopped")
    
    def stop(self):
        """停止服务器"""
        self.running = False

