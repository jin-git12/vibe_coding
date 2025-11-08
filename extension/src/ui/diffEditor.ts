/**
 * 差异对比编辑器
 * 显示代码变更的对比视图
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { Logger } from '../utils/logger';

export interface DiffContent {
    original: string;
    modified: string;
    language?: string;
    title?: string;
}

export class DiffEditor {
    /**
     * 显示差异对比
     */
    static async showDiff(
        originalContent: string,
        modifiedContent: string,
        title: string = 'Comparison',
        language: string = 'plaintext'
    ): Promise<void> {
        try {
            // 创建临时文档
            const originalUri = vscode.Uri.parse(`untitled:Original - ${title}`);
            const modifiedUri = vscode.Uri.parse(`untitled:Modified - ${title}`);

            // 打开差异编辑器
            await vscode.commands.executeCommand(
                'vscode.diff',
                originalUri.with({ scheme: 'vibe-coding', path: '/original' }),
                modifiedUri.with({ scheme: 'vibe-coding', path: '/modified' }),
                `${title} (Comparison)`,
                {
                    preview: true
                }
            );

            Logger.info(`Opened diff editor: ${title}`);
        } catch (error) {
            Logger.error('Failed to show diff', error as Error);
            throw error;
        }
    }

    /**
     * 显示文件差异
     */
    static async showFileDiff(
        originalPath: string,
        modifiedPath: string,
        title?: string
    ): Promise<void> {
        try {
            const originalUri = vscode.Uri.file(originalPath);
            const modifiedUri = vscode.Uri.file(modifiedPath);

            const displayTitle = title || 
                `${path.basename(originalPath)} ↔ ${path.basename(modifiedPath)}`;

            await vscode.commands.executeCommand(
                'vscode.diff',
                originalUri,
                modifiedUri,
                displayTitle
            );

            Logger.info(`Opened file diff: ${displayTitle}`);
        } catch (error) {
            Logger.error('Failed to show file diff', error as Error);
            throw error;
        }
    }

    /**
     * 显示文档的修改前后对比
     */
    static async showDocumentChanges(
        document: vscode.TextDocument,
        originalContent: string,
        title?: string
    ): Promise<void> {
        try {
            const currentContent = document.getText();
            const displayTitle = title || `${path.basename(document.fileName)} - Changes`;

            await DiffEditor.showDiff(
                originalContent,
                currentContent,
                displayTitle,
                document.languageId
            );
        } catch (error) {
            Logger.error('Failed to show document changes', error as Error);
            throw error;
        }
    }

    /**
     * 显示 AI 建议的代码变更
     */
    static async showAISuggestion(
        original: string,
        suggested: string,
        language: string = 'typescript',
        context?: string
    ): Promise<boolean> {
        try {
            const title = context ? `AI Suggestion - ${context}` : 'AI Suggestion';

            // 显示差异
            await DiffEditor.showDiff(original, suggested, title, language);

            // 询问用户是否接受
            const choice = await vscode.window.showInformationMessage(
                'Do you want to apply this AI suggestion?',
                { modal: true },
                'Accept',
                'Reject',
                'Edit'
            );

            switch (choice) {
                case 'Accept':
                    return true;
                case 'Edit':
                    // 打开编辑器让用户手动修改
                    await this.openForEditing(suggested, language);
                    return false;
                default:
                    return false;
            }
        } catch (error) {
            Logger.error('Failed to show AI suggestion', error as Error);
            return false;
        }
    }

    /**
     * 打开内容进行编辑
     */
    private static async openForEditing(
        content: string,
        language: string
    ): Promise<void> {
        const document = await vscode.workspace.openTextDocument({
            content,
            language
        });
        await vscode.window.showTextDocument(document);
    }

    /**
     * 应用文本差异
     */
    static async applyDiff(
        document: vscode.TextDocument,
        newContent: string
    ): Promise<boolean> {
        const edit = new vscode.WorkspaceEdit();
        const fullRange = new vscode.Range(
            document.positionAt(0),
            document.positionAt(document.getText().length)
        );
        
        edit.replace(document.uri, fullRange, newContent);
        
        const success = await vscode.workspace.applyEdit(edit);
        
        if (success) {
            Logger.info('Applied diff successfully');
        } else {
            Logger.error('Failed to apply diff');
        }
        
        return success;
    }

    /**
     * 比较两个文档
     */
    static async compareDocuments(
        doc1: vscode.TextDocument,
        doc2: vscode.TextDocument
    ): Promise<void> {
        await vscode.commands.executeCommand(
            'vscode.diff',
            doc1.uri,
            doc2.uri,
            `${path.basename(doc1.fileName)} ↔ ${path.basename(doc2.fileName)}`
        );
    }

    /**
     * 显示内联差异（在当前编辑器中）
     */
    static showInlineDiff(
        editor: vscode.TextEditor,
        changes: Array<{ range: vscode.Range; newText: string }>
    ): vscode.Disposable[] {
        const decorations: vscode.Disposable[] = [];

        // 创建装饰类型
        const addDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(0, 255, 0, 0.2)',
            isWholeLine: true
        });

        const deleteDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 0, 0, 0.2)',
            isWholeLine: true,
            textDecoration: 'line-through'
        });

        // 应用装饰
        const addRanges: vscode.Range[] = [];
        const deleteRanges: vscode.Range[] = [];

        changes.forEach(change => {
            if (change.newText) {
                addRanges.push(change.range);
            } else {
                deleteRanges.push(change.range);
            }
        });

        editor.setDecorations(addDecorationType, addRanges);
        editor.setDecorations(deleteDecorationType, deleteRanges);

        decorations.push(addDecorationType, deleteDecorationType);

        return decorations;
    }
}

/**
 * Diff 内容提供器
 */
export class DiffContentProvider implements vscode.TextDocumentContentProvider {
    private contents = new Map<string, string>();

    onDidChangeEmitter = new vscode.EventEmitter<vscode.Uri>();
    onDidChange = this.onDidChangeEmitter.event;

    provideTextDocumentContent(uri: vscode.Uri): string {
        return this.contents.get(uri.toString()) || '';
    }

    setContent(uri: vscode.Uri, content: string): void {
        this.contents.set(uri.toString(), content);
        this.onDidChangeEmitter.fire(uri);
    }

    dispose(): void {
        this.contents.clear();
        this.onDidChangeEmitter.dispose();
    }
}

