/**
 * JSON-RPC 2.0 类型定义
 */

export interface JsonRpcRequest {
    jsonrpc: '2.0';
    method: string;
    params?: any;
    id: number | string;
}

export interface JsonRpcResponse {
    jsonrpc: '2.0';
    result?: any;
    error?: JsonRpcError;
    id: number | string | null;
}

export interface JsonRpcNotification {
    jsonrpc: '2.0';
    method: string;
    params?: any;
}

export interface JsonRpcError {
    code: number;
    message: string;
    data?: any;
}

/**
 * RPC 方法名称常量
 */
export enum RpcMethod {
    GenerateCode = 'generate_code',
    ExplainCode = 'explain_code',
    RefactorCode = 'refactor_code',
    ReviewCode = 'review_code',
    SearchCode = 'search_code',
    Chat = 'chat',
    GetContext = 'get_context',
    AnalyzeProject = 'analyze_project',
    HealthCheck = 'health_check',
    Shutdown = 'shutdown'
}

/**
 * RPC 错误码
 */
export enum RpcErrorCode {
    ParseError = -32700,
    InvalidRequest = -32600,
    MethodNotFound = -32601,
    InvalidParams = -32602,
    InternalError = -32603,
    AgentError = -32000,
    LlmError = -32001,
    FileSystemError = -32002,
    TimeoutError = -32003,
    SecurityError = -32004
}

