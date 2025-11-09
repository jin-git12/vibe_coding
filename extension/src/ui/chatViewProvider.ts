/**
 * 聊天视图提供程序
 * 侧边栏中的 AI 聊天界面
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { AgentBridge } from '../services/agentBridge';
import { Conversation, ConversationMessage } from '../models/contextTypes';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';
import { ContextService } from '../services/contextService';

export class ChatViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'vibe-coding-chat';
    private view?: vscode.WebviewView;
    private currentConversation: Conversation | null = null;
    private conversations: Map<string, Conversation> = new Map();
    private selectedModel: string = 'qwen-turbo'; // 当前选择的模型

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly agentBridge: AgentBridge
    ) {
        // 监听流式响应
        this.agentBridge.on('chat-stream', (chunk: any) => {
            this.handleStreamChunk(chunk);
        });
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        token: vscode.CancellationToken
    ): void | Thenable<void> {
        this.view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                vscode.Uri.joinPath(this.extensionUri, 'resources')
            ]
        };

        webviewView.webview.html = this.getHtmlForWebview(webviewView.webview);

        // 处理来自 webview 的消息
        webviewView.webview.onDidReceiveMessage(async (data) => {
            await this.handleMessage(data);
        });

        // 初始化新对话
        this.newConversation();
    }

    /**
     * 发送消息到 AI
     */
    async sendMessage(message: string, model?: string): Promise<void> {
        // 如果提供了模型参数，更新选择的模型
        if (model) {
            this.selectedModel = model;
            await ConfigManager.setModel(model);
        }
        if (!this.currentConversation) {
            this.newConversation();
        }

        // 添加用户消息
        const userMessage: ConversationMessage = {
            role: 'user',
            content: message,
            timestamp: Date.now()
        };
        this.currentConversation!.messages.push(userMessage);

        // 显示在 UI
        this.postMessage({
            type: 'addMessage',
            message: {
                role: 'user',
                content: message
            }
        });

        // 显示加载状态
        this.postMessage({ type: 'setLoading', loading: true });

        try {
            // 收集上下文
            const context = await ContextService.buildCodeContext({
                includeSelection: true,
                includeCurrentFile: true,
                includeSurrounding: true
            });

            const config = ConfigManager.getConfig();

            // 发送到 AI
            const result = await this.agentBridge.chat({
                message,
                conversationId: this.currentConversation!.id,
                context,
                stream: config.streamResponse
            });

            // 添加 AI 响应
            const assistantMessage: ConversationMessage = {
                role: 'assistant',
                content: result.response,
                timestamp: Date.now()
            };
            this.currentConversation!.messages.push(assistantMessage);
            this.currentConversation!.updatedAt = Date.now();

            // 如果不是流式，立即显示完整响应
            if (!config.streamResponse) {
                this.postMessage({
                    type: 'addMessage',
                    message: {
                        role: 'assistant',
                        content: result.response
                    }
                });
            }

            // 显示建议
            if (result.suggestions && result.suggestions.length > 0) {
                this.postMessage({
                    type: 'showSuggestions',
                    suggestions: result.suggestions
                });
            }

        } catch (error) {
            Logger.error('Failed to send message', error as Error);
            this.postMessage({
                type: 'addMessage',
                message: {
                    role: 'assistant',
                    content: `❌ Error: ${(error as Error).message}`
                }
            });
        } finally {
            this.postMessage({ type: 'setLoading', loading: false });
        }
    }

    /**
     * 创建新对话
     */
    newConversation(): void {
        const conversationId = this.generateId();
        this.currentConversation = {
            id: conversationId,
            title: 'New Conversation',
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now()
        };
        this.conversations.set(conversationId, this.currentConversation);

        // 通知 WebView 创建新标签
        this.postMessage({ 
            type: 'createNewConversation',
            conversationId: conversationId
        });
        Logger.info(`New conversation created: ${conversationId}`);
    }

    /**
     * 切换到指定对话
     */
    switchConversation(conversationId: string): void {
        const conversation = this.conversations.get(conversationId);
        if (!conversation) {
            Logger.warn(`Conversation not found: ${conversationId}`);
            return;
        }

        this.currentConversation = conversation;
        
        // 清空 UI 并加载消息
        this.postMessage({ type: 'clearChat' });
        
        // 依次显示所有消息
        for (const message of conversation.messages) {
            this.postMessage({
                type: 'addMessage',
                message: {
                    role: message.role,
                    content: message.content
                }
            });
        }

        Logger.info(`Switched to conversation: ${conversationId}`);
    }

    /**
     * 删除指定对话
     */
    deleteConversation(conversationId: string): void {
        this.conversations.delete(conversationId);
        
        // 如果删除的是当前对话，创建新对话
        if (this.currentConversation?.id === conversationId) {
            this.newConversation();
        }

        Logger.info(`Conversation deleted: ${conversationId}`);
    }

    /**
     * 清除历史
     */
    clearHistory(): void {
        this.conversations.clear();
        this.newConversation();
        vscode.window.showInformationMessage('All chat history cleared');
    }

    /**
     * 获取所有对话
     */
    getConversations(): Conversation[] {
        return Array.from(this.conversations.values());
    }

    private async handleMessage(data: any): Promise<void> {
        switch (data.type) {
            case 'sendMessage':
                await this.sendMessage(data.message, data.model);
                break;

            case 'modelChanged':
                Logger.info(`📝 Received modelChanged event: ${data.model}`);
                // 更新选择的模型
                this.selectedModel = data.model;
                await ConfigManager.setModel(data.model);
                Logger.info(`✓ Config updated with model: ${data.model}`);
                
                // 🔧 调用后端切换模型
                try {
                    Logger.info(`🔄 Calling agentBridge.switchModel(${data.model})`);
                    const result = await this.agentBridge.switchModel(data.model);
                    Logger.info(`✓ Model switched successfully: ${JSON.stringify(result)}`);
                    vscode.window.showInformationMessage(`Model switched to: ${data.model}`);
                } catch (error) {
                    Logger.error('❌ Failed to switch model', error as Error);
                    vscode.window.showErrorMessage(`Failed to switch model: ${(error as Error).message}`);
                }
                break;

            case 'newConversation':
                // WebView 创建的新会话
                const conversationId = data.conversationId;
                if (!this.conversations.has(conversationId)) {
                    this.currentConversation = {
                        id: conversationId,
                        title: 'New Conversation',
                        messages: [],
                        createdAt: Date.now(),
                        updatedAt: Date.now()
                    };
                    this.conversations.set(conversationId, this.currentConversation);
                }
                break;

            case 'switchConversation':
                // WebView 切换会话
                const switchId = data.conversationId;
                const conv = this.conversations.get(switchId);
                if (conv) {
                    this.currentConversation = conv;
                }
                break;

            case 'deleteConversation':
                // WebView 删除会话
                const deleteId = data.conversationId;
                this.conversations.delete(deleteId);
                break;

            case 'insertCode':
                this.insertCodeAtCursor(data.code);
                break;

            case 'copyCode':
                vscode.env.clipboard.writeText(data.code);
                vscode.window.showInformationMessage('Code copied to clipboard');
                break;

            case 'ready':
                // WebView 已准备好
                Logger.info('Chat webview ready');
                break;
        }
    }

    private handleStreamChunk(chunk: any): void {
        if (chunk.conversationId !== this.currentConversation?.id) {
            return;
        }

        this.postMessage({
            type: 'streamChunk',
            chunk: chunk.chunk,
            done: chunk.done
        });

        if (chunk.done) {
            // 流式完成，更新对话
            this.currentConversation!.updatedAt = Date.now();
        }
    }

    private postMessage(message: any): void {
        this.view?.webview.postMessage(message);
    }

    private insertCodeAtCursor(code: string): void {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            editor.edit(editBuilder => {
                editBuilder.insert(editor.selection.active, code);
            });
        }
    }

    private generateId(): string {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    private getHtmlForWebview(webview: vscode.Webview): string {
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'resources', 'webview', 'chat.js')
        );
        const styleUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'resources', 'webview', 'chat.css')
        );

        // 读取 HTML 文件
        const htmlPath = vscode.Uri.joinPath(this.extensionUri, 'resources', 'webview', 'chat.html');
        const fs = require('fs');
        let html = fs.readFileSync(htmlPath.fsPath, 'utf8');

        const nonce = this.getNonce();
        
        // 添加缓存破坏参数（使用时间戳）
        const cacheBuster = Date.now();

        // 获取 codicon 字体 URI
        const codiconUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'resources', 'fonts', 'codicon.css')
        );

        // 替换占位符
        html = html.replace(/chat\.css/g, `${styleUri}?v=${cacheBuster}`)
                   .replace(/chat\.js/g, `${scriptUri}?v=${cacheBuster}`)
                   .replace(/<head>/g, `<head>
    <link rel="stylesheet" href="${codiconUri}">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; font-src ${webview.cspSource}; script-src 'nonce-${nonce}';">`)
                   .replace(/<script/g, `<script nonce="${nonce}"`);

        return html;
    }

    private getNonce(): string {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }
}

