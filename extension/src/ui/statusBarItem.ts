/**
 * 状态栏管理
 * 显示扩展状态和快捷操作
 */

import * as vscode from 'vscode';
import { ProcessStatus } from '../services/pythonProcessService';

export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusBarItem.show();
    }

    /**
     * 更新状态栏显示
     */
    updateStatus(status: ProcessStatus, message?: string): void {
        switch (status) {
            case ProcessStatus.Idle:
                this.statusBarItem.text = '$(circle-outline) Vibe Coding';
                this.statusBarItem.tooltip = 'Vibe Coding AI - Idle';
                this.statusBarItem.color = undefined;
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.command = 'vibe-coding.openChat';
                break;

            case ProcessStatus.Starting:
                this.statusBarItem.text = '$(loading~spin) Vibe Coding';
                this.statusBarItem.tooltip = 'Vibe Coding AI - Starting...';
                this.statusBarItem.color = undefined;
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.command = undefined;
                break;

            case ProcessStatus.Ready:
                this.statusBarItem.text = '$(check) Vibe Coding';
                this.statusBarItem.tooltip = 'Vibe Coding AI - Ready\nClick to open chat';
                this.statusBarItem.color = undefined;
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.command = 'vibe-coding.openChat';
                break;

            case ProcessStatus.Busy:
                this.statusBarItem.text = '$(sync~spin) Vibe Coding';
                this.statusBarItem.tooltip = 'Vibe Coding AI - Processing...';
                this.statusBarItem.color = undefined;
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.command = undefined;
                break;

            case ProcessStatus.Error:
                this.statusBarItem.text = '$(error) Vibe Coding';
                this.statusBarItem.tooltip = `Vibe Coding AI - Error${message ? '\n' + message : ''}\nClick to view logs`;
                this.statusBarItem.color = new vscode.ThemeColor('statusBarItem.errorForeground');
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                this.statusBarItem.command = 'vibe-coding.showLogs';
                break;

            case ProcessStatus.Stopped:
                this.statusBarItem.text = '$(stop-circle) Vibe Coding';
                this.statusBarItem.tooltip = 'Vibe Coding AI - Stopped';
                this.statusBarItem.color = undefined;
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.command = 'vibe-coding.openChat';
                break;
        }
    }

    /**
     * 显示临时消息
     */
    showTemporaryMessage(message: string, duration: number = 3000): void {
        const originalText = this.statusBarItem.text;
        const originalTooltip = this.statusBarItem.tooltip;

        this.statusBarItem.text = `$(info) ${message}`;
        this.statusBarItem.tooltip = message;

        setTimeout(() => {
            this.statusBarItem.text = originalText;
            this.statusBarItem.tooltip = originalTooltip;
        }, duration);
    }

    /**
     * 显示进度
     */
    showProgress(message: string): void {
        this.statusBarItem.text = `$(sync~spin) ${message}`;
        this.statusBarItem.tooltip = message;
    }

    /**
     * 隐藏状态栏
     */
    hide(): void {
        this.statusBarItem.hide();
    }

    /**
     * 显示状态栏
     */
    show(): void {
        this.statusBarItem.show();
    }

    /**
     * 清理资源
     */
    dispose(): void {
        this.statusBarItem.dispose();
    }

    /**
     * 获取状态栏项（用于注册到 context.subscriptions）
     */
    getStatusBarItem(): vscode.StatusBarItem {
        return this.statusBarItem;
    }
}

