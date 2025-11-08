/**
 * 上下文树视图提供程序
 * 显示当前代码上下文信息
 */

import * as vscode from 'vscode';
import { ContextService } from '../services/contextService';
import { Logger } from '../utils/logger';

export interface ContextItem {
    type: 'file' | 'selection' | 'symbol' | 'workspace';
    label: string;
    description?: string;
    detail?: string;
    path?: string;
    range?: vscode.Range;
}

export class ContextTreeProvider implements vscode.TreeDataProvider<ContextTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ContextTreeItem | undefined | null | void> = 
        new vscode.EventEmitter<ContextTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ContextTreeItem | undefined | null | void> = 
        this._onDidChangeTreeData.event;

    private contextItems: ContextItem[] = [];

    constructor() {
        // 监听编辑器变化
        vscode.window.onDidChangeActiveTextEditor(() => {
            this.refresh();
        });

        // 监听选择变化
        vscode.window.onDidChangeTextEditorSelection(() => {
            this.refresh();
        });
    }

    refresh(): void {
        this.updateContext();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ContextTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: ContextTreeItem): Promise<ContextTreeItem[]> {
        if (element) {
            return [];
        }

        // 更新上下文
        await this.updateContext();

        // 转换为树项
        return this.contextItems.map(item => new ContextTreeItem(item));
    }

    /**
     * 更新当前上下文信息
     */
    private async updateContext(): Promise<void> {
        this.contextItems = [];

        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return;
        }

        // 当前文件
        this.contextItems.push({
            type: 'file',
            label: vscode.workspace.asRelativePath(editor.document.uri),
            description: `${editor.document.lineCount} lines`,
            detail: editor.document.languageId,
            path: editor.document.uri.fsPath
        });

        // 当前选择
        const selection = editor.selection;
        if (!selection.isEmpty) {
            const selectedText = editor.document.getText(selection);
            const lineCount = selection.end.line - selection.start.line + 1;
            
            this.contextItems.push({
                type: 'selection',
                label: 'Selected Text',
                description: `${lineCount} line${lineCount > 1 ? 's' : ''}`,
                detail: selectedText.length > 100 
                    ? selectedText.substring(0, 100) + '...' 
                    : selectedText,
                range: selection
            });
        }

        // 工作区信息
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
        if (workspaceFolder) {
            this.contextItems.push({
                type: 'workspace',
                label: workspaceFolder.name,
                description: 'Workspace',
                path: workspaceFolder.uri.fsPath
            });
        }
    }

    /**
     * 获取所有上下文项
     */
    getContextItems(): ContextItem[] {
        return this.contextItems;
    }
}

export class ContextTreeItem extends vscode.TreeItem {
    constructor(public readonly contextItem: ContextItem) {
        super(contextItem.label, vscode.TreeItemCollapsibleState.None);

        this.description = contextItem.description;
        this.tooltip = contextItem.detail || contextItem.label;

        // 设置图标
        switch (contextItem.type) {
            case 'file':
                this.iconPath = new vscode.ThemeIcon('file-code');
                break;
            case 'selection':
                this.iconPath = new vscode.ThemeIcon('selection');
                break;
            case 'symbol':
                this.iconPath = new vscode.ThemeIcon('symbol-method');
                break;
            case 'workspace':
                this.iconPath = new vscode.ThemeIcon('folder-opened');
                break;
        }

        // 设置命令
        if (contextItem.type === 'file' && contextItem.path) {
            this.command = {
                command: 'vscode.open',
                title: 'Open File',
                arguments: [vscode.Uri.file(contextItem.path)]
            };
        } else if (contextItem.type === 'selection' && contextItem.range) {
            this.command = {
                command: 'vibe-coding.revealSelection',
                title: 'Reveal Selection',
                arguments: [contextItem.range]
            };
        }

        this.contextValue = contextItem.type;
    }
}

