from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext


class SummaryAgent(BaseAgent):
    """
    Summary Agent
    负责总结类工作
    比如总结上下文、总结文章风格
    """
    
    def __init__(self):
        super().__init__(
            name="SummaryAgent",
            description="负责总结类工作，比如总结上下文、总结文章风格"
        )
    
    async def execute(self, context: AgentContext) -> str:
        """执行总结任务"""
        # TODO: 实现总结逻辑
        return f"SummaryAgent 总结: {context.user_input}"
