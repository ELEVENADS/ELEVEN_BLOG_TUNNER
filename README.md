# ELEVEN Blog Tuner

## 项目基础信息

- **项目名**：ELEVEN Blog Tuner
- **项目目的**：个人博客 AI 智能助手，根据个人笔记学习并生成相似文笔的文章
- **项目创建日期**：2026/4/15
- **项目作者**：ELEVEN(elven)

## 项目功能描述

### 核心功能
1. **风格学习**：从个人笔记中学习写作风格和特点
2. **文章生成**：根据学习到的风格生成新的文章
3. **文章发布**：支持将生成的文章发布到多种博客平台

### 技术特点
- **多 LLM 提供商支持**：集成 OpenAI 和本地 Ollama 模型
- **Agent 协作**：5 个核心 Agent 协同工作，实现复杂任务处理
- **RAG 增强**：检索增强生成，提高文章质量和相关性
- **记忆系统**：短期和长期记忆，保持对话上下文

## 技术栈

- **后端**：Python 3.10+, FastAPI
- **前端**：Vue3, Vite, TypeScript
- **AI 模型**：OpenAI API, Ollama 本地模型
- **向量数据库**：Chroma (计划中)
- **任务队列**：Celery (计划中)
- **缓存**：Redis (计划中)

## 项目结构

```
eleven_blog_tunner/
├── __init__.py              # 包初始化
├── main.py                  # FastAPI 应用入口
├── core/                    # 核心层 - 基础设施
│   ├── config.py            # 统一配置管理
│   └── exceptions.py        # 自定义异常类
├── agents/                  # Agent 层 - AI 智能体
│   ├── base_agent.py        # Agent 抽象基类
│   ├── boss_agent.py        # Boss Agent (任务调度)
│   ├── system_agent.py      # System Agent (系统查询)
│   ├── summary_agent.py     # Summary Agent (总结逻辑)
│   ├── writer_agent.py      # Writer Agent (文章撰写)
│   └── review_agent.py      # Review Agent (内容审查)
├── rag/                     # RAG 层 - 检索增强生成
│   ├── document_washer.py   # 文档清洗
│   ├── chunker.py           # 文档分块
│   ├── embedding.py         # 向量化服务
│   ├── searcher.py          # 向量检索
│   ├── reranker.py          # 结果重排序
│   └── pipeline.py          # RAG 处理管道
├── llm/                     # LLM 层 - 大语言模型
│   ├── base.py              # LLM 抽象基类
│   ├── openai_provider.py   # OpenAI 提供商实现
│   ├── local_provider.py    # 本地 Ollama 提供商实现
│   ├── factory.py           # LLM 工厂
│   └── memory.py            # 记忆管理
├── tools/                   # Tools 层 - 工具集
│   ├── registry.py          # 工具注册中心
│   ├── agent_caller.py      # Agent 调用器
│   ├── mcp_tools.py         # MCP 工具集管理
│   └── skill_manager.py     # Skill 管理器
├── api/                     # API 层 - HTTP 接口
│   └── routes/              # 路由定义
├── utils/                   # 工具层 - 通用工具
│   └── logger.py            # 日志系统
└── common/                  # Common 层 - 公共工具
    └── env_utils.py         # 环境变量加载工具
```

## 安装说明

### 开发环境

1. **克隆项目**
   ```bash
   git clone <项目仓库地址>
   cd ELEVEN_BLOG_TUNNER
   ```

2. **安装依赖**
   ```bash
   python3 -m pip install -e .
   ```

3. **配置环境变量**
   创建 `.env` 文件，配置以下参数：
   ```env
   # API 配置
   API_KEY=your_openai_api_key
   
   # LLM 配置
   LLM_PROVIDER=openai  # 或 local
   LLM_MODEL=gpt-4
   LLM_TEMPERATURE=0.7
   LLM_MAX_TOKENS=4096
   
   # 本地 LLM 配置
   LOCAL_LLM_BASE_URL=http://localhost:11434/api
   LOCAL_LLM_MODEL=qwen3.5:9b
   
   # RAG 配置
   VECTOR_DB_PATH=./data/vector_db
   EMBEDDING_MODEL=text-embedding-3-small
   CHUNK_SIZE=1000
   
   # 数据库
   DATABASE_URL=sqlite:///./data/app.db
   
   # 日志
   LOG_LEVEL=INFO
   ```

4. **运行开发服务器**
   ```bash
   python3 run.py
   ```

### 生产环境

使用 Gunicorn + Uvicorn Workers 部署：

```bash
gunicorn eleven_blog_tunner.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 开发进度

### 已完成
- ✅ 基础架构搭建
- ✅ 统一配置管理
- ✅ 异常处理体系
- ✅ 日志系统集成
- ✅ 数据库模型设计
- ✅ 单元测试框架
- ✅ OpenAI 提供商实现
- ✅ 本地 Ollama 提供商实现
- ✅ LLM 工厂模式优化

### 待完成
- 🔄 记忆系统实现
- 🔄 Agent 核心功能
- 🔄 RAG 与知识库
- 🔄 文章生成与发布
- 🔄 前端界面
- 🔄 测试与部署

## 使用方法

### LLM 模块使用

```python
from eleven_blog_tunner.llm.factory import LLMFactory

# 创建 LLM 实例
llm = LLMFactory.create(provider="openai")

# 发送对话
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
]

response = await llm.chat(messages)
print(response)

# 流式对话
async for chunk in llm.stream_chat(messages):
    print(chunk, end="")
```

### 测试 LLM 提供商

```bash
# 测试所有提供商
python3 -m eleven_blog_tunner.llm.factory

# 测试指定提供商
python3 -m eleven_blog_tunner.llm.factory local qwen3.5:9b
```

## 扩展指南

### 添加新的 LLM 提供商
1. 在 `llm/` 下创建新的 provider 文件
2. 继承 `BaseLLM` 实现 `chat()` 和 `stream_chat()`
3. 在 `factory.py` 的 `_providers` 中注册

### 添加新的 Agent
1. 在 `agents/` 下创建新的 agent 文件
2. 继承 `BaseAgent` 实现 `execute()`
3. 在 `AgentCaller` 中注册

### 添加新的 Tool
1. 使用 `@tool` 装饰器注册函数
2. 实现具体的工具逻辑
3. 自动通过 `ToolRegistry` 管理

## 贡献指南

1. **提交规范**
   - `feat`: 新功能
   - `fix`: 修复 bug
   - `docs`: 文档更新
   - `style`: 代码格式调整
   - `refactor`: 重构
   - `test`: 测试相关
   - `chore`: 构建/工具相关

2. **代码风格**
   - 使用 Black 格式化 (line-length: 100)
   - 使用 Ruff 进行代码检查
   - 类型注解必须完整
   - 文档字符串使用双引号

## 许可证

MIT License

## 联系方式

- 作者：ELEVEN(elven)
- 项目地址：[项目仓库地址](https://github.com/ELEVENADS/eleven_blog_turner)
