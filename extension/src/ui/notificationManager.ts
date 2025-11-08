/**
 * 通知管理器
 * 统一管理各种通知和提示
 */

import * as vscode from 'vscode';
import { Logger } from '../utils/logger';

export enum NotificationType {
    Info = 'info',
    Warning = 'warning',
    Error = 'error',
    Success = 'success'
}

export interface NotificationOptions {
    modal?: boolean;
    actions?: string[];
    detail?: string;
}

export class NotificationManager {
    private static instance: NotificationManager;

    private constructor() {}

    /**
     * 获取单例实例
     */
    static getInstance(): NotificationManager {
        if (!NotificationManager.instance) {
            NotificationManager.instance = new NotificationManager();
        }
        return NotificationManager.instance;
    }

    /**
     * 显示信息通知
     */
    async showInfo(
        message: string,
        options?: NotificationOptions
    ): Promise<string | undefined> {
        Logger.info(message);
        
        if (options?.actions && options.actions.length > 0) {
            return await vscode.window.showInformationMessage(
                message,
                { modal: options.modal, detail: options.detail },
                ...options.actions
            );
        }
        
        vscode.window.showInformationMessage(message);
        return undefined;
    }

    /**
     * 显示警告通知
     */
    async showWarning(
        message: string,
        options?: NotificationOptions
    ): Promise<string | undefined> {
        Logger.warn(message);
        
        if (options?.actions && options.actions.length > 0) {
            return await vscode.window.showWarningMessage(
                message,
                { modal: options.modal, detail: options.detail },
                ...options.actions
            );
        }
        
        vscode.window.showWarningMessage(message);
        return undefined;
    }

    /**
     * 显示错误通知
     */
    async showError(
        message: string,
        error?: Error,
        options?: NotificationOptions
    ): Promise<string | undefined> {
        const fullMessage = error ? `${message}: ${error.message}` : message;
        Logger.error(message, error);
        
        if (options?.actions && options.actions.length > 0) {
            return await vscode.window.showErrorMessage(
                fullMessage,
                { modal: options.modal, detail: options.detail || error?.stack },
                ...options.actions
            );
        }
        
        vscode.window.showErrorMessage(fullMessage);
        return undefined;
    }

    /**
     * 显示成功通知
     */
    showSuccess(message: string): void {
        Logger.info(`✓ ${message}`);
        vscode.window.showInformationMessage(`✓ ${message}`);
    }

    /**
     * 显示带确认的通知
     */
    async confirm(
        message: string,
        detail?: string
    ): Promise<boolean> {
        const result = await vscode.window.showInformationMessage(
            message,
            { modal: true, detail },
            'Yes',
            'No'
        );
        return result === 'Yes';
    }

    /**
     * 显示带确认的警告
     */
    async confirmWarning(
        message: string,
        detail?: string
    ): Promise<boolean> {
        const result = await vscode.window.showWarningMessage(
            message,
            { modal: true, detail },
            'Yes',
            'No'
        );
        return result === 'Yes';
    }

    /**
     * 显示选择对话框
     */
    async showQuickPick<T extends vscode.QuickPickItem>(
        items: T[],
        options?: vscode.QuickPickOptions
    ): Promise<T | undefined> {
        return await vscode.window.showQuickPick(items, options);
    }

    /**
     * 显示输入框
     */
    async showInputBox(
        options?: vscode.InputBoxOptions
    ): Promise<string | undefined> {
        return await vscode.window.showInputBox(options);
    }

    /**
     * 显示多选对话框
     */
    async showMultiPick<T extends vscode.QuickPickItem>(
        items: T[],
        options?: vscode.QuickPickOptions
    ): Promise<T[] | undefined> {
        const quickPick = vscode.window.createQuickPick<T>();
        quickPick.items = items;
        quickPick.canSelectMany = true;
        
        if (options?.placeHolder) {
            quickPick.placeholder = options.placeHolder;
        }

        return new Promise((resolve) => {
            quickPick.onDidAccept(() => {
                const selection = quickPick.selectedItems;
                quickPick.hide();
                resolve(selection.length > 0 ? Array.from(selection) : undefined);
            });

            quickPick.onDidHide(() => {
                resolve(undefined);
                quickPick.dispose();
            });

            quickPick.show();
        });
    }

    /**
     * 显示文件选择对话框
     */
    async showOpenDialog(
        options?: vscode.OpenDialogOptions
    ): Promise<vscode.Uri[] | undefined> {
        return await vscode.window.showOpenDialog(options);
    }

    /**
     * 显示保存对话框
     */
    async showSaveDialog(
        options?: vscode.SaveDialogOptions
    ): Promise<vscode.Uri | undefined> {
        return await vscode.window.showSaveDialog(options);
    }

    /**
     * 显示进度通知
     */
    async showProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ message?: string; increment?: number }>) => Promise<T>
    ): Promise<T> {
        return await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title,
                cancellable: false
            },
            task
        );
    }

    /**
     * 显示可取消的进度通知
     */
    async showCancellableProgress<T>(
        title: string,
        task: (
            progress: vscode.Progress<{ message?: string; increment?: number }>,
            token: vscode.CancellationToken
        ) => Promise<T>
    ): Promise<T> {
        return await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title,
                cancellable: true
            },
            task
        );
    }

    /**
     * 在状态栏显示临时消息
     */
    showStatusMessage(message: string, duration?: number): vscode.Disposable {
        if (duration !== undefined) {
            return vscode.window.setStatusBarMessage(message, duration);
        }
        return vscode.window.setStatusBarMessage(message);
    }
}

// 导出便捷方法
export const notify = NotificationManager.getInstance();

