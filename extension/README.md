# Vibe Coding - AI Code Assistant

AI-powered code assistant with deepagents, featuring intelligent sidebar chat and code analysis.

## ✨ Features

### 🤖 AI Chat Sidebar
- **Interactive Chat**: Dedicated sidebar for natural conversations with AI
- **Context-Aware**: Automatically includes your current file, selection, and workspace context
- **Streaming Responses**: Real-time responses for a smooth experience
- **Chat History**: Keep track of your conversations
- **Active Context View**: See what context the AI is using

### 💻 Code Operations

- **Generate Code**: Create code from natural language descriptions
- **Explain Code**: Get detailed explanations of selected code
- **Refactor Code**: AI-powered code refactoring
- **Review Code**: Get suggestions and identify potential issues
- **Semantic Search**: Find code by meaning, not just text

### 🎯 Key Highlights

- **🚀 Zero Configuration**: No need to manually start services
- **🔒 Local Processing**: Your code stays on your machine
- **⚡ Fast Responses**: Optimized for quick interactions
- **🎨 Beautiful UI**: Modern, VS Code-native interface
- **📊 Smart Context**: Intelligently selects relevant context

## 🚀 Getting Started

### Installation

1. Install the extension from VS Code Marketplace
2. Configure your DashScope API Key in settings
3. Open any workspace and start coding!

### Configuration

Open VS Code settings (`Ctrl+,`) and search for "Vibe Coding":

- **`vibe-coding.dashscopeApiKey`**: Your DashScope API Key (required)
- **`vibe-coding.model`**: Choose AI model (qwen-turbo/qwen-plus/qwen-max)
- **`vibe-coding.streamResponse`**: Enable streaming responses
- **`vibe-coding.maxContextFiles`**: Maximum context files to include

### Getting DashScope API Key

1. Visit [DashScope Console](https://dashscope.console.aliyun.com/)
2. Sign up or log in
3. Create an API key
4. Copy the key to VS Code settings

## 🎮 Usage

### Using the AI Chat Sidebar

1. Click the Vibe Coding icon in the activity bar
2. Type your question in the chat input
3. Get AI responses with code snippets
4. Click "Insert" to add code to your editor

### Commands

- **Generate Code**: `Ctrl+Shift+G` (or Cmd+Shift+G on Mac)
- **Open AI Chat**: `Ctrl+Shift+L` (or Cmd+Shift+L on Mac)
- **Explain Code**: Right-click on selected code → "Explain Code"
- **Refactor Code**: Right-click on selected code → "Refactor Code"
- **Review Code**: Right-click on selected code → "Review Code"

### Quick Tips

- Select code before asking questions for better context
- Use the Active Context view to see what AI sees
- Try semantic search to find code by description
- Use chat history to revisit previous conversations

## 📋 Requirements

- VS Code 1.80.0 or higher
- Python 3.11+ (for backend)
- uv (Python package manager)
- DashScope API Key

## 🏗️ Architecture

- **Frontend**: TypeScript VS Code Extension
- **Backend**: Python with deepagents
- **Communication**: JSON-RPC over stdin/stdout
- **AI Model**: Qwen (via DashScope)

## 🐛 Troubleshooting

### Extension not activating

1. Check if Python and uv are installed
2. Verify DashScope API Key is configured
3. Open Output panel → "Vibe Coding" for logs

### Chat not responding

1. Check status bar indicator
2. Ensure workspace is open
3. Verify API key has sufficient quota
4. Check logs for errors

### Performance issues

1. Reduce `maxContextFiles` setting
2. Close unnecessary editors
3. Restart VS Code

## 🤝 Contributing

Contributions are welcome! Please check our [GitHub repository](https://github.com/your-repo/vibe-coding) for more information.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with [deepagents](https://github.com/example/deepagents)
- Powered by [Qwen](https://dashscope.aliyuncs.com/)
- Uses [LangChain](https://python.langchain.com/)

## 📞 Support

- 📧 Email: support@vibe-coding.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/vibe-coding/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-repo/vibe-coding/discussions)

---

**Made with ❤️ by the Vibe Coding Team**

