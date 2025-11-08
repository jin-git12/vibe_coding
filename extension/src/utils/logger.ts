/**
 * 日志管理工具
 */

import * as vscode from 'vscode';

export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3
}

export class Logger {
    private static outputChannel: vscode.OutputChannel;
    private static level: LogLevel = LogLevel.INFO;

    static initialize() {
        this.outputChannel = vscode.window.createOutputChannel('Vibe Coding');
    }

    static setLevel(level: LogLevel) {
        this.level = level;
    }

    static debug(message: string, ...args: any[]) {
        if (this.level <= LogLevel.DEBUG) {
            this.log('DEBUG', message, args);
        }
    }

    static info(message: string, ...args: any[]) {
        if (this.level <= LogLevel.INFO) {
            this.log('INFO', message, args);
        }
    }

    static warn(message: string, ...args: any[]) {
        if (this.level <= LogLevel.WARN) {
            this.log('WARN', message, args);
        }
    }

    static error(message: string, error?: Error, ...args: any[]) {
        if (this.level <= LogLevel.ERROR) {
            this.log('ERROR', message, args);
            if (error) {
                this.outputChannel.appendLine(`  Stack: ${error.stack}`);
            }
        }
    }

    private static log(level: string, message: string, args: any[]) {
        const timestamp = new Date().toISOString();
        const formattedMessage = `[${timestamp}] [${level}] ${message}`;
        
        this.outputChannel.appendLine(formattedMessage);
        
        if (args.length > 0) {
            this.outputChannel.appendLine(`  Data: ${JSON.stringify(args, null, 2)}`);
        }
    }

    static show() {
        this.outputChannel.show();
    }

    static dispose() {
        this.outputChannel.dispose();
    }
}

