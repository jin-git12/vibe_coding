/**
 * 配置管理工具
 */

import * as vscode from 'vscode';

export interface VibeCodingConfig {
    dashscopeApiKey: string;
    model: string;
    dashscopeBaseUrl: string;
    enableAutoComplete: boolean;
    maxContextFiles: number;
    streamResponse: boolean;
    pythonPath: string;
}

export class ConfigManager {
    private static readonly EXTENSION_ID = 'vibe-coding';

    static getConfig(): VibeCodingConfig {
        const config = vscode.workspace.getConfiguration(this.EXTENSION_ID);
        
        return {
            dashscopeApiKey: config.get('dashscopeApiKey', ''),
            model: config.get('model', 'qwen-turbo'),
            dashscopeBaseUrl: config.get('dashscopeBaseUrl', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            enableAutoComplete: config.get('enableAutoComplete', true),
            maxContextFiles: config.get('maxContextFiles', 5),
            streamResponse: config.get('streamResponse', true),
            pythonPath: config.get('pythonPath', 'uv')
        };
    }

    static async setApiKey(apiKey: string): Promise<void> {
        const config = vscode.workspace.getConfiguration(this.EXTENSION_ID);
        await config.update('dashscopeApiKey', apiKey, vscode.ConfigurationTarget.Global);
    }

    static async setModel(model: string): Promise<void> {
        const config = vscode.workspace.getConfiguration(this.EXTENSION_ID);
        await config.update('model', model, vscode.ConfigurationTarget.Global);
    }

    static onConfigChange(callback: () => void): vscode.Disposable {
        return vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration(this.EXTENSION_ID)) {
                callback();
            }
        });
    }

    static validateConfig(): { valid: boolean; errors: string[] } {
        const config = this.getConfig();
        const errors: string[] = [];

        if (!config.dashscopeApiKey) {
            errors.push('DashScope API Key is not configured');
        }

        if (!config.pythonPath) {
            errors.push('Python path is not configured');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

