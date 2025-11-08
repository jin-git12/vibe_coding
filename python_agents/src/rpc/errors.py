"""
JSON-RPC 错误码定义
"""

class JSONRPCError(Exception):
    """JSON-RPC 错误基类"""
    def __init__(self, code: int, message: str, data: dict = None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(message)
    
    def to_dict(self):
        """转换为 JSON-RPC 错误格式"""
        error = {
            "code": self.code,
            "message": self.message
        }
        if self.data:
            error["data"] = self.data
        return error


# 标准 JSON-RPC 错误
class ParseError(JSONRPCError):
    """JSON 解析错误"""
    def __init__(self, message: str = "Parse error", data: dict = None):
        super().__init__(-32700, message, data)


class InvalidRequest(JSONRPCError):
    """无效的请求"""
    def __init__(self, message: str = "Invalid Request", data: dict = None):
        super().__init__(-32600, message, data)


class MethodNotFound(JSONRPCError):
    """方法不存在"""
    def __init__(self, method: str, data: dict = None):
        super().__init__(-32601, f"Method not found: {method}", data)


class InvalidParams(JSONRPCError):
    """无效的参数"""
    def __init__(self, message: str = "Invalid params", data: dict = None):
        super().__init__(-32602, message, data)


class InternalError(JSONRPCError):
    """内部错误"""
    def __init__(self, message: str = "Internal error", data: dict = None):
        super().__init__(-32603, message, data)


# 自定义错误
class AgentError(JSONRPCError):
    """Agent 执行错误"""
    def __init__(self, message: str, data: dict = None):
        super().__init__(-32000, f"Agent error: {message}", data)


class LLMError(JSONRPCError):
    """LLM API 错误"""
    def __init__(self, message: str, data: dict = None):
        super().__init__(-32001, f"LLM error: {message}", data)


class FileSystemError(JSONRPCError):
    """文件系统错误"""
    def __init__(self, message: str, data: dict = None):
        super().__init__(-32002, f"File system error: {message}", data)


class TimeoutError(JSONRPCError):
    """超时错误"""
    def __init__(self, message: str = "Operation timeout", data: dict = None):
        super().__init__(-32003, message, data)


class SecurityError(JSONRPCError):
    """安全检查失败"""
    def __init__(self, message: str, data: dict = None):
        super().__init__(-32004, f"Security error: {message}", data)

