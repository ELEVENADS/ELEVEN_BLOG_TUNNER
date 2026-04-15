"""
Agent 调用器
负责 agent 直接的调用，每次调用需要进行安全检验
规定各类 agent 解析的方法，统一结果返回结构
"""
from typing import Dict, Any
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext


class AgentCaller:
    """Agent 调用器"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent):
        """注册 Agent"""
        self._agents[agent.name] = agent
    
    async def call(self, agent_name: str, context: AgentContext) -> Dict[str, Any]:
        """
        调用 Agent
        进行安全检验并统一返回结构
        """
        if agent_name not in self._agents:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "data": None
            }
        
        try:
            agent = self._agents[agent_name]
            # TODO: 安全检验
            result = await agent.execute(context)
            return {
                "success": True,
                "error": None,
                "data": result,
                "agent": agent_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "agent": agent_name
            }
