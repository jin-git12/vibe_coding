/**
 * Python 进程管理服务
 * 负责启动、监控和管理 Python Agent 进程
 */

import { spawn, ChildProcess } from 'child_process';
import * as readline from 'readline';
import * as path from 'path';
import * as fs from 'fs';
import * as vscode from 'vscode';
import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';

export enum ProcessStatus {
    Idle = 'idle',
    Starting = 'starting',
    Ready = 'ready',
    Busy = 'busy',
    Error = 'error',
    Stopped = 'stopped'
}

export class PythonProcessService extends EventEmitter {
    private process: ChildProcess | null = null;
    private status: ProcessStatus = ProcessStatus.Idle;
    private extensionPath: string;
    private workspacePath: string;
    private restartCount = 0;
    private lastRestartTime = 0;
    private readonly MAX_RESTARTS = 3;
    private readonly RESTART_WINDOW = 5 * 60 * 1000; // 5 minutes
    private healthCheckInterval: NodeJS.Timeout | null = null;

    constructor(extensionPath: string, workspacePath: string) {
        super();
        this.extensionPath = extensionPath;
        this.workspacePath = workspacePath;
    }

    /**
     * 启动 Python 进程
     */
    async start(): Promise<void> {
        if (this.status !== ProcessStatus.Idle && this.status !== ProcessStatus.Stopped) {
            Logger.warn(`Cannot start process: current status is ${this.status}`);
            return;
        }

        try {
            this.setStatus(ProcessStatus.Starting);
            Logger.info('Starting Python agent process...');

            const config = ConfigManager.getConfig();
            
            // Python 后端在扩展目录的 python_agents 子目录
            const pythonAgentsDir = path.join(this.extensionPath, 'python_agents');
            const pythonScriptPath = path.join(pythonAgentsDir, 'src', 'agent_server.py');
            
            // 检查文件是否存在
            if (!fs.existsSync(pythonScriptPath)) {
                throw new Error(`Python script not found: ${pythonScriptPath}. Please ensure the extension is installed correctly.`);
            }
            
            if (!fs.existsSync(pythonAgentsDir)) {
                throw new Error(`Python agents directory not found: ${pythonAgentsDir}`);
            }

            // 检查是否为开发模式（F5 调试）
            // 如果通过 F5 启动扩展，通常不会打包，所以 extensionPath 包含源码目录
            const isDevelopment = process.env.VSCODE_DEBUG_MODE === 'true' || 
                                  !this.extensionPath.endsWith('.vsix');
            
            Logger.info(`Development mode: ${isDevelopment}`);
            
            // 环境变量
            const env = {
                ...process.env,
                WORKSPACE_ROOT: this.workspacePath,
                DASHSCOPE_API_KEY: config.dashscopeApiKey || '',
                DASHSCOPE_BASE_URL: config.dashscopeBaseUrl || '',
                LLM_MODEL: config.model || 'qwen-turbo',  // ✅ 使用 LLM_MODEL（通用）
                DASHSCOPE_MODEL: config.model || 'qwen-turbo',  // 向后兼容
                LOG_LEVEL: isDevelopment ? 'DEBUG' : 'INFO',
                DEV_MODE: isDevelopment ? 'true' : 'false',  // 🔧 开发模式标志
                PYTHONUNBUFFERED: '1',
                PYTHONIOENCODING: 'utf-8',  // 🔧 强制使用 UTF-8 编码（解决 Windows GBK 问题）
                PYTHONUTF8: '1'  // 🔧 Python 3.7+ UTF-8 模式
            };

            // 使用 uv run 启动进程
            // 重要: 工作目录必须是 python_agents，使用相对路径
            Logger.info(`Starting Python process: uv run python src/agent_server.py`);
            Logger.info(`Working directory: ${pythonAgentsDir}`);
            Logger.info(`Extension path: ${this.extensionPath}`);
            
            // 检查 pyproject.toml 是否存在
            const pyprojectPath = path.join(pythonAgentsDir, 'pyproject.toml');
            if (fs.existsSync(pyprojectPath)) {
                Logger.info(`Found pyproject.toml: ${pyprojectPath}`);
            } else {
                Logger.warn(`pyproject.toml not found at: ${pyprojectPath}`);
            }
            
            this.process = spawn('uv', ['run', 'python', 'src/agent_server.py'], {
                cwd: pythonAgentsDir,  // 关键修复: 工作目录改为 python_agents
                env,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            Logger.info(`Python process spawned with PID: ${this.process.pid}`);
            Logger.info('Waiting for server.ready notification...');

            // 设置事件监听
            this.setupProcessHandlers();

            // 等待就绪信号
            Logger.info('Waiting for Python process to be ready...');
            await this.waitForReady();
            Logger.info('Python process is ready!');

            // 启动健康检查
            this.startHealthCheck();

            Logger.info('Python agent process started successfully');
            
            // 显示成功消息
            const vscode = require('vscode');
            vscode.window.showInformationMessage('Vibe Coding is ready! 🚀');
        } catch (error) {
            this.setStatus(ProcessStatus.Error);
            Logger.error('Failed to start Python process', error as Error);
            throw error;
        }
    }

    /**
     * 停止 Python 进程
     */
    async stop(): Promise<void> {
        if (!this.process || this.status === ProcessStatus.Stopped) {
            return;
        }

        Logger.info('Stopping Python agent process...');

        // 停止健康检查
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }

        try {
            // 尝试优雅关闭
            this.emit('shutdown-request');
            
            // 等待最多 5 秒
            const stopped = await this.waitForExit(5000);
            
            if (!stopped) {
                Logger.warn('Process did not stop gracefully, killing...');
                this.process?.kill('SIGKILL');
            }
        } catch (error) {
            Logger.error('Error stopping process', error as Error);
            this.process?.kill('SIGKILL');
        }

        this.process = null;
        this.setStatus(ProcessStatus.Stopped);
        Logger.info('Python agent process stopped');
    }

    /**
     * 重启进程
     */
    async restart(): Promise<void> {
        Logger.info('Restarting Python agent process...');
        
        // 检查重启频率
        const now = Date.now();
        if (now - this.lastRestartTime < this.RESTART_WINDOW) {
            this.restartCount++;
            if (this.restartCount > this.MAX_RESTARTS) {
                const error = new Error('Too many restarts in short time, giving up');
                Logger.error(error.message, error);
                vscode.window.showErrorMessage(
                    'Vibe Coding: Python agent process keeps crashing. Please check the logs.'
                );
                throw error;
            }
        } else {
            this.restartCount = 0;
        }
        
        this.lastRestartTime = now;

        await this.stop();
        
        // 指数退避
        const delay = Math.min(1000 * Math.pow(2, this.restartCount), 10000);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        await this.start();
    }

    /**
     * 发送数据到 Python 进程
     */
    send(data: any): void {
        if (!this.process || !this.process.stdin) {
            throw new Error('Process not running or stdin not available');
        }

        const json = JSON.stringify(data);
        Logger.debug('Sending to Python:', { data: json.substring(0, 200) });
        this.process.stdin.write(json + '\n');
    }

    /**
     * 获取进程状态
     */
    getStatus(): ProcessStatus {
        return this.status;
    }

    /**
     * 检查进程是否健康
     */
    isHealthy(): boolean {
        return this.status === ProcessStatus.Ready || this.status === ProcessStatus.Busy;
    }

    private setupProcessHandlers(): void {
        if (!this.process) {
            return;
        }

        // 处理 stdout（JSON-RPC 响应）
        const rl = readline.createInterface({
            input: this.process.stdout!,
            crlfDelay: Infinity
        });

        rl.on('line', (line) => {
            line = line.trim();
            if (!line) {
                return;
            }
            
            Logger.info(`[Python stdout] ${line.substring(0, 200)}${line.length > 200 ? '...' : ''}`);
            
            try {
                const message = JSON.parse(line);
                
                // 如果是通知（没有 id）
                if (!message.id && message.method) {
                    Logger.info(`Received notification: ${message.method}`);
                    this.emit('notification', message.method, message.params);
                } else {
                    // 如果是响应（有 id）
                    Logger.info(`Received response with id: ${message.id}`);
                    this.emit('response', message);
                }
            } catch (error) {
                Logger.error('Failed to parse JSON from Python:', error as Error, { line });
            }
        });

        // 处理 stderr（日志）
        this.process.stderr!.on('data', (data) => {
            const text = data.toString().trim();
            if (text) {
                Logger.info(`[Python stderr] ${text}`);
            }
            
            // 检查是否有致命错误或启动失败
            if (text.includes('FATAL') || text.includes('CRITICAL') || text.includes('Traceback')) {
                Logger.error('Python process error detected', new Error(text));
            }
            
            // 检查常见错误
            if (text.includes('ModuleNotFoundError') || text.includes('ImportError')) {
                Logger.error('Python dependencies missing. Run: cd python_agents && uv sync');
            }
            if (text.includes('command not found') || text.includes('is not recognized')) {
                Logger.error('uv command not found. Make sure uv is installed and in PATH.');
            }
        });

        // 处理进程退出
        this.process.on('exit', (code, signal) => {
            Logger.warn(`Python process exited with code ${code}, signal ${signal}`);
            this.setStatus(ProcessStatus.Error);
            
            if (code !== 0) {
                // 异常退出，尝试重启
                this.restart().catch(err => {
                    Logger.error('Failed to restart after crash', err);
                });
            }
        });

        // 处理进程错误
        this.process.on('error', (error) => {
            Logger.error('Python process error', error);
            this.setStatus(ProcessStatus.Error);
        });
    }

    private async waitForReady(): Promise<void> {
        return new Promise((resolve, reject) => {
            // 增加超时时间到 120 秒（首次运行可能需要安装依赖）
            const timeout = setTimeout(() => {
                const error = new Error('Timeout waiting for Python process to be ready (120s). Check logs for details.');
                Logger.error('Python process ready timeout', error);
                Logger.info('This usually means:');
                Logger.info('1. First run: uv is installing Python dependencies (may take 1-2 minutes)');
                Logger.info('2. Network slow: dependency download is taking longer');
                Logger.info('3. uv command not found in PATH');
                Logger.info('4. Python process crashed on startup - check stderr above');
                Logger.info('Try: Close VS Code completely and reopen, or run "uv sync" manually in python_agents folder');
                reject(error);
            }, 120000);

            const handler = (method: string) => {
                if (method === 'server.ready') {
                    Logger.info('Received server.ready notification');
                    clearTimeout(timeout);
                    this.removeListener('notification', handler);
                    this.setStatus(ProcessStatus.Ready);
                    resolve();
                }
            };

            this.on('notification', handler);
        });
    }

    private async waitForExit(timeoutMs: number): Promise<boolean> {
        return new Promise((resolve) => {
            const timeout = setTimeout(() => resolve(false), timeoutMs);
            
            this.process?.once('exit', () => {
                clearTimeout(timeout);
                resolve(true);
            });
        });
    }

    private startHealthCheck(): void {
        this.healthCheckInterval = setInterval(() => {
            if (this.status === ProcessStatus.Ready || this.status === ProcessStatus.Busy) {
                this.emit('health-check-request');
            }
        }, 30000); // 每 30 秒检查一次
    }

    private setStatus(status: ProcessStatus): void {
        const oldStatus = this.status;
        this.status = status;
        Logger.debug(`Process status changed: ${oldStatus} -> ${status}`);
        this.emit('status-change', status, oldStatus);
    }
}

