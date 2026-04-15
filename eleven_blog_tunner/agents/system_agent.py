from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext


class SystemAgent(BaseAgent):
    """
    System Agent
    负责系统内任务状态查询和各种参数返回
    比如返回风格数据等
    """
    
    def __init__(self):
        super().__init__(
            name="SystemAgent",
            description="负责系统内任务状态查询和各种参数返回"
        )
    
    async def execute(self, context: AgentContext) -> str:
        """执行系统查询"""
        # TODO: 实现系统状态查询逻辑
        return f"SystemAgent 查询: {context.user_input}"
