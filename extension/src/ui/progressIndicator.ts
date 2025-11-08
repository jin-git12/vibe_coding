/**
 * 进度指示器
 * 显示长时间操作的进度
 */

import * as vscode from 'vscode';

export class ProgressIndicator {
    /**
     * 显示确定性进度
     */
    static async withProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ increment?: number; message?: string }>) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: title,
                cancellable: false
            },
            task
        );
    }

    /**
     * 显示可取消的进度
     */
    static async withCancellableProgress<T>(
        title: string,
        task: (
            progress: vscode.Progress<{ increment?: number; message?: string }>,
            token: vscode.CancellationToken
        ) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: title,
                cancellable: true
            },
            task
        );
    }

    /**
     * 在状态栏显示进度
     */
    static async withStatusBarProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ message?: string }>) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Window,
                title: title
            },
            task
        );
    }

    /**
     * 显示不确定性进度（无百分比）
     */
    static async showIndeterminate(
        title: string,
        task: () => Promise<void>
    ): Promise<void> {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: title,
                cancellable: false
            },
            async () => {
                await task();
            }
        );
    }

    /**
     * 显示步骤进度
     */
    static async showSteps(
        title: string,
        steps: Array<{ name: string; task: () => Promise<void> }>
    ): Promise<void> {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: title,
                cancellable: false
            },
            async (progress) => {
                const increment = 100 / steps.length;

                for (let i = 0; i < steps.length; i++) {
                    const step = steps[i];
                    progress.report({
                        message: `${step.name} (${i + 1}/${steps.length})`,
                        increment: i === 0 ? increment : increment
                    });

                    await step.task();
                }
            }
        );
    }

    /**
     * 显示简单的加载消息
     */
    static async showLoading(
        message: string,
        task: () => Promise<void>
    ): Promise<void> {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Window,
                title: message
            },
            async () => {
                await task();
            }
        );
    }
}

/**
 * 进度报告器类
 * 用于手动控制进度
 */
export class ProgressReporter {
    private progress: vscode.Progress<{ increment?: number; message?: string }> | null = null;
    private currentValue: number = 0;

    constructor(
        private title: string,
        private cancellable: boolean = false
    ) {}

    /**
     * 开始显示进度
     */
    async start<T>(
        task: (reporter: ProgressReporter) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: this.title,
                cancellable: this.cancellable
            },
            async (progress, token) => {
                this.progress = progress;
                
                if (this.cancellable) {
                    token.onCancellationRequested(() => {
                        // 任务取消处理
                    });
                }

                return await task(this);
            }
        );
    }

    /**
     * 报告进度
     */
    report(value: number, message?: string): void {
        if (this.progress) {
            const increment = value - this.currentValue;
            this.currentValue = value;
            
            this.progress.report({
                increment: increment,
                message: message
            });
        }
    }

    /**
     * 更新消息
     */
    updateMessage(message: string): void {
        if (this.progress) {
            this.progress.report({ message });
        }
    }

    /**
     * 完成进度
     */
    complete(message?: string): void {
        if (this.progress) {
            const remaining = 100 - this.currentValue;
            this.progress.report({
                increment: remaining,
                message: message || 'Complete'
            });
        }
    }
}

