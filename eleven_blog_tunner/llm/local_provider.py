"""
本地 LLM 提供商
"""
from typing import AsyncIterator, List, Dict, Any
import httpx
import json
from eleven_blog_tunner.llm.base import BaseLLM


class LocalProvider(BaseLLM):
    """本地 LLM 提供商（支持 Ollama）
    
    将标准消息格式转换为 Ollama API 格式。
    """
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434/api", **kwargs):
        super().__init__(model=model, **kwargs)
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
    
    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准备消息，转换为 Ollama 格式
        
        Ollama 使用不同的消息格式：
        - system: 系统提示（单独字段）
        - messages: 对话消息列表（只包含 user 和 assistant）
        
        Returns:
            包含 ollama_messages 和 system_content 的字典
        """
        ollama_messages = []
        system_content = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                # Ollama 将 system 消息放在单独的字段
                system_content = content
            elif role == "tool":
                # 工具消息转换为 assistant 消息，包含工具结果
                ollama_messages.append({
                    "role": "assistant",
                    "content": f"工具调用结果: {content}"
                })
            elif role == "assistant" and "tool_calls" in msg:
                # 包含工具调用的 assistant 消息
                tool_calls_str = json.dumps(msg["tool_calls"], ensure_ascii=False)
                ollama_messages.append({
                    "role": "assistant",
                    "content": f"我将使用工具: {tool_calls_str}"
                })
            else:
                # 普通 user 或 assistant 消息
                ollama_messages.append({
                    "role": role,
                    "content": content
                })
        
        return {
            "messages": ollama_messages,
            "system": system_content
        }
    
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """对话
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数
                - tools: 工具定义列表（Ollama 通过系统提示模拟）
                
        Returns:
            模型的响应文本
        """
        tools = kwargs.get('tools')
        
        # 准备消息
        prepared = self._prepare_messages(messages)
        ollama_messages = prepared["messages"]
        system_content = prepared["system"]
        
        # 构建 Ollama 请求体
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        # 添加系统提示（如果有）
        if system_content:
            payload["system"] = system_content
        
        # 对于 Ollama，函数调用通过系统提示模拟
        if tools:
            tool_prompt = self._build_tool_prompt(tools)
            if "system" in payload:
                payload["system"] += tool_prompt
            else:
                payload["system"] = tool_prompt
        
        try:
            response = await self.client.post("/chat", json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            # 尝试解析工具调用（如果模型输出了工具调用格式）
            tool_calls = self._parse_tool_calls(content)
            if tool_calls:
                return {
                    "content": "",
                    "tool_calls": tool_calls
                }
            
            return content
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            raise Exception(f"Ollama API error: {error_detail}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def stream_chat(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """流式对话
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数
                - tools: 工具定义列表
                
        Yields:
            模型响应的文本片段
        """
        tools = kwargs.get('tools')
        
        # 准备消息
        prepared = self._prepare_messages(messages)
        ollama_messages = prepared["messages"]
        system_content = prepared["system"]
        
        # 构建 Ollama 请求体
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        # 添加系统提示（如果有）
        if system_content:
            payload["system"] = system_content
        
        # 对于 Ollama，函数调用通过系统提示模拟
        if tools:
            tool_prompt = self._build_tool_prompt(tools)
            if "system" in payload:
                payload["system"] += tool_prompt
            else:
                payload["system"] = tool_prompt
        
        try:
            async with self.client.stream("POST", "/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            raise Exception(f"Ollama API error: {error_detail}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def _build_tool_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """构建工具提示"""
        prompt = "\n\n你是一个助手，可以使用以下工具来回答问题：\n\n"
        
        for tool in tools:
            func = tool.get("function", {})
            name = func.get("name", "")
            desc = func.get("description", "")
            params = func.get("parameters", {})
            
            prompt += f"工具名称: {name}\n"
            prompt += f"描述: {desc}\n"
            prompt += f"参数: {json.dumps(params, ensure_ascii=False)}\n\n"
        
        prompt += "当你需要使用工具时，请按照以下格式输出：\n"
        prompt += '{"tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "工具名称", "arguments": "{\\"参数1\\": \\"值1\\"}"}}]}\n\n'
        
        return prompt
    
    def _parse_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """尝试从响应内容中解析工具调用"""
        try:
            # 尝试解析 JSON 格式的工具调用
            data = json.loads(content)
            if isinstance(data, dict) and "tool_calls" in data:
                return data["tool_calls"]
        except json.JSONDecodeError:
            pass
        
        return []
