"""
Boss Agent 模块

负责统筹系统任务调度和信息返回，是整个 Agent 系统的协调中心。
"""
from typing import Dict, List, Optional, Any
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext, AgentType, AgentResponse
from eleven_blog_tunner.agents.agent_protocol import get_protocol
from eleven_blog_tunner.utils.logger import logger_instance as logger


class BossAgent(BaseAgent):
    """
    Boss Agent

    负责统筹系统任务调度和信息返回：
    - 接收用户请求并解析任务类型
    - 协调其他 Agent 完成复杂任务
    - 监控任务执行状态
    - 返回最终结果给用户
    """

    def __init__(self, llm_provider: str = "openai", use_memory: bool = True):
        super().__init__(
            name="BossAgent",
            description="负责统筹系统任务调度和信息返回",
            agent_type=AgentType.BOSS,
            llm_provider=llm_provider,
            use_memory=use_memory
        )
        self._protocol = None
    
    @property
    def protocol(self):
        if self._protocol is None:
            from eleven_blog_tunner.agents.agent_protocol import get_protocol
            self._protocol = get_protocol()
        return self._protocol

    async def execute(self, context: AgentContext) -> str:
        """执行任务调度

        Args:
            context: Agent 上下文

        Returns:
            调度结果
        """
        logger.info(f"BossAgent 开始执行任务: {context.task_id}")
        
        if not self.validate_context(context):
            logger.error(f"BossAgent 无效的上下文: {context.task_id}")
            return "错误: 无效的上下文"

        user_input = context.user_input
        logger.info(f"BossAgent 接收到用户输入: {user_input[:100]}...")

        task_type = await self._analyze_task_type(user_input)
        logger.info(f"BossAgent 分析任务类型: {task_type}")

        self.add_to_memory("user", user_input)

        if task_type == "article_generation":
            result = await self._handle_article_generation(context)
        elif task_type == "style_query":
            result = await self._handle_style_query(context)
        elif task_type == "article_review":
            result = await self._handle_article_review(context)
        elif task_type == "system_status":
            result = await self._handle_system_status(context)
        else:
            result = await self._handle_general_task(context)

        self.add_to_memory("assistant", result)
        logger.info(f"BossAgent 任务执行完成: {context.task_id}")

        return result

    async def _analyze_task_type(self, user_input: str) -> str:
        """分析任务类型

        Args:
            user_input: 用户输入

        Returns:
            任务类型
        """
        system_prompt = """你是一个任务分析助手。根据用户输入判断任务类型。
        
        任务类型包括：
        - article_generation: 文章生成任务
        - style_query: 风格查询任务
        - article_review: 文章审查任务
        - system_status: 系统状态查询任务
        - general: 其他一般任务
        
        只返回一个词：任务类型"""
        
        try:
            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": user_input})
            result = await self.call_llm(messages)
            return result.strip().lower()
        except Exception:
            return "general"

    async def _handle_article_generation(self, context: AgentContext) -> str:
        """处理文章生成任务

        Args:
            context: Agent 上下文

        Returns:
            生成结果
        """
        try:
            # 并行执行SystemAgent和SummaryAgent
            import asyncio
            system_result, summary_result = await asyncio.gather(
                self._call_system_agent(context, "获取风格配置"),
                self._call_summary_agent(context, "分析写作上下文")
            )
            
            context.metadata["style_config"] = system_result
            context.metadata["context_analysis"] = summary_result
            
            writer_context = AgentContext(
                task_id=context.task_id,
                user_input=f"根据以下要求撰写文章：\n风格配置：{system_result}\n上下文分析：{summary_result}",
                history=context.history,
                metadata=context.metadata,
                agent_type=AgentType.WRITER
            )
            writer_result = await self._call_writer_agent(writer_context)
            
            review_context = AgentContext(
                task_id=context.task_id,
                user_input=writer_result,
                history=context.history,
                metadata=context.metadata,
                agent_type=AgentType.REVIEW
            )
            review_result = await self._call_review_agent(review_context)
            
            if "需要修改" in review_result or "不合格" in review_result:
                return f"文章需要修改：{review_result}"
            
            return writer_result
            
        except Exception as e:
            return f"文章生成失败: {str(e)}"

    async def _handle_style_query(self, context: AgentContext) -> str:
        """处理风格查询任务

        Args:
            context: Agent 上下文

        Returns:
            查询结果
        """
        return await self._call_system_agent(context, context.user_input)

    async def _handle_article_review(self, context: AgentContext) -> str:
        """处理文章审查任务

        Args:
            context: Agent 上下文

        Returns:
            审查结果
        """
        return await self._call_review_agent(context)

    async def _handle_system_status(self, context: AgentContext) -> str:
        """处理系统状态查询任务

        Args:
            context: Agent 上下文

        Returns:
            系统状态
        """
        return await self._call_system_agent(context, "查询系统状态")

    async def _handle_general_task(self, context: AgentContext) -> str:
        """处理一般任务

        Args:
            context: Agent 上下文

        Returns:
            处理结果
        """
        system_prompt = """你是一个专业的博客写作助手。用户会输入各种请求，
        请根据用户输入调用相应的 Agent 完成工作。

        如果用户请求：
        1. 生成文章 → 调用 WriterAgent
        2. 审查文章 → 调用 ReviewAgent
        3. 查询风格/配置 → 调用 SystemAgent
        4. 分析内容 → 调用 SummaryAgent

        对于一般问题，直接回答即可。"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": context.user_input})

        return await self.call_llm(messages)

    async def _call_system_agent(self, context: AgentContext, query: str) -> str:
        """调用 System Agent

        Args:
            context: Agent 上下文
            query: 查询内容

        Returns:
            调用结果
        """
        try:
            system_agent = self.protocol.get_agent("SystemAgent")
            if not system_agent:
                return "SystemAgent 不可用"

            system_context = AgentContext(
                task_id=context.task_id,
                user_input=query,
                history=context.history,
                metadata=context.metadata,
                agent_type=AgentType.SYSTEM
            )
            return await system_agent.execute(system_context)
        except Exception as e:
            return f"SystemAgent 调用失败: {str(e)}"

    async def _call_summary_agent(self, context: AgentContext, query: str) -> str:
        """调用 Summary Agent

        Args:
            context: Agent 上下文
            query: 查询内容

        Returns:
            调用结果
        """
        try:
            summary_agent = self.protocol.get_agent("SummaryAgent")
            if not summary_agent:
                return "SummaryAgent 不可用"

            summary_context = AgentContext(
                task_id=context.task_id,
                user_input=query,
                history=context.history,
                metadata=context.metadata,
                agent_type=AgentType.SUMMARY
            )
            return await summary_agent.execute(summary_context)
        except Exception as e:
            return f"SummaryAgent 调用失败: {str(e)}"

    async def _call_writer_agent(self, context: AgentContext) -> str:
        """调用 Writer Agent

        Args:
            context: Agent 上下文

        Returns:
            调用结果
        """
        try:
            writer_agent = self.protocol.get_agent("WriterAgent")
            if not writer_agent:
                return "WriterAgent 不可用"

            return await writer_agent.execute(context)
        except Exception as e:
            return f"WriterAgent 调用失败: {str(e)}"

    async def _call_review_agent(self, context: AgentContext) -> str:
        """调用 Review Agent

        Args:
            context: Agent 上下文

        Returns:
            调用结果
        """
        try:
            review_agent = self.protocol.get_agent("ReviewAgent")
            if not review_agent:
                return "ReviewAgent 不可用"

            return await review_agent.execute(context)
        except Exception as e:
            return f"ReviewAgent 调用失败: {str(e)}"

    def get_system_prompt(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return """你是 BossAgent，是整个博客写作系统的协调中心。

你的职责：
1. 接收并分析用户请求
2. 协调 SystemAgent、SummaryAgent、WriterAgent、ReviewAgent 完成复杂任务
3. 监控任务执行状态
4. 返回最终结果

协调流程：
1. SystemAgent → 获取风格配置和系统参数
2. SummaryAgent → 分析上下文，提取关键信息
3. WriterAgent → 根据风格和上下文撰写文章
4. ReviewAgent → 审查文章质量和合规性

始终保持专业的协调者姿态，确保各 Agent 高效协作。"""
