/**
 * Agent 桥接服务
 * 提供高层次的 Agent 调用 API
 */

import { JsonRpcClient } from './jsonRpcClient';
import { RpcMethod } from '../models/rpcTypes';
import {
    GenerateCodeParams, GenerateCodeResult,
    ExplainCodeParams, ExplainCodeResult,
    RefactorCodeParams, RefactorCodeResult,
    ReviewCodeParams, ReviewCodeResult,
    SearchCodeParams, SearchCodeResult,
    ChatParams, ChatResult, ChatStreamChunk
} from '../models/agentTypes';
import { Logger } from '../utils/logger';
import { EventEmitter } from 'events';

export class AgentBridge extends EventEmitter {
    constructor(private rpcClient: JsonRpcClient) {
        super();
        
        // 监听流式响应通知
        this.rpcClient.on('notification', (method: string, params: any) => {
            if (method === 'chat.stream') {
                this.emit('chat-stream', params as ChatStreamChunk);
            } else if (method.startsWith('progress.')) {
                this.emit('progress', method, params);
            }
        });
    }

    /**
     * 生成代码
     */
    async generateCode(params: GenerateCodeParams): Promise<GenerateCodeResult> {
        try {
            Logger.info('Generating code...', { prompt: params.prompt });
            const result = await this.rpcClient.request(RpcMethod.GenerateCode, params);
            Logger.info('Code generated successfully');
            return result;
        } catch (error) {
            Logger.error('Failed to generate code', error as Error);
            throw this.wrapError(error, 'Failed to generate code');
        }
    }

    /**
     * 解释代码
     */
    async explainCode(params: ExplainCodeParams): Promise<ExplainCodeResult> {
        try {
            Logger.info('Explaining code...', { language: params.language });
            const result = await this.rpcClient.request(RpcMethod.ExplainCode, params);
            Logger.info('Code explained successfully');
            return result;
        } catch (error) {
            Logger.error('Failed to explain code', error as Error);
            throw this.wrapError(error, 'Failed to explain code');
        }
    }

    /**
     * 重构代码
     */
    async refactorCode(params: RefactorCodeParams): Promise<RefactorCodeResult> {
        try {
            Logger.info('Refactoring code...', { instructions: params.instructions });
            const result = await this.rpcClient.request(RpcMethod.RefactorCode, params);
            Logger.info('Code refactored successfully');
            return result;
        } catch (error) {
            Logger.error('Failed to refactor code', error as Error);
            throw this.wrapError(error, 'Failed to refactor code');
        }
    }

    /**
     * 审查代码
     */
    async reviewCode(params: ReviewCodeParams): Promise<ReviewCodeResult> {
        try {
            Logger.info('Reviewing code...', { language: params.language });
            const result = await this.rpcClient.request(RpcMethod.ReviewCode, params);
            Logger.info('Code reviewed successfully');
            return result;
        } catch (error) {
            Logger.error('Failed to review code', error as Error);
            throw this.wrapError(error, 'Failed to review code');
        }
    }

    /**
     * 搜索代码
     */
    async searchCode(params: SearchCodeParams): Promise<SearchCodeResult> {
        try {
            Logger.info('Searching code...', { query: params.query });
            const result = await this.rpcClient.request(RpcMethod.SearchCode, params);
            Logger.info(`Found ${result.totalMatches} matches`);
            return result;
        } catch (error) {
            Logger.error('Failed to search code', error as Error);
            throw this.wrapError(error, 'Failed to search code');
        }
    }

    /**
     * 与 AI 聊天（流式）
     */
    async chat(params: ChatParams): Promise<ChatResult> {
        try {
            Logger.info('Starting chat...', { conversationId: params.conversationId });
            const result = await this.rpcClient.request(RpcMethod.Chat, params, 60000); // 60s timeout for chat
            Logger.info('Chat completed');
            return result;
        } catch (error) {
            Logger.error('Chat failed', error as Error);
            throw this.wrapError(error, 'Chat failed');
        }
    }

    /**
     * 切换 LLM 模型
     */
    async switchModel(model: string): Promise<{ success: boolean; message: string }> {
        try {
            Logger.info(`🔄 AgentBridge.switchModel called with: ${model}`);
            Logger.info(`📤 Sending RPC request: ${RpcMethod.SwitchModel}`);
            const result = await this.rpcClient.request(RpcMethod.SwitchModel, { model });
            Logger.info(`✓ RPC response received: ${JSON.stringify(result)}`);
            return result;
        } catch (error) {
            Logger.error('❌ AgentBridge.switchModel failed', error as Error);
            throw this.wrapError(error, 'Failed to switch model');
        }
    }

    /**
     * 健康检查
     */
    async healthCheck(): Promise<{ status: string; memory_mb: number }> {
        try {
            return await this.rpcClient.request(RpcMethod.HealthCheck, {}, 5000);
        } catch (error) {
            Logger.error('Health check failed', error as Error);
            throw error;
        }
    }

    /**
     * 关闭 Agent
     */
    async shutdown(): Promise<void> {
        try {
            this.rpcClient.notify(RpcMethod.Shutdown);
        } catch (error) {
            Logger.error('Shutdown failed', error as Error);
        }
    }

    private wrapError(error: any, message: string): Error {
        if (error instanceof Error) {
            error.message = `${message}: ${error.message}`;
            return error;
        }
        return new Error(`${message}: ${String(error)}`);
    }
}

