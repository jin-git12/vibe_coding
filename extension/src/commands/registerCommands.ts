/**
 * 命令注册中心
 */

import * as vscode from 'vscode';
import { AgentBridge } from '../services/agentBridge';
import { ChatViewProvider } from '../ui/chatViewProvider';
import { ContextService } from '../services/contextService';
import { Logger } from '../utils/logger';

export function registerCommands(
    context: vscode.ExtensionContext,
    agentBridge: AgentBridge,
    chatViewProvider: ChatViewProvider,
    extensionUri: vscode.Uri
): void {
    // 生成代码
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.generateCode', async () => {
            await generateCodeCommand(agentBridge);
        })
    );

    // 解释代码
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.explainCode', async () => {
            await explainCodeCommand(agentBridge);
        })
    );

    // 重构代码
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.refactorCode', async () => {
            await refactorCodeCommand(agentBridge);
        })
    );

    // 审查代码
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.reviewCode', async () => {
            await reviewCodeCommand(agentBridge);
        })
    );

    // 搜索代码
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.searchCode', async () => {
            await searchCodeCommand(agentBridge);
        })
    );

    // 打开聊天（侧边栏）
    context.subscriptions.push(
        vscode.commands.registerCommand('vibe-coding.openChat', async () => {
            await vscode.commands.executeCommand('vibe-coding-chat.focus');
        })
    );

    // 注意: newConversation, showHistory, showChatMenu 命令已在 setupUI() 中注册
    // 这些命令需要在 UI 初始化后立即可用，所以移到了 setupUI 函数中

    Logger.info('All commands registered');
}

/**
 * 生成代码命令
 */
async function generateCodeCommand(agentBridge: AgentBridge): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const prompt = await vscode.window.showInputBox({
        prompt: 'What code would you like to generate?',
        placeHolder: 'e.g., Create a calculator class with add and subtract methods'
    });

    if (!prompt) {
        return;
    }

    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
    statusBarItem.text = '$(sync~spin) Generating code...';
    statusBarItem.show();

    try {
        const context = await ContextService.buildCodeContext({
            includeCurrentFile: true,
            includeSurrounding: true
        });

        const result = await agentBridge.generateCode({
            prompt,
            language: editor.document.languageId,
            context
        });

        // 插入代码到光标位置
        await editor.edit(editBuilder => {
            editBuilder.insert(editor.selection.active, result.code);
        });

        // 显示解释（如果有）
        if (result.explanation) {
            vscode.window.showInformationMessage(result.explanation);
        }

        Logger.info('Code generated successfully');
    } catch (error) {
        Logger.error('Failed to generate code', error as Error);
        vscode.window.showErrorMessage(`Failed to generate code: ${(error as Error).message}`);
    } finally {
        statusBarItem.dispose();
    }
}

/**
 * 解释代码命令
 */
async function explainCodeCommand(agentBridge: AgentBridge): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const selectedCode = ContextService.getSelectedCode();
    if (!selectedCode) {
        vscode.window.showErrorMessage('Please select some code to explain');
        return;
    }

    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
    statusBarItem.text = '$(sync~spin) Explaining code...';
    statusBarItem.show();

    try {
        const context = await ContextService.buildCodeContext({
            includeSelection: true,
            includeCurrentFile: true
        });

        const result = await agentBridge.explainCode({
            code: selectedCode,
            language: editor.document.languageId,
            context,
            detailLevel: 'detailed'
        });

        // 显示在新面板
        const panel = vscode.window.createWebviewPanel(
            'codeExplanation',
            'Code Explanation',
            vscode.ViewColumn.Beside,
            {}
        );

        panel.webview.html = getExplanationHtml(result);

        Logger.info('Code explained successfully');
    } catch (error) {
        Logger.error('Failed to explain code', error as Error);
        vscode.window.showErrorMessage(`Failed to explain code: ${(error as Error).message}`);
    } finally {
        statusBarItem.dispose();
    }
}

/**
 * 重构代码命令
 */
async function refactorCodeCommand(agentBridge: AgentBridge): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const selectedCode = ContextService.getSelectedCode();
    if (!selectedCode) {
        vscode.window.showErrorMessage('Please select some code to refactor');
        return;
    }

    const instructions = await vscode.window.showInputBox({
        prompt: 'How would you like to refactor this code?',
        placeHolder: 'e.g., Extract repeated logic into a function'
    });

    if (!instructions) {
        return;
    }

    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
    statusBarItem.text = '$(sync~spin) Refactoring code...';
    statusBarItem.show();

    try {
        const context = await ContextService.buildCodeContext({
            includeSelection: true,
            includeCurrentFile: true
        });

        const result = await agentBridge.refactorCode({
            code: selectedCode,
            language: editor.document.languageId,
            instructions,
            context
        });

        // 替换选中的代码
        await editor.edit(editBuilder => {
            editBuilder.replace(editor.selection, result.refactoredCode);
        });

        // 显示变更说明
        if (result.changes && result.changes.length > 0) {
            const message = result.changes.map(c => c.reason).join('\n');
            vscode.window.showInformationMessage(`Refactored: ${message}`);
        }

        Logger.info('Code refactored successfully');
    } catch (error) {
        Logger.error('Failed to refactor code', error as Error);
        vscode.window.showErrorMessage(`Failed to refactor code: ${(error as Error).message}`);
    } finally {
        statusBarItem.dispose();
    }
}

/**
 * 审查代码命令
 */
async function reviewCodeCommand(agentBridge: AgentBridge): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const selectedCode = ContextService.getSelectedCode() || ContextService.getCurrentFileContent();
    if (!selectedCode) {
        vscode.window.showErrorMessage('No code to review');
        return;
    }

    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
    statusBarItem.text = '$(sync~spin) Reviewing code...';
    statusBarItem.show();

    try {
        const context = await ContextService.buildCodeContext({
            includeSelection: true,
            includeCurrentFile: true
        });

        const result = await agentBridge.reviewCode({
            code: selectedCode,
            language: editor.document.languageId,
            context
        });

        // 显示审查结果
        const panel = vscode.window.createWebviewPanel(
            'codeReview',
            'Code Review',
            vscode.ViewColumn.Beside,
            {}
        );

        panel.webview.html = getReviewHtml(result);

        Logger.info('Code reviewed successfully');
    } catch (error) {
        Logger.error('Failed to review code', error as Error);
        vscode.window.showErrorMessage(`Failed to review code: ${(error as Error).message}`);
    } finally {
        statusBarItem.dispose();
    }
}

/**
 * 搜索代码命令
 */
async function searchCodeCommand(agentBridge: AgentBridge): Promise<void> {
    const query = await vscode.window.showInputBox({
        prompt: 'What would you like to search for?',
        placeHolder: 'e.g., functions that handle user authentication'
    });

    if (!query) {
        return;
    }

    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
    statusBarItem.text = '$(sync~spin) Searching...';
    statusBarItem.show();

    try {
        const workspaceRoot = ContextService.getWorkspaceRoot();

        const result = await agentBridge.searchCode({
            query,
            workspaceRoot,
            maxResults: 10
        });

        // 显示搜索结果
        if (result.results.length === 0) {
            vscode.window.showInformationMessage('No results found');
        } else {
            const items = result.results.map(r => ({
                label: `$(file) ${r.file}:${r.line}`,
                description: r.codeSnippet.substring(0, 100),
                detail: `Relevance: ${(r.relevanceScore * 100).toFixed(0)}%`,
                file: r.file,
                line: r.line
            }));

            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: `Found ${result.totalMatches} matches`
            });

            if (selected) {
                const uri = vscode.Uri.file(selected.file);
                const document = await vscode.workspace.openTextDocument(uri);
                await vscode.window.showTextDocument(document, {
                    selection: new vscode.Range(selected.line - 1, 0, selected.line - 1, 0)
                });
            }
        }

        Logger.info(`Search completed: ${result.totalMatches} matches`);
    } catch (error) {
        Logger.error('Failed to search code', error as Error);
        vscode.window.showErrorMessage(`Failed to search code: ${(error as Error).message}`);
    } finally {
        statusBarItem.dispose();
    }
}

/**
 * 生成解释的 HTML
 */
function getExplanationHtml(result: any): string {
    return `<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            padding: 20px;
            line-height: 1.6;
        }
        h1 { color: var(--vscode-textLink-foreground); }
        h2 { margin-top: 20px; }
        .section { margin: 20px 0; }
        code {
            background: var(--vscode-textCodeBlock-background);
            padding: 2px 6px;
            border-radius: 3px;
        }
        ul { padding-left: 20px; }
    </style>
</head>
<body>
    <h1>Code Explanation</h1>
    
    <div class="section">
        <h2>Summary</h2>
        <p>${result.summary}</p>
    </div>
    
    <div class="section">
        <h2>Detailed Explanation</h2>
        <p>${result.detailedExplanation}</p>
    </div>
    
    ${result.keyConcepts ? `
        <div class="section">
            <h2>Key Concepts</h2>
            <ul>
                ${result.keyConcepts.map((c: string) => `<li>${c}</li>`).join('')}
            </ul>
        </div>
    ` : ''}
    
    ${result.complexity ? `
        <div class="section">
            <h2>Complexity</h2>
            <p>${result.complexity}</p>
        </div>
    ` : ''}
</body>
</html>`;
}

/**
 * 生成审查的 HTML
 */
function getReviewHtml(result: any): string {
    return `<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            padding: 20px;
            line-height: 1.6;
        }
        h1 { color: var(--vscode-textLink-foreground); }
        .issue {
            margin: 15px 0;
            padding: 10px;
            border-left: 3px solid;
            background: var(--vscode-editor-background);
        }
        .error { border-left-color: var(--vscode-editorError-foreground); }
        .warning { border-left-color: var(--vscode-editorWarning-foreground); }
        .info { border-left-color: var(--vscode-editorInfo-foreground); }
        .severity {
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>Code Review</h1>
    
    <p><strong>${result.summary}</strong></p>
    
    <h2>Issues</h2>
    ${result.issues.map((issue: any) => `
        <div class="issue ${issue.severity}">
            <div class="severity">${issue.severity}</div>
            <p>${issue.message}</p>
            ${issue.suggestion ? `<p><em>Suggestion: ${issue.suggestion}</em></p>` : ''}
        </div>
    `).join('')}
    
    ${result.suggestions.length > 0 ? `
        <h2>General Suggestions</h2>
        <ul>
            ${result.suggestions.map((s: string) => `<li>${s}</li>`).join('')}
        </ul>
    ` : ''}
</body>
</html>`;
}

