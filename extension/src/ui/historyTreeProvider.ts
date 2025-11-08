/**
 * 历史记录树视图提供程序
 * 显示聊天历史和会话列表
 */

import * as vscode from 'vscode';
import { Conversation } from '../models/contextTypes';
import { Logger } from '../utils/logger';

export interface HistoryItem {
    id: string;
    title: string;
    timestamp: number;
    messageCount: number;
    preview?: string;
}

export class HistoryTreeProvider implements vscode.TreeDataProvider<HistoryTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<HistoryTreeItem | undefined | null | void> = 
        new vscode.EventEmitter<HistoryTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<HistoryTreeItem | undefined | null | void> = 
        this._onDidChangeTreeData.event;

    private historyItems: Map<string, HistoryItem> = new Map();

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: HistoryTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: HistoryTreeItem): Thenable<HistoryTreeItem[]> {
        if (element) {
            return Promise.resolve([]);
        }

        // 按时间倒序排列
        const items = Array.from(this.historyItems.values())
            .sort((a, b) => b.timestamp - a.timestamp)
            .map(item => new HistoryTreeItem(item));

        return Promise.resolve(items);
    }

    /**
     * 添加历史项
     */
    addHistoryItem(conversation: Conversation): void {
        const preview = conversation.messages.length > 0
            ? conversation.messages[0].content.substring(0, 50)
            : 'Empty conversation';

        const historyItem: HistoryItem = {
            id: conversation.id,
            title: conversation.title,
            timestamp: conversation.updatedAt,
            messageCount: conversation.messages.length,
            preview: preview
        };

        this.historyItems.set(conversation.id, historyItem);
        this.refresh();
    }

    /**
     * 更新历史项
     */
    updateHistoryItem(conversationId: string, conversation: Conversation): void {
        const existing = this.historyItems.get(conversationId);
        if (existing) {
            existing.title = conversation.title;
            existing.timestamp = conversation.updatedAt;
            existing.messageCount = conversation.messages.length;
            
            if (conversation.messages.length > 0) {
                existing.preview = conversation.messages[0].content.substring(0, 50);
            }
            
            this.refresh();
        }
    }

    /**
     * 删除历史项
     */
    removeHistoryItem(conversationId: string): void {
        this.historyItems.delete(conversationId);
        this.refresh();
    }

    /**
     * 清空所有历史
     */
    clearAll(): void {
        this.historyItems.clear();
        this.refresh();
    }

    /**
     * 获取所有历史项
     */
    getHistoryItems(): HistoryItem[] {
        return Array.from(this.historyItems.values())
            .sort((a, b) => b.timestamp - a.timestamp);
    }

    /**
     * 导出历史到文件
     */
    async exportHistory(): Promise<void> {
        const items = this.getHistoryItems();
        
        if (items.length === 0) {
            vscode.window.showInformationMessage('No history to export');
            return;
        }

        const content = JSON.stringify(items, null, 2);
        
        const uri = await vscode.window.showSaveDialog({
            defaultUri: vscode.Uri.file('vibe-coding-history.json'),
            filters: {
                'JSON': ['json']
            }
        });

        if (uri) {
            const fs = require('fs');
            fs.writeFileSync(uri.fsPath, content, 'utf8');
            vscode.window.showInformationMessage('History exported successfully');
        }
    }
}

export class HistoryTreeItem extends vscode.TreeItem {
    constructor(public readonly historyItem: HistoryItem) {
        super(historyItem.title, vscode.TreeItemCollapsibleState.None);

        // 格式化时间
        const timeAgo = this.formatTimeAgo(historyItem.timestamp);
        
        this.description = timeAgo;
        this.tooltip = `${historyItem.messageCount} messages\n${historyItem.preview || ''}`;
        
        // 设置图标
        this.iconPath = new vscode.ThemeIcon('comment-discussion');
        
        // 设置命令 - 点击打开该会话
        this.command = {
            command: 'vibe-coding.openHistoryItem',
            title: 'Open Conversation',
            arguments: [historyItem.id]
        };

        this.contextValue = 'historyItem';
    }

    /**
     * 格式化时间距离
     */
    private formatTimeAgo(timestamp: number): string {
        const now = Date.now();
        const diff = now - timestamp;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) {
            return 'Just now';
        } else if (minutes < 60) {
            return `${minutes}m ago`;
        } else if (hours < 24) {
            return `${hours}h ago`;
        } else if (days < 7) {
            return `${days}d ago`;
        } else {
            return new Date(timestamp).toLocaleDateString();
        }
    }
}

