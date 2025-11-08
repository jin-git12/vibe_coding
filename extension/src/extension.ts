/**
 * VS Code 扩展入口点
 * Vibe Coding - AI Code Assistant
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { PythonProcessService, ProcessStatus } from './services/pythonProcessService';
import { JsonRpcClient } from './services/jsonRpcClient';
import { AgentBridge } from './services/agentBridge';
import { ChatViewProvider } from './ui/chatViewProvider';
import { registerCommands } from './commands/registerCommands';
import { Logger, LogLevel } from './utils/logger';
import { ConfigManager } from './utils/config';

let pythonProcessService: PythonProcessService | null = null;
let jsonRpcClient: JsonRpcClient | null = null;
let agentBridge: AgentBridge | null = null;
let statusBarItem: vscode.StatusBarItem | null = null;

/**
 * 扩展激活
 */
export async function activate(context: vscode.ExtensionContext) {
    Logger.initialize();
    Logger.info('Activating Vibe Coding extension...');

    try {
        // 验证配置
        const configValidation = ConfigManager.validateConfig();
        if (!configValidation.valid) {
            Logger.warn('Configuration issues:', configValidation.errors);
            vscode.window.showWarningMessage(
                `Vibe Coding: ${configValidation.errors.join(', ')}. Please configure in settings.`,
                'Open Settings'
            ).then(selection => {
                if (selection === 'Open Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'vibe-coding');
                }
            });
        }

        // 初始化状态栏
        statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        statusBarItem.text = '$(loading~spin) Vibe Coding: Starting...';
        statusBarItem.show();
        context.subscriptions.push(statusBarItem);

        // 获取工作区路径
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            throw new Error('No workspace folder open');
        }
        const workspacePath = workspaceFolders[0].uri.fsPath;

        // 初始化 JSON-RPC 客户端
        jsonRpcClient = new JsonRpcClient();

        // 初始化 Agent 桥接
        agentBridge = new AgentBridge(jsonRpcClient);

        // ⚡ 重要：先初始化 UI（侧边栏视图），不依赖 Python 后端
        // 这样即使后端启动失败，侧边栏图标也会显示
        await setupUI(context, agentBridge);

        // 注册命令
        registerCommands(context, agentBridge, context.workspaceState.get('chatViewProvider')!, context.extensionUri);

        // 初始化 Python 进程服务
        pythonProcessService = new PythonProcessService(context.extensionPath, workspacePath);

        // 连接 Python 进程和 RPC 客户端
        setupProcessCommunication(pythonProcessService, jsonRpcClient, agentBridge);

        // 启动 Python 进程（异步，不阻塞 UI）
        pythonProcessService.start().catch(err => {
            Logger.error('Failed to start Python process', err);
            updateStatusBar(ProcessStatus.Error);
            vscode.window.showErrorMessage(
                `Vibe Coding: Python backend failed to start. ${err.message}`,
                'Show Logs'
            ).then(selection => {
                if (selection === 'Show Logs') {
                    Logger.show();
                }
            });
        });
        
        // 注册查看日志命令
        context.subscriptions.push(
            vscode.commands.registerCommand('vibe-coding.showLogs', () => {
                Logger.show();
            })
        );

        // 监听配置变化
        context.subscriptions.push(
            ConfigManager.onConfigChange(() => {
                Logger.info('Configuration changed, restarting Python process...');
                pythonProcessService?.restart().catch(err => {
                    Logger.error('Failed to restart after config change', err);
                });
            })
        );

        Logger.info('Vibe Coding extension activated successfully');
        // 注意：状态栏会在 Python 进程启动成功后更新

    } catch (error) {
        Logger.error('Failed to activate extension', error as Error);
        vscode.window.showErrorMessage(
            `Failed to activate Vibe Coding: ${(error as Error).message}`
        );
        updateStatusBar(ProcessStatus.Error);
    }
}

/**
 * 扩展停用
 */
export async function deactivate() {
    Logger.info('Deactivating Vibe Coding extension...');

    try {
        // 关闭 Agent
        if (agentBridge) {
            await agentBridge.shutdown();
        }

        // 停止 Python 进程
        if (pythonProcessService) {
            await pythonProcessService.stop();
        }

        // 取消所有待处理请求
        if (jsonRpcClient) {
            jsonRpcClient.cancelAll('Extension deactivating');
        }

        // 清理状态栏
        if (statusBarItem) {
            statusBarItem.dispose();
        }

        // 清理日志
        Logger.dispose();

        Logger.info('Vibe Coding extension deactivated');
    } catch (error) {
        Logger.error('Error during deactivation', error as Error);
    }
}

/**
 * 设置进程通信
 */
function setupProcessCommunication(
    processService: PythonProcessService,
    rpcClient: JsonRpcClient,
    agentBridge: AgentBridge
): void {
    // Python 进程响应 -> RPC 客户端
    processService.on('response', (message) => {
        rpcClient.handleResponse(message);
    });

    // Python 进程通知 -> RPC 客户端
    processService.on('notification', (method: string, params: any) => {
        rpcClient.handleNotification({ jsonrpc: '2.0', method, params });
    });

    // RPC 客户端 -> Python 进程
    rpcClient.on('request', (request) => {
        processService.send(request);
    });

    // 进程状态变化
    processService.on('status-change', (status: ProcessStatus) => {
        updateStatusBar(status);
    });

    // 健康检查请求
    processService.on('health-check-request', async () => {
        try {
            const result = await agentBridge.healthCheck();
            Logger.debug('Health check passed', { result });
        } catch (error) {
            Logger.error('Health check failed', error as Error);
            // 健康检查失败后会自动重启
            processService.restart().catch(err => {
                Logger.error('Failed to restart after health check failure', err);
            });
        }
    });

    // 关闭请求
    processService.on('shutdown-request', () => {
        agentBridge.shutdown();
    });
}

/**
 * 设置 UI
 */
async function setupUI(
    context: vscode.ExtensionContext,
    agentBridge: AgentBridge
): Promise<void> {
    // 创建聊天视图提供程序
    const chatViewProvider = new ChatViewProvider(context.extensionUri, agentBridge);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            ChatViewProvider.viewType,
            chatViewProvider,
            {
                webviewOptions: {
                    retainContextWhenHidden: true
                }
            }
        )
    );

    // 注册新建会话命令
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.newConversation', () => {
            chatViewProvider.newConversation();
        })
    );

    // 注册显示历史命令
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.showHistory', async () => {
            const conversations = chatViewProvider.getConversations();
            
            if (conversations.length === 0) {
                vscode.window.showInformationMessage('No conversation history yet');
                return;
            }

            // 格式化时间
            const formatTime = (timestamp: number) => {
                const now = Date.now();
                const diff = now - timestamp;
                const minutes = Math.floor(diff / 60000);
                const hours = Math.floor(diff / 3600000);
                const days = Math.floor(diff / 86400000);

                if (minutes < 1) return 'Just now';
                if (minutes < 60) return `${minutes}m`;
                if (hours < 24) return `${hours}h`;
                if (days < 7) return `${days}d`;
                return new Date(timestamp).toLocaleDateString();
            };

            // 创建快速选择项
            interface ConversationQuickPickItem extends vscode.QuickPickItem {
                conversationId: string;
            }

            const items: ConversationQuickPickItem[] = conversations
                .sort((a, b) => b.updatedAt - a.updatedAt)
                .map(conv => {
                    const messageCount = conv.messages.length;
                    const timeAgo = formatTime(conv.updatedAt);
                    
                    // 获取第一条用户消息作为标题
                    let title = conv.title;
                    if (title === 'New Conversation' && conv.messages.length > 0) {
                        const firstUserMsg = conv.messages.find(m => m.role === 'user');
                        if (firstUserMsg) {
                            title = firstUserMsg.content.substring(0, 50);
                            if (firstUserMsg.content.length > 50) {
                                title += '...';
                            }
                        }
                    }

                    return {
                        label: `$(comment-discussion) ${title}`,
                        description: timeAgo,
                        detail: `${messageCount} messages`,
                        conversationId: conv.id
                    };
                });

            // 显示快速选择
            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select a conversation to open',
                matchOnDescription: true,
                matchOnDetail: true
            });

            if (selected) {
                chatViewProvider.switchConversation(selected.conversationId);
            }
        })
    );

    // 注册显示聊天菜单命令
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.showChatMenu', async () => {
            const items = [
                { label: '$(close) Close Chat', value: 'close' },
                { label: '$(clear-all) Clear All Chats', value: 'clearAll' },
                { label: '$(close-all) Close Other Chats', value: 'closeOthers' },
                { label: '$(go-to-file) Open Chat as Editor', value: 'openEditor' },
                { label: '$(export) Export Chat', value: 'export' },
                { label: '$(copy) Copy Request ID', value: 'copyId' },
                { label: '$(feedback) Give Feedback', value: 'feedback' },
                { label: '$(settings-gear) Agent Settings', value: 'settings' }
            ];
            
            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select an action'
            });
            
            if (selected) {
                switch (selected.value) {
                    case 'close':
                        chatViewProvider.newConversation();
                        vscode.window.showInformationMessage('Started new conversation');
                        break;
                    case 'clearAll':
                        const confirm = await vscode.window.showWarningMessage(
                            'Are you sure you want to clear all chat history?',
                            'Yes', 'No'
                        );
                        if (confirm === 'Yes') {
                            chatViewProvider.clearHistory();
                        }
                        break;
                    case 'closeOthers':
                        vscode.window.showInformationMessage('Close other chats functionality coming soon');
                        break;
                    case 'openEditor':
                        vscode.window.showInformationMessage('Open chat as editor functionality coming soon');
                        break;
                    case 'export':
                        vscode.window.showInformationMessage('Export chat functionality coming soon');
                        break;
                    case 'copyId':
                        const conversations = chatViewProvider.getConversations();
                        if (conversations.length > 0) {
                            const currentConv = conversations[conversations.length - 1];
                            vscode.env.clipboard.writeText(currentConv.id);
                            vscode.window.showInformationMessage('Request ID copied to clipboard');
                        }
                        break;
                    case 'feedback':
                        vscode.env.openExternal(vscode.Uri.parse('https://github.com/yourusername/vibe-coding/issues'));
                        break;
                    case 'settings':
                        vscode.commands.executeCommand('workbench.action.openSettings', 'vibe-coding');
                        break;
                }
            }
        })
    );

    // 保存到工作区状态以便命令访问
    context.workspaceState.update('chatViewProvider', chatViewProvider);

    Logger.info('UI components initialized');
}

/**
 * 更新状态栏
 */
function updateStatusBar(status: ProcessStatus): void {
    if (!statusBarItem) {
        return;
    }

    switch (status) {
        case ProcessStatus.Idle:
            statusBarItem.text = '$(circle-outline) Vibe Coding: Idle';
            statusBarItem.color = undefined;
            break;

        case ProcessStatus.Starting:
            statusBarItem.text = '$(loading~spin) Vibe Coding: Starting...';
            statusBarItem.color = undefined;
            break;

        case ProcessStatus.Ready:
            statusBarItem.text = '$(check) Vibe Coding: Ready';
            statusBarItem.color = undefined;
            statusBarItem.tooltip = 'Click to open AI Chat';
            statusBarItem.command = 'vibe-coding.openChat';
            break;

        case ProcessStatus.Busy:
            statusBarItem.text = '$(sync~spin) Vibe Coding: Busy';
            statusBarItem.color = undefined;
            break;

        case ProcessStatus.Error:
            statusBarItem.text = '$(error) Vibe Coding: Error';
            statusBarItem.color = new vscode.ThemeColor('statusBarItem.errorBackground');
            statusBarItem.tooltip = 'Click to view logs';
            statusBarItem.command = 'vibe-coding.showLogs';
            break;

        case ProcessStatus.Stopped:
            statusBarItem.text = '$(stop-circle) Vibe Coding: Stopped';
            statusBarItem.color = undefined;
            break;
    }
}

