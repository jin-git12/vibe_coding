/**
 * 上下文相关类型定义
 */

import * as vscode from 'vscode';

export interface FileContext {
    uri: vscode.Uri;
    content: string;
    language: string;
    relativePath: string;
}

export interface WorkspaceContext {
    rootPath: string;
    files: FileContext[];
    activeFile?: FileContext;
    openFiles: FileContext[];
}

export interface EditorContext {
    document: vscode.TextDocument;
    selection?: vscode.Selection;
    position: vscode.Position;
    visibleRange: vscode.Range;
}

export interface ConversationMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
    context?: any;
}

export interface Conversation {
    id: string;
    title: string;
    messages: ConversationMessage[];
    createdAt: number;
    updatedAt: number;
}

export interface ContextItem {
    type: 'file' | 'selection' | 'function' | 'class';
    label: string;
    description?: string;
    uri?: vscode.Uri;
    range?: vscode.Range;
}

