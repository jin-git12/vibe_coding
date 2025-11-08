(function() {
    const vscode = acquireVsCodeApi();

    const messagesContainer = document.getElementById('messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading');
    const suggestionsContainer = document.getElementById('suggestions');
    const conversationTabsContainer = document.getElementById('conversation-tabs');

    let currentAssistantMessage = null;
    let currentStreamContent = '';
    let conversations = new Map(); // conversationId -> {title, messages}
    let activeConversationId = null;

    // 初始化：创建第一个会话
    function init() {
        createNewConversation();
    }

    // 创建新会话
    function createNewConversation() {
        const conversationId = generateId();
        const title = 'New Chat';
        
        conversations.set(conversationId, {
            id: conversationId,
            title: title,
            messages: [],
            createdAt: Date.now()
        });

        addConversationTab(conversationId, title);
        switchToConversation(conversationId);

        // 通知扩展创建新会话
        vscode.postMessage({
            type: 'newConversation',
            conversationId: conversationId
        });
    }

    // 添加会话标签
    function addConversationTab(conversationId, title) {
        const tab = document.createElement('div');
        tab.className = 'conversation-tab';
        tab.dataset.conversationId = conversationId;

        const titleSpan = document.createElement('span');
        titleSpan.className = 'tab-title';
        titleSpan.textContent = title;

        const closeBtn = document.createElement('span');
        closeBtn.className = 'tab-close codicon codicon-close';
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            closeConversation(conversationId);
        };

        tab.appendChild(titleSpan);
        tab.appendChild(closeBtn);
        tab.onclick = () => switchToConversation(conversationId);

        conversationTabsContainer.appendChild(tab);
    }

    // 切换会话
    function switchToConversation(conversationId) {
        if (activeConversationId === conversationId) return;

        activeConversationId = conversationId;

        // 更新标签激活状态
        document.querySelectorAll('.conversation-tab').forEach(tab => {
            if (tab.dataset.conversationId === conversationId) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        // 清空并加载会话消息
        messagesContainer.innerHTML = '';
        const conversation = conversations.get(conversationId);
        if (conversation && conversation.messages) {
            conversation.messages.forEach(msg => {
                addMessage(msg.role, msg.content, false);
            });
        }

        // 通知扩展切换会话
        vscode.postMessage({
            type: 'switchConversation',
            conversationId: conversationId
        });
    }

    // 关闭会话
    function closeConversation(conversationId) {
        const tab = conversationTabsContainer.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (tab) {
            tab.remove();
        }

        conversations.delete(conversationId);

        // 如果关闭的是当前会话，切换到其他会话
        if (activeConversationId === conversationId) {
            const remainingTabs = conversationTabsContainer.querySelectorAll('.conversation-tab');
            if (remainingTabs.length > 0) {
                const firstTab = remainingTabs[0];
                switchToConversation(firstTab.dataset.conversationId);
            } else {
                // 没有会话了，创建一个新的
                createNewConversation();
            }
        }

        // 通知扩展删除会话
        vscode.postMessage({
            type: 'deleteConversation',
            conversationId: conversationId
        });
    }

    // 生成唯一ID
    function generateId() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    // 自动调整输入框高度
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });

    // 发送按钮点击
    sendButton.addEventListener('click', sendMessage);

    // Enter 发送，Shift+Enter 换行
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 发送消息
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || !activeConversationId) return;

        // 保存消息到当前会话
        const conversation = conversations.get(activeConversationId);
        if (conversation) {
            conversation.messages.push({
                role: 'user',
                content: message,
                timestamp: Date.now()
            });

            // 更新标签标题（使用第一条消息）
            if (conversation.title === 'New Chat' && conversation.messages.length === 1) {
                const newTitle = message.substring(0, 20) + (message.length > 20 ? '...' : '');
                conversation.title = newTitle;
                const tab = conversationTabsContainer.querySelector(`[data-conversation-id="${activeConversationId}"]`);
                if (tab) {
                    tab.querySelector('.tab-title').textContent = newTitle;
                }
            }
        }

        vscode.postMessage({
            type: 'sendMessage',
            message: message,
            conversationId: activeConversationId
        });

        messageInput.value = '';
        messageInput.style.height = 'auto';
    }

    // 添加消息到界面
    function addMessage(role, content, saveToConversation = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '👤' : '🤖';

        const body = document.createElement('div');
        body.className = 'message-body';

        if (role === 'assistant') {
            // 渲染 Markdown
            body.innerHTML = renderMarkdown(content);
            
            // 添加代码块工具栏
            body.querySelectorAll('pre code').forEach((block) => {
                const pre = block.parentElement;
                if (!pre.querySelector('.code-toolbar')) {
                    const toolbar = createCodeToolbar(block.textContent);
                    pre.insertBefore(toolbar, block);
                }
            });
        } else {
            body.textContent = content;
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(body);
        messagesContainer.appendChild(messageDiv);

        // 滚动到底部
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // 保存到会话
        if (saveToConversation && activeConversationId) {
            const conversation = conversations.get(activeConversationId);
            if (conversation && role === 'assistant') {
                conversation.messages.push({
                    role: role,
                    content: content,
                    timestamp: Date.now()
                });
            }
        }

        return messageDiv;
    }

    // 创建代码工具栏
    function createCodeToolbar(code) {
        const toolbar = document.createElement('div');
        toolbar.className = 'code-toolbar';

        const copyBtn = document.createElement('button');
        copyBtn.className = 'code-toolbar-btn';
        copyBtn.innerHTML = '<span class="codicon codicon-copy"></span> Copy';
        copyBtn.onclick = () => {
            vscode.postMessage({
                type: 'copyCode',
                code: code
            });
        };

        const insertBtn = document.createElement('button');
        insertBtn.className = 'code-toolbar-btn';
        insertBtn.innerHTML = '<span class="codicon codicon-insert"></span> Insert';
        insertBtn.onclick = () => {
            vscode.postMessage({
                type: 'insertCode',
                code: code
            });
        };

        toolbar.appendChild(copyBtn);
        toolbar.appendChild(insertBtn);

        return toolbar;
    }

    // 简单的 Markdown 渲染
    function renderMarkdown(text) {
        // 代码块
        text = text.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`;
        });

        // 行内代码
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

        // 粗体
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // 斜体
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // 链接
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // 列表
        text = text.replace(/^\* (.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // 段落
        text = text.split('\n\n').map(p => {
            if (p.startsWith('<')) return p;
            return `<p>${p.replace(/\n/g, '<br>')}</p>`;
        }).join('');

        return text;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 显示加载状态
    function setLoading(loading) {
        if (loading) {
            loadingIndicator.classList.remove('hidden');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } else {
            loadingIndicator.classList.add('hidden');
        }
    }

    // 处理流式响应
    function handleStreamChunk(chunk, done) {
        if (!currentAssistantMessage) {
            currentAssistantMessage = addMessage('assistant', '', true);
            currentStreamContent = '';
        }

        currentStreamContent += chunk;
        const body = currentAssistantMessage.querySelector('.message-body');
        body.innerHTML = renderMarkdown(currentStreamContent);

        // 添加代码块工具栏
        body.querySelectorAll('pre code').forEach((block) => {
            const pre = block.parentElement;
            if (!pre.querySelector('.code-toolbar')) {
                const toolbar = createCodeToolbar(block.textContent);
                pre.insertBefore(toolbar, block);
            }
        });

        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        if (done) {
            currentAssistantMessage = null;
            currentStreamContent = '';
        }
    }

    // 清空聊天
    function clearChat() {
        messagesContainer.innerHTML = '';
        currentAssistantMessage = null;
        currentStreamContent = '';
    }

    // 显示建议
    function showSuggestions(suggestions) {
        suggestionsContainer.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-btn';
            btn.textContent = suggestion;
            btn.onclick = () => {
                messageInput.value = suggestion;
                messageInput.focus();
                suggestionsContainer.classList.add('hidden');
            };
            suggestionsContainer.appendChild(btn);
        });

        suggestionsContainer.classList.remove('hidden');
    }

    // 监听来自扩展的消息
    window.addEventListener('message', event => {
        const message = event.data;

        switch (message.type) {
            case 'addMessage':
                addMessage(message.message.role, message.message.content, true);
                break;

            case 'setLoading':
                setLoading(message.loading);
                break;

            case 'streamChunk':
                handleStreamChunk(message.chunk, message.done);
                break;

            case 'clearChat':
                clearChat();
                break;

            case 'showSuggestions':
                showSuggestions(message.suggestions);
                break;

            case 'createNewConversation':
                createNewConversation();
                break;
        }
    });

    // 通知扩展 WebView 已准备好
    vscode.postMessage({ type: 'ready' });

    // 初始化
    init();

    // 聚焦输入框
    messageInput.focus();
})();
