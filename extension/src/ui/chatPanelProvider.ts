/**
 * 聊天面板提供程序
 * 独立窗口中的 AI 聊天界面（与侧边栏不同）
 */

import * as vscode from 'vscode';
import { AgentBridge } from '../services/agentBridge';
import { Conversation, ConversationMessage } from '../models/contextTypes';
import { Logger } from '../utils/logger';

export class ChatPanelProvider {
    private static currentPanel: vscode.WebviewPanel | undefined;
    private disposables: vscode.Disposable[] = [];

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly agentBridge: AgentBridge
    ) {}

    /**
     * 创建或显示聊天面板
     */
    public static createOrShow(
        extensionUri: vscode.Uri,
        agentBridge: AgentBridge
    ): void {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // 如果面板已存在，显示它
        if (ChatPanelProvider.currentPanel) {
            ChatPanelProvider.currentPanel.reveal(column);
            return;
        }

        // 创建新面板
        const panel = vscode.window.createWebviewPanel(
            'vibeCodingChat',
            'Vibe Coding AI Chat',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionUri, 'resources')
                ]
            }
        );

        ChatPanelProvider.currentPanel = panel;
        const provider = new ChatPanelProvider(extensionUri, agentBridge);
        provider.update(panel);

        // 监听面板关闭
        panel.onDidDispose(
            () => {
                ChatPanelProvider.currentPanel = undefined;
                provider.dispose();
            },
            null,
            provider.disposables
        );

        // 监听消息
        panel.webview.onDidReceiveMessage(
            async (message) => {
                await provider.handleMessage(message, panel);
            },
            null,
            provider.disposables
        );
    }

    /**
     * 更新面板内容
     */
    private update(panel: vscode.WebviewPanel): void {
        panel.webview.html = this.getHtmlForWebview(panel.webview);
    }

    /**
     * 处理来自 WebView 的消息
     */
    private async handleMessage(
        message: any,
        panel: vscode.WebviewPanel
    ): Promise<void> {
        switch (message.type) {
            case 'sendMessage':
                // 发送消息到 AI
                await this.sendMessage(message.message, panel);
                break;

            case 'insertCode':
                // 插入代码到编辑器
                this.insertCodeAtCursor(message.code);
                break;

            case 'copyCode':
                // 复制代码到剪贴板
                vscode.env.clipboard.writeText(message.code);
                vscode.window.showInformationMessage('Code copied to clipboard');
                break;

            case 'ready':
                Logger.info('Chat panel webview ready');
                break;
        }
    }

    /**
     * 发送消息到 AI
     */
    private async sendMessage(
        message: string,
        panel: vscode.WebviewPanel
    ): Promise<void> {
        try {
            // 显示加载状态
            panel.webview.postMessage({ type: 'setLoading', loading: true });

            // 调用 AI
            const result = await this.agentBridge.chat({
                message,
                conversationId: 'panel-' + Date.now(),
                context: {},
                stream: false
            });

            // 显示响应
            panel.webview.postMessage({
                type: 'addMessage',
                message: {
                    role: 'assistant',
                    content: result.response
                }
            });
        } catch (error) {
            Logger.error('Failed to send message', error as Error);
            panel.webview.postMessage({
                type: 'addMessage',
                message: {
                    role: 'assistant',
                    content: `❌ Error: ${(error as Error).message}`
                }
            });
        } finally {
            panel.webview.postMessage({ type: 'setLoading', loading: false });
        }
    }

    /**
     * 插入代码到光标位置
     */
    private insertCodeAtCursor(code: string): void {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            editor.edit(editBuilder => {
                editBuilder.insert(editor.selection.active, code);
            });
        }
    }

    /**
     * 获取 WebView HTML
     */
    private getHtmlForWebview(webview: vscode.Webview): string {
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'resources', 'webview', 'chat.js')
        );
        const styleUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'resources', 'webview', 'chat.css')
        );

        const nonce = this.getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <link rel="stylesheet" href="${styleUri}">
    <title>Vibe Coding AI Chat</title>
</head>
<body>
    <div id="chat-container">
        <div id="messages"></div>
    </div>
    <div id="input-container">
        <textarea id="message-input" placeholder="Ask AI anything..."></textarea>
        <button id="send-button">Send</button>
    </div>
    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
    }

    /**
     * 生成随机 nonce
     */
    private getNonce(): string {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }

    /**
     * 清理资源
     */
    public dispose(): void {
        while (this.disposables.length) {
            const disposable = this.disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}

