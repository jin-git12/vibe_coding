/**
 * 上下文服务
 * 负责收集和管理代码上下文
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { CodeContext } from '../models/agentTypes';
import { FileContext, EditorContext } from '../models/contextTypes';
import { Logger } from '../utils/logger';

export class ContextService {
    /**
     * 获取当前编辑器上下文
     */
    static getCurrentEditorContext(): EditorContext | null {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return null;
        }

        return {
            document: editor.document,
            selection: editor.selection,
            position: editor.selection.active,
            visibleRange: editor.visibleRanges[0]
        };
    }

    /**
     * 构建代码上下文
     */
    static async buildCodeContext(options: {
        includeSelection?: boolean;
        includeCurrentFile?: boolean;
        includeSurrounding?: boolean;
        maxSurroundingLines?: number;
    } = {}): Promise<CodeContext> {
        const {
            includeSelection = true,
            includeCurrentFile = true,
            includeSurrounding = true,
            maxSurroundingLines = 20
        } = options;

        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return {};
        }

        const context: CodeContext = {
            language: editor.document.languageId
        };

        // 当前文件
        if (includeCurrentFile) {
            context.currentFile = this.getRelativePath(editor.document.uri);
        }

        // 光标位置
        context.cursorPosition = {
            line: editor.selection.active.line,
            column: editor.selection.active.character
        };

        // 选中的代码
        if (includeSelection && !editor.selection.isEmpty) {
            context.selectedCode = editor.document.getText(editor.selection);
        }

        // 周围的代码
        if (includeSurrounding) {
            context.surroundingCode = this.getSurroundingCode(
                editor.document,
                editor.selection.active,
                maxSurroundingLines
            );
        }

        // 工作区文件（最近打开的）
        const workspaceFiles = await this.getRecentWorkspaceFiles(5);
        context.workspaceFiles = workspaceFiles.map(uri => this.getRelativePath(uri));

        // 导入语句
        context.imports = this.extractImports(editor.document);

        return context;
    }

    /**
     * 获取选中代码
     */
    static getSelectedCode(): string | null {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            return null;
        }

        return editor.document.getText(editor.selection);
    }

    /**
     * 获取当前文件内容
     */
    static getCurrentFileContent(): string | null {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return null;
        }

        return editor.document.getText();
    }

    /**
     * 获取周围代码
     */
    private static getSurroundingCode(
        document: vscode.TextDocument,
        position: vscode.Position,
        maxLines: number
    ): string {
        const startLine = Math.max(0, position.line - maxLines);
        const endLine = Math.min(document.lineCount - 1, position.line + maxLines);
        
        const range = new vscode.Range(
            startLine, 0,
            endLine, document.lineAt(endLine).text.length
        );

        return document.getText(range);
    }

    /**
     * 提取导入语句
     */
    private static extractImports(document: vscode.TextDocument): string[] {
        const imports: string[] = [];
        const language = document.languageId;

        // 根据语言提取导入语句
        for (let i = 0; i < Math.min(document.lineCount, 50); i++) {
            const line = document.lineAt(i).text.trim();
            
            if (language === 'python') {
                if (line.startsWith('import ') || line.startsWith('from ')) {
                    imports.push(line);
                }
            } else if (language === 'typescript' || language === 'javascript') {
                if (line.startsWith('import ') || line.startsWith('require(')) {
                    imports.push(line);
                }
            }
        }

        return imports;
    }

    /**
     * 获取最近的工作区文件
     */
    private static async getRecentWorkspaceFiles(limit: number): Promise<vscode.Uri[]> {
        const recentFiles: vscode.Uri[] = [];
        
        // 获取所有打开的文档
        for (const document of vscode.workspace.textDocuments) {
            if (!document.isUntitled && document.uri.scheme === 'file') {
                recentFiles.push(document.uri);
                if (recentFiles.length >= limit) {
                    break;
                }
            }
        }

        return recentFiles;
    }

    /**
     * 获取相对路径
     */
    private static getRelativePath(uri: vscode.Uri): string {
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
        if (workspaceFolder) {
            return path.relative(workspaceFolder.uri.fsPath, uri.fsPath);
        }
        return uri.fsPath;
    }

    /**
     * 读取文件内容
     */
    static async readFile(uri: vscode.Uri): Promise<string> {
        try {
            const content = await vscode.workspace.fs.readFile(uri);
            return Buffer.from(content).toString('utf8');
        } catch (error) {
            Logger.error(`Failed to read file: ${uri.fsPath}`, error as Error);
            throw error;
        }
    }

    /**
     * 获取工作区根路径
     */
    static getWorkspaceRoot(): string {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            throw new Error('No workspace folder open');
        }
        return workspaceFolders[0].uri.fsPath;
    }
}

