# Agent 系统说明文档

## 1. 系统概述

ELEVEN Blog Tuner 项目的 Agent 系统是一个智能协作网络，由多个专门的 Agent 组成，负责不同的任务，通过统一的通信协议进行协作，共同完成博客写作的全流程。

### 1.1 系统架构

系统采用分层架构设计，其中 **Gateway 层** 作为控制系统的核心层，负责：
- 24小时运行和自动处理任务链
- 接收 API 请求并处理
- 与 BossAgent 和 SystemAgent 深度绑定
- 管理系统状态和任务进度
- 作为用户与 Agent 系统的桥梁

### 1.1 核心价值

- **模块化设计**：每个 Agent 专注于特定功能，职责清晰
- **智能协作**：通过 Agent 通信协议实现高效协作
- **可扩展性**：支持添加新的 Agent 和工具
- **灵活性**：可根据任务类型动态调整工作流程

## 2. 架构设计

### 2.1 整体架构

```
用户
  ↓
AgentProtocol (通信协议)
  ↓
┌──────────────────────────────────────┐
│ BossAgent (任务调度中心)             │
├──────────────────────────────────────┤
│ ┌────────────┐ ┌─────────────┐      │
│ │SystemAgent│ │SummaryAgent │      │
│ └────────────┘ └─────────────┘      │
│ ┌────────────┐ ┌─────────────┐      │
│ │ WriterAgent│ │ReviewAgent  │      │
│ └────────────┘ └─────────────┘      │
└──────────────────────────────────────┘
```

### 2.2 BaseAgent 基座

所有 Agent 都继承自 `BaseAgent` 基类，提供以下核心功能：

- **LLM 集成**：通过 `call_llm` 方法调用大语言模型
- **记忆系统**：通过 `add_to_memory` 管理对话历史
- **工具系统**：通过 `add_tool` 和 `call_tool` 管理工具
- **子 Agent 调用**：通过 `call_agent` 调用其他 Agent
- **消息构建**：通过 `build_messages` 构建标准消息格式

## 3. 核心 Agent 介绍

### 3.1 BossAgent

**职责**：统筹系统任务调度和信息返回

**核心功能**：
- 任务类型分析和分类
- 协调其他 Agent 完成复杂任务
- 监控任务执行状态
- 整合结果返回给用户

**工作流程**：
1. 接收用户请求
2. 分析任务类型（文章生成、风格查询、文章审查等）
3. 调用相应的 Agent 完成子任务
4. 整合结果并返回

**示例**：
```python
from eleven_blog_tunner.agents import BossAgent, AgentContext

boss_agent = BossAgent()
context = AgentContext(
    user_input="请写一篇关于人工智能的文章"
)
result = await boss_agent.execute(context)
print(result)
```

### 3.2 SystemAgent

**职责**：系统内任务状态查询和各种参数返回

**核心功能**：
- 风格配置查询
- 系统参数获取
- 任务状态查询
- 记忆数据检索
- 与 **Gateway 层深度绑定**：为 Gateway 层提供系统配置和状态信息

**与 Gateway 层的关系**：
- Gateway 层通过 SystemAgent 获取系统配置和状态
- SystemAgent 作为系统信息的中央提供者
- 两者紧密协作，确保 Gateway 层能够实时获取系统状态
- SystemAgent 响应 Gateway 层的系统查询请求

**工具**：
- `get_style_config`：获取风格配置
- `get_system_config`：获取系统配置
- `query_memory`：查询记忆数据
- `get_task_status`：获取任务状态

**示例**：
```python
from eleven_blog_tunner.agents import SystemAgent, AgentContext

system_agent = SystemAgent()
context = AgentContext(
    user_input="获取当前风格配置"
)
result = await system_agent.execute(context)
print(result)
```

### 3.3 SummaryAgent

**职责**：总结类工作，比如总结上下文、总结文章风格

**核心功能**：
- 上下文分析和总结
- 文章风格提取
- 对话历史压缩
- 文章大纲生成

**工具**：
- `summarize_context`：总结上下文
- `extract_style`：提取风格特征
- `compress_history`：压缩历史记录
- `generate_outline`：生成文章大纲

**示例**：
```python
from eleven_blog_tunner.agents import SummaryAgent, AgentContext

summary_agent = SummaryAgent()
context = AgentContext(
    user_input="分析这篇文章的风格：..."
)
result = await summary_agent.execute(context)
print(result)
```

### 3.4 WriterAgent

**职责**：文章的撰写，通过固定的风格和例子调用工具完成文章

**核心功能**：
- 文章大纲生成
- 章节内容撰写
- 文章润色和优化
- 参考资料搜索

**工具**：
- `generate_outline`：生成文章大纲
- `write_section`：撰写章节内容
- `polish_content`：润色文章
- `search_reference`：搜索参考资料

**示例**：
```python
from eleven_blog_tunner.agents import WriterAgent, AgentContext

writer_agent = WriterAgent()
context = AgentContext(
    user_input="写一篇关于Python的文章",
    metadata={
        "style_config": {"writing_style": "简洁专业"},
        "context_analysis": "Python是一种流行的编程语言"
    }
)
result = await writer_agent.execute(context)
print(result)
```

### 3.5 ReviewAgent

**职责**：审查文章质量和是否违规

**核心功能**：
- 内容质量评分
- 违规内容检测
- 风格一致性检查
- 修改建议生成

**工具**：
- `check_quality`：检查文章质量
- `check_violation`：检查违规内容
- `check_style_consistency`：检查风格一致性
- `generate_suggestions`：生成修改建议

**示例**：
```python
from eleven_blog_tunner.agents import ReviewAgent, AgentContext

review_agent = ReviewAgent()
context = AgentContext(
    user_input="[文章内容]..."
)
result = await review_agent.execute(context)
print(result)
```

## 4. Agent 通信协议

### 4.1 核心组件

- **AgentProtocol**：Agent 通信的核心协议，管理 Agent 间的通信
- **AgentCallChain**：管理 Agent 调用链，记录调用历史
- **TaskContext**：任务上下文，跟踪任务执行状态
- **AgentMessage**：Agent 间传递的消息结构

### 4.2 通信流程

1. **消息发送**：通过 `send_message` 发送消息
2. **消息路由**：通过 `route_message` 路由消息到目标 Agent
3. **任务执行**：通过 `execute_task` 执行完整任务流程
4. **直接调用**：通过 `call_agent` 直接调用单个 Agent

### 4.3 标准消息格式

```python
AgentMessage(
    message_id="uuid",
    sender="BossAgent",
    receiver="SystemAgent",
    content="获取风格配置",
    message_type=MessageType.REQUEST,
    metadata={"task_id": "123"}
)
```

### 4.4 任务执行流程

```python
from eleven_blog_tunner.agents import get_protocol

protocol = get_protocol()

# 执行完整任务流程
result = await protocol.execute_task(
    task="文章生成",
    initial_input="写一篇关于人工智能的文章"
)

# 直接调用单个 Agent
result = await protocol.call_agent(
    caller="BossAgent",
    callee="WriterAgent",
    input_data="写一篇关于Python的文章"
)
```

## 5. 配置与使用

### 5.1 配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `llm_provider` | LLM 提供商 | "openai" |
| `use_memory` | 是否使用记忆 | `True` |
| `max_history` | 最大历史记录数 | `10` |

### 5.2 初始化 Agent

```python
from eleven_blog_tunner.agents import BossAgent

# 基本初始化
boss_agent = BossAgent()

# 自定义配置
boss_agent = BossAgent(
    llm_provider="local",
    use_memory=True,
    max_history=20
)
```

### 5.3 工具注册

```python
from eleven_blog_tunner.agents import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("CustomAgent", "自定义Agent", AgentType.SUMMARY)
        self.add_tool("custom_tool", self._custom_tool)
    
    def _custom_tool(self, param):
        return f"处理参数: {param}"
```

## 6. 最佳实践

### 6.1 任务分配策略

- **文章生成**：BossAgent → SystemAgent → SummaryAgent → WriterAgent → ReviewAgent
- **风格查询**：BossAgent → SystemAgent
- **文章审查**：BossAgent → ReviewAgent
- **系统状态**：BossAgent → SystemAgent

### 6.2 错误处理

```python
from eleven_blog_tunner.agents import get_protocol

protocol = get_protocol()
try:
    result = await protocol.execute_task(
        task="文章生成",
        initial_input="写一篇关于AI的文章"
    )
except Exception as e:
    print(f"任务执行失败: {e}")
```

### 6.3 性能优化

- **记忆管理**：定期清理不需要的记忆
- **工具选择**：只加载必要的工具
- **并行执行**：对于独立任务使用异步并行执行
- **缓存策略**：缓存频繁使用的结果

## 7. 扩展与定制

### 7.1 添加新 Agent

1. 继承 `BaseAgent` 类
2. 实现 `execute` 方法
3. 注册到 `AgentProtocol`

```python
from eleven_blog_tunner.agents import BaseAgent, AgentType, get_protocol

class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__("NewAgent", "新功能Agent", AgentType.SUMMARY)
    
    async def execute(self, context):
        return "新Agent执行结果"

# 注册到协议
protocol = get_protocol()
protocol.register_agent("NewAgent", NewAgent())
```

### 7.2 定制工具

```python
from eleven_blog_tunner.agents import BossAgent

boss_agent = BossAgent()

# 定义自定义工具
def custom_tool(param1, param2):
    return f"处理: {param1} 和 {param2}"

# 注册工具
boss_agent.add_tool("custom_tool", custom_tool)

# 使用工具
result = await boss_agent.call_tool("custom_tool", param1="value1", param2="value2")
```

## 8. 故障排除

### 8.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|----------|
| Agent 未找到 | 未注册 Agent | 检查 `register_agent` 调用 |
| LLM 调用失败 | API 密钥错误 | 检查配置文件中的 API 密钥 |
| 记忆系统未初始化 | 依赖未安装 | 安装 chromadb 和 ollama |
| 工具调用失败 | 工具未注册 | 检查 `add_tool` 调用 |

### 8.2 日志与监控

- **调用历史**：通过 `get_call_history()` 查看调用历史
- **任务状态**：通过 `get_task_context()` 查看任务状态
- **Agent 状态**：检查 Agent 的 `llm` 和 `memory` 属性

## 9. 示例场景

### 9.1 通过 Gateway 层发起任务

```python
from eleven_blog_tunner.gateway.task_manager import TaskManager

# 创建任务管理器
task_manager = TaskManager()

# 发起文章生成任务
task_id = await task_manager.create_task(
    task_type="article_generation",
    input_data="写一篇关于人工智能发展趋势的文章",
    user_id="user123"
)

print(f"任务创建成功，任务ID: {task_id}")

# 监控任务状态
while True:
    status = await task_manager.get_task_status(task_id)
    print(f"任务状态: {status['status']}")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    await asyncio.sleep(2)

# 获取任务结果
if status['status'] == 'completed':
    result = await task_manager.get_task_result(task_id)
    print("任务结果:")
    print(result)
else:
    print(f"任务失败: {status['error']}")
```

### 9.2 完整文章生成流程

```python
from eleven_blog_tunner.agents import get_protocol

protocol = get_protocol()

# 执行完整的文章生成流程
result = await protocol.execute_task(
    task="文章生成",
    initial_input="写一篇关于人工智能发展趋势的文章",
    agent_sequence=[
        "BossAgent",
        "SystemAgent",
        "SummaryAgent",
        "WriterAgent",
        "ReviewAgent"
    ]
)

print("生成结果:")
print(result)
```

### 9.3 风格分析与应用

```python
from eleven_blog_tunner.agents import get_protocol

protocol = get_protocol()

# 1. 分析文章风格
style_result = await protocol.call_agent(
    caller="User",
    callee="SystemAgent",
    input_data="分析这篇文章的风格：[文章内容]"
)

# 2. 使用风格撰写新文章
writer_result = await protocol.call_agent(
    caller="User",
    callee="WriterAgent",
    input_data=f"根据分析的风格写一篇新文章: {style_result['result']}"
)

print("风格分析:")
print(style_result['result'])
print("\n生成文章:")
print(writer_result['result'])
```

## 10. 未来规划

- **Agent 自动扩展**：根据任务自动调整 Agent 组合
- **智能路由**：基于任务类型自动选择最优 Agent 组合
- **学习能力**：Agent 从历史任务中学习优化
- **多模态支持**：支持图像、音频等多模态内容处理
- **插件系统**：支持第三方插件扩展

## 11. 总结

ELEVEN Blog Tuner 的 Agent 系统是一个高度模块化、智能协作的系统，通过专业分工和高效通信，为用户提供高质量的博客写作服务。系统设计遵循了良好的软件工程原则，具有良好的可扩展性和可维护性。

通过合理配置和使用这些 Agent，可以：
- 提高文章写作效率
- 保证文章质量
- 确保内容合规
- 实现个性化风格

Agent 系统是 ELEVEN Blog Tuner 项目的核心竞争力之一，为用户提供了智能、高效、个性化的博客写作体验。