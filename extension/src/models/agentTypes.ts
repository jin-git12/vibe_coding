/**
 * Agent 相关类型定义
 */

export interface CodeContext {
    currentFile?: string;
    cursorPosition?: { line: number; column: number };
    surroundingCode?: string;
    workspaceFiles?: string[];
    selectedCode?: string;
    language?: string;
    imports?: string[];
}

export interface GenerateCodeParams {
    prompt: string;
    language: string;
    context: CodeContext;
    options?: {
        style?: string;
        includeTests?: boolean;
        includeDocs?: boolean;
    };
}

export interface GenerateCodeResult {
    code: string;
    explanation?: string;
    suggestions?: string[];
}

export interface ExplainCodeParams {
    code: string;
    language: string;
    context?: CodeContext;
    detailLevel?: 'brief' | 'detailed' | 'comprehensive';
}

export interface ExplainCodeResult {
    summary: string;
    detailedExplanation: string;
    keyConcepts?: string[];
    complexity?: string;
    potentialIssues?: string[];
}

export interface RefactorCodeParams {
    code: string;
    language: string;
    refactorType?: string;
    instructions: string;
    context?: CodeContext;
}

export interface RefactorCodeResult {
    refactoredCode: string;
    changes: Array<{
        type: string;
        oldCode: string;
        newCode: string;
        reason: string;
    }>;
    diff?: string;
}

export interface ReviewCodeParams {
    code: string;
    language: string;
    context?: CodeContext;
}

export interface ReviewCodeResult {
    summary: string;
    issues: Array<{
        severity: 'error' | 'warning' | 'info';
        message: string;
        line?: number;
        suggestion?: string;
    }>;
    suggestions: string[];
}

export interface SearchCodeParams {
    query: string;
    workspaceRoot: string;
    filePatterns?: string[];
    maxResults?: number;
}

export interface SearchCodeResult {
    results: Array<{
        file: string;
        line: number;
        codeSnippet: string;
        relevanceScore: number;
        context?: string;
    }>;
    totalMatches: number;
}

export interface ChatParams {
    message: string;
    conversationId: string;
    context?: CodeContext;
    stream?: boolean;
}

export interface ChatResult {
    conversationId: string;
    response: string;
    suggestions?: string[];
}

export interface ChatStreamChunk {
    conversationId: string;
    chunk: string;
    done: boolean;
}

