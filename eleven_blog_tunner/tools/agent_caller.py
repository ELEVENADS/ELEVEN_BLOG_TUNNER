"""
Agent 调用器
负责 agent 直接的调用，每次调用需要进行安全检验
规定各类 agent 解析的方法，统一结果返回结构
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time
from collections import defaultdict, deque
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext
from eleven_blog_tunner.core.exceptions import AgentException


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls  # 最大调用次数
        self.time_window = time_window  # 时间窗口（秒）
        self.calls = defaultdict(lambda: deque())
    
    def check(self, key: str) -> bool:
        """检查是否超过速率限制"""
        now = time.time()
        # 移除过期的调用记录
        while self.calls[key] and now - self.calls[key][0] > self.time_window:
            self.calls[key].popleft()
        # 检查是否超过限制
        if len(self.calls[key]) >= self.max_calls:
            return False
        # 记录本次调用
        self.calls[key].append(now)
        return True


class CircuitBreaker:
    """熔断机制"""
    
    def __init__(self, failure_threshold: int, recovery_time: int):
        self.failure_threshold = failure_threshold  # 失败阈值
        self.recovery_time = recovery_time  # 恢复时间（秒）
        self.failure_counts = defaultdict(int)
        self.open_since = defaultdict(Optional[float])
    
    def check(self, key: str) -> bool:
        """检查熔断状态"""
        now = time.time()
        # 检查是否处于熔断状态
        if self.open_since[key] and now - self.open_since[key] < self.recovery_time:
            return False
        # 重置熔断状态
        if self.open_since[key] and now - self.open_since[key] >= self.recovery_time:
            self.open_since[key] = None
            self.failure_counts[key] = 0
        return True
    
    def record_failure(self, key: str):
        """记录失败"""
        self.failure_counts[key] += 1
        if self.failure_counts[key] >= self.failure_threshold:
            self.open_since[key] = time.time()
    
    def record_success(self, key: str):
        """记录成功"""
        self.failure_counts[key] = 0
        self.open_since[key] = None


class CallChainMonitor:
    """调用链监控"""
    
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.call_chains = defaultdict(list)
    
    def check(self, caller: str, target: str, context: AgentContext) -> bool:
        """检查调用链"""
        chain = self.call_chains.get(context.task_id, [])
        # 检查循环调用
        if target in chain:
            return False
        # 检查调用深度
        if len(chain) >= self.max_depth:
            return False
        return True
    
    def start_call(self, caller: str, target: str, context: AgentContext):
        """开始调用"""
        if context.task_id not in self.call_chains:
            self.call_chains[context.task_id] = []
        self.call_chains[context.task_id].append(target)
    
    def end_call(self, context: AgentContext):
        """结束调用"""
        if context.task_id in self.call_chains and self.call_chains[context.task_id]:
            self.call_chains[context.task_id].pop()
        # 清理空调用链
        if context.task_id in self.call_chains and not self.call_chains[context.task_id]:
            del self.call_chains[context.task_id]


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        # 权限表：{调用者: {被调用者: bool}}
        self.permissions = defaultdict(dict)
    
    def grant_permission(self, caller: str, target: str):
        """授予权限"""
        self.permissions[caller][target] = True
    
    def revoke_permission(self, caller: str, target: str):
        """撤销权限"""
        if target in self.permissions[caller]:
            del self.permissions[caller][target]
    
    def check_permission(self, caller: str, target: str) -> bool:
        """检查权限"""
        # 默认允许自我调用
        if caller == target:
            return True
        return self.permissions.get(caller, {}).get(target, False)


class AgentCaller:
    """Agent 调用器"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)  # 60秒内最多100次调用
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_time=30)  # 5次失败后熔断30秒
        self.call_chain_monitor = CallChainMonitor(max_depth=10)  # 最大调用深度10
        self.permission_manager = PermissionManager()
        self._init_default_permissions()
    
    def _init_default_permissions(self):
        """初始化默认权限"""
        # BossAgent 可以调用所有其他 Agent
        self.permission_manager.grant_permission("BossAgent", "SystemAgent")
        self.permission_manager.grant_permission("BossAgent", "SummaryAgent")
        self.permission_manager.grant_permission("BossAgent", "WriterAgent")
        self.permission_manager.grant_permission("BossAgent", "ReviewAgent")
        
        # SystemAgent 可以被所有 Agent 调用
        self.permission_manager.grant_permission("SystemAgent", "SystemAgent")
        self.permission_manager.grant_permission("SummaryAgent", "SystemAgent")
        self.permission_manager.grant_permission("WriterAgent", "SystemAgent")
        self.permission_manager.grant_permission("ReviewAgent", "SystemAgent")
    
    def register_agent(self, agent: BaseAgent):
        """注册 Agent"""
        self._agents[agent.name] = agent
    
    async def call(self, agent_name: str, context: AgentContext, caller: str = "System") -> Dict[str, Any]:
        """
        调用 Agent
        进行安全检验并统一返回结构
        
        Args:
            agent_name: 目标 Agent 名称
            context: 调用上下文
            caller: 调用者名称
            
        Returns:
            调用结果
        """
        # 1. 检查 Agent 是否存在
        if agent_name not in self._agents:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "data": None,
                "agent": agent_name,
                "caller": caller
            }
        
        # 2. 安全检验
        security_check = await self._security_check(caller, agent_name, context)
        if not security_check["success"]:
            return security_check
        
        agent = self._agents[agent_name]
        
        # 3. 记录调用链
        self.call_chain_monitor.start_call(caller, agent_name, context)
        
        try:
            # 4. 执行 Agent
            result = await agent.execute(context)
            
            # 5. 记录成功
            self.circuit_breaker.record_success(agent_name)
            
            return {
                "success": True,
                "error": None,
                "data": result,
                "agent": agent_name,
                "caller": caller
            }
        except Exception as e:
            # 6. 记录失败
            self.circuit_breaker.record_failure(agent_name)
            
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "agent": agent_name,
                "caller": caller
            }
        finally:
            # 7. 结束调用链
            self.call_chain_monitor.end_call(context)
    
    async def _security_check(self, caller: str, agent_name: str, context: AgentContext) -> Dict[str, Any]:
        """安全检验
        
        Args:
            caller: 调用者名称
            agent_name: 目标 Agent 名称
            context: 调用上下文
            
        Returns:
            检验结果
        """
        # 1. 权限验证
        if not self.permission_manager.check_permission(caller, agent_name):
            return {
                "success": False,
                "error": f"Permission denied: {caller} cannot call {agent_name}",
                "data": None,
                "agent": agent_name,
                "caller": caller
            }
        
        # 2. 速率限制
        rate_key = f"{caller}:{agent_name}"
        if not self.rate_limiter.check(rate_key):
            return {
                "success": False,
                "error": f"Rate limit exceeded: {caller} -> {agent_name}",
                "data": None,
                "agent": agent_name,
                "caller": caller
            }
        
        # 3. 熔断检查
        if not self.circuit_breaker.check(agent_name):
            return {
                "success": False,
                "error": f"Circuit breaker open: {agent_name} is temporarily unavailable",
                "data": None,
                "agent": agent_name,
                "caller": caller
            }
        
        # 4. 调用链检查
        if not self.call_chain_monitor.check(caller, agent_name, context):
            return {
                "success": False,
                "error": f"Invalid call chain: possible circular call or too deep recursion",
                "data": None,
                "agent": agent_name,
                "caller": caller
            }
        
        # 5. 参数验证
        if not self._validate_context(context):
            return {
                "success": False,
                "error": "Invalid context: missing required fields",
                "data": None,
                "agent": agent_name,
                "caller": caller
            }
        
        return {
            "success": True,
            "error": None,
            "data": None,
            "agent": agent_name,
            "caller": caller
        }
    
    def _validate_context(self, context: AgentContext) -> bool:
        """验证上下文
        
        Args:
            context: 调用上下文
            
        Returns:
            是否有效
        """
        # 检查必要字段
        if not context.task_id:
            return False
        if not context.user_input:
            return False
        return True
    
    def grant_permission(self, caller: str, target: str):
        """授予权限
        
        Args:
            caller: 调用者名称
            target: 目标 Agent 名称
        """
        self.permission_manager.grant_permission(caller, target)
    
    def revoke_permission(self, caller: str, target: str):
        """撤销权限
        
        Args:
            caller: 调用者名称
            target: 目标 Agent 名称
        """
        self.permission_manager.revoke_permission(caller, target)
    
    def get_agents(self) -> List[str]:
        """获取所有注册的 Agent
        
        Returns:
            Agent 名称列表
        """
        return list(self._agents.keys())
    
    def get_permissions(self) -> Dict[str, List[str]]:
        """获取权限配置
        
        Returns:
            权限配置
        """
        permissions = {}
        for caller, targets in self.permission_manager.permissions.items():
            permissions[caller] = [target for target, allowed in targets.items() if allowed]
        return permissions
