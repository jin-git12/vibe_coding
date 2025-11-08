/**
 * JSON-RPC 2.0 客户端
 * 负责与 Python 进程通信
 */

import { EventEmitter } from 'events';
import { JsonRpcRequest, JsonRpcResponse, JsonRpcNotification, RpcErrorCode } from '../models/rpcTypes';
import { Logger } from '../utils/logger';

export interface PendingRequest {
    resolve: (result: any) => void;
    reject: (error: Error) => void;
    timeout: NodeJS.Timeout;
}

export class JsonRpcClient extends EventEmitter {
    private requestId = 0;
    private pendingRequests = new Map<number | string, PendingRequest>();
    private readonly DEFAULT_TIMEOUT = 30000; // 30 seconds

    constructor() {
        super();
    }

    /**
     * 发送 RPC 请求
     */
    async request(method: string, params?: any, timeout?: number): Promise<any> {
        const id = ++this.requestId;
        const request: JsonRpcRequest = {
            jsonrpc: '2.0',
            method,
            params,
            id
        };

        return new Promise((resolve, reject) => {
            const timeoutMs = timeout || this.DEFAULT_TIMEOUT;
            const timer = setTimeout(() => {
                this.pendingRequests.delete(id);
                reject(new Error(`Request timeout after ${timeoutMs}ms: ${method}`));
            }, timeoutMs);

            this.pendingRequests.set(id, { resolve, reject, timeout: timer });

            Logger.debug(`Sending RPC request: ${method}`, { id, params });
            this.emit('request', request);
        });
    }

    /**
     * 发送通知（无需响应）
     */
    notify(method: string, params?: any): void {
        const notification: JsonRpcNotification = {
            jsonrpc: '2.0',
            method,
            params
        };

        Logger.debug(`Sending RPC notification: ${method}`, { params });
        this.emit('request', notification);
    }

    /**
     * 处理来自 Python 的响应
     */
    handleResponse(response: JsonRpcResponse): void {
        const { id, result, error } = response;

        if (id === null || id === undefined) {
            Logger.warn('Received response without id', response);
            return;
        }

        const pending = this.pendingRequests.get(id);
        if (!pending) {
            Logger.warn(`Received response for unknown request: ${id}`);
            return;
        }

        clearTimeout(pending.timeout);
        this.pendingRequests.delete(id);

        if (error) {
            Logger.error(`RPC error for request ${id}:`, new Error(error.message), error);
            pending.reject(this.createError(error));
        } else {
            Logger.debug(`Received RPC response for request ${id}`, { result });
            pending.resolve(result);
        }
    }

    /**
     * 处理来自 Python 的通知
     */
    handleNotification(notification: JsonRpcNotification): void {
        Logger.debug(`Received RPC notification: ${notification.method}`, notification.params);
        this.emit('notification', notification.method, notification.params);
    }

    /**
     * 处理接收到的数据
     */
    handleMessage(message: JsonRpcResponse | JsonRpcNotification): void {
        if ('id' in message) {
            // Response
            this.handleResponse(message);
        } else if ('method' in message) {
            // Notification
            this.handleNotification(message);
        } else {
            Logger.warn('Received invalid JSON-RPC message', message);
        }
    }

    /**
     * 取消所有待处理的请求
     */
    cancelAll(reason: string): void {
        for (const [id, pending] of this.pendingRequests) {
            clearTimeout(pending.timeout);
            pending.reject(new Error(reason));
        }
        this.pendingRequests.clear();
    }

    /**
     * 获取待处理请求数量
     */
    getPendingCount(): number {
        return this.pendingRequests.size;
    }

    private createError(rpcError: any): Error {
        const error = new Error(rpcError.message || 'Unknown RPC error');
        (error as any).code = rpcError.code;
        (error as any).data = rpcError.data;
        return error;
    }
}

