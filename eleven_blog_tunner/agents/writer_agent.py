from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext


class WriterAgent(BaseAgent):
    """
    Writer Agent
    负责文章的撰写
    通过固定的风格和例子调用工具完成文章
    """
    
    def __init__(self):
        super().__init__(
            name="WriterAgent",
            description="负责文章的撰写，通过固定的风格和例子调用工具完成文章"
        )
    
    async def execute(self, context: AgentContext) -> str:
        """执行写作任务"""
        # TODO: 实现文章撰写逻辑
        return f"WriterAgent 撰写: {context.user_input}"
