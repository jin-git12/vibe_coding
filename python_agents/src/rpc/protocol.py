"""
JSON-RPC 协议定义
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class JSONRPCRequest:
    """JSON-RPC 请求"""
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'JSONRPCRequest':
        """从字典创建请求对象"""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data["method"],
            params=data.get("params", {}),
            id=data.get("id")
        )
    
    def is_notification(self) -> bool:
        """是否是通知（无 id）"""
        return self.id is None


@dataclass
class JSONRPCResponse:
    """JSON-RPC 响应"""
    jsonrpc: str
    result: Any
    id: int
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "jsonrpc": self.jsonrpc,
            "result": self.result,
            "id": self.id
        }


@dataclass
class JSONRPCErrorResponse:
    """JSON-RPC 错误响应"""
    jsonrpc: str
    error: Dict[str, Any]
    id: Optional[int]
    
    def to_dict(self) -> dict:
        """转换为字典"""
        response = {
            "jsonrpc": self.jsonrpc,
            "error": self.error
        }
        if self.id is not None:
            response["id"] = self.id
        return response


@dataclass
class JSONRPCNotification:
    """JSON-RPC 通知"""
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params
        }

