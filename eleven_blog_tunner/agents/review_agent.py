from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext


class ReviewAgent(BaseAgent):
    """
    Review Agent
    负责审查文章质量和是否违规
    """
    
    def __init__(self):
        super().__init__(
            name="ReviewAgent",
            description="负责审查文章质量和是否违规"
        )
    
    async def execute(self, context: AgentContext) -> str:
        """执行审查任务"""
        # TODO: 实现审查逻辑
        return f"ReviewAgent 审查: {context.user_input}"
