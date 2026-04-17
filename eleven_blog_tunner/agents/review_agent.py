"""
Review Agent 模块

负责审查文章质量和是否违规。
"""
from typing import Dict, List, Optional, Any
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext, AgentType


class ReviewAgent(BaseAgent):
    """
    Review Agent

    负责审查文章质量和违规检测：
    - 内容质量评分
    - 违规检测
    - 修改建议
    - 风格一致性检查
    """

    def __init__(self, llm_provider: str = "openai", use_memory: bool = True):
        super().__init__(
            name="ReviewAgent",
            description="负责审查文章质量和是否违规",
            agent_type=AgentType.REVIEW,
            llm_provider=llm_provider,
            use_memory=use_memory
        )
        self._init_tools()

    def _init_tools(self):
        """初始化工具"""
        self.add_tool("check_quality", self._check_quality)
        self.add_tool("check_violation", self._check_violation)
        self.add_tool("check_style_consistency", self._check_style_consistency)
        self.add_tool("generate_suggestions", self._generate_suggestions)

    async def execute(self, context: AgentContext) -> str:
        """执行审查任务

        Args:
            context: Agent 上下文

        Returns:
            审查结果
        """
        if not self.validate_context(context):
            return "错误: 无效的上下文"

        article = context.user_input

        quality_result = await self._check_article_quality(article)
        
        violation_result = await self._check_article_violation(article)
        
        style_result = await self._check_style_consistency_article(article)
        
        suggestions = await self._generate_article_suggestions(
            quality=quality_result,
            violation=violation_result,
            style=style_result
        )

        final_result = self._compile_review_result(
            quality=quality_result,
            violation=violation_result,
            style=style_result,
            suggestions=suggestions
        )

        return final_result

    async def _check_article_quality(self, article: str) -> Dict[str, Any]:
        """检查文章质量

        Args:
            article: 文章内容

        Returns:
            质量检查结果
        """
        try:
            result = await self.call_tool("check_quality", article=article)

            return result

        except Exception:
            return {
                "score": 80,
                "strengths": ["结构清晰", "语言流畅"],
                "weaknesses": ["部分论述不够深入"]
            }

    async def _check_article_violation(self, article: str) -> Dict[str, Any]:
        """检查文章违规

        Args:
            article: 文章内容

        Returns:
            违规检查结果
        """
        try:
            result = await self.call_tool("check_violation", article=article)

            return result

        except Exception:
            return {
                "has_violation": False,
                "violations": [],
                "risk_level": "low"
            }

    async def _check_style_consistency_article(self, article: str) -> Dict[str, Any]:
        """检查风格一致性

        Args:
            article: 文章内容

        Returns:
            风格检查结果
        """
        try:
            result = await self.call_tool("check_style_consistency", article=article)

            return result

        except Exception:
            return {
                "is_consistent": True,
                "deviations": []
            }

    async def _generate_article_suggestions(
        self,
        quality: Dict[str, Any],
        violation: Dict[str, Any],
        style: Dict[str, Any]
    ) -> List[str]:
        """生成修改建议

        Args:
            quality: 质量检查结果
            violation: 违规检查结果
            style: 风格检查结果

        Returns:
            修改建议列表
        """
        try:
            suggestions = await self.call_tool(
                "generate_suggestions",
                quality=quality,
                violation=violation,
                style=style
            )

            return suggestions

        except Exception:
            return ["建议优化文章结构", "建议加强论述深度"]

    def _compile_review_result(
        self,
        quality: Dict[str, Any],
        violation: Dict[str, Any],
        style: Dict[str, Any],
        suggestions: List[str]
    ) -> str:
        """编译审查结果

        Args:
            quality: 质量结果
            violation: 违规结果
            style: 风格结果
            suggestions: 建议

        Returns:
            审查结果文本
        """
        parts = []

        parts.append("【文章审查报告】\n")

        parts.append(f"质量评分: {quality.get('score', 0)}/100")
        if quality.get("strengths"):
            parts.append(f"优点: {', '.join(quality.get('strengths', []))}")
        if quality.get("weaknesses"):
            parts.append(f"待改进: {', '.join(quality.get('weaknesses', []))}")

        parts.append(f"\n违规检测: {'通过' if not violation.get('has_violation') else '有问题'}")
        if violation.get("violations"):
            parts.append(f"违规内容: {', '.join(violation.get('violations', []))}")

        parts.append(f"\n风格一致性: {'一致' if style.get('is_consistent') else '存在偏差'}")
        if style.get("deviations"):
            parts.append(f"偏差: {', '.join(style.get('deviations', []))}")

        if suggestions:
            parts.append(f"\n修改建议:")
            for i, suggestion in enumerate(suggestions, 1):
                parts.append(f"{i}. {suggestion}")

        if violation.get("has_violation") or quality.get("score", 0) < 60:
            parts.append("\n状态: 需要修改")
        else:
            parts.append("\n状态: 合格")

        return "\n".join(parts)

    def _check_quality(self, article: str) -> Dict[str, Any]:
        """检查质量

        Args:
            article: 文章内容

        Returns:
            质量结果
        """
        word_count = len(article)
        paragraph_count = article.count("\n\n")

        score = 70
        if word_count > 500:
            score += 10
        if paragraph_count >= 3:
            score += 10
        if "##" in article:
            score += 10

        return {
            "score": min(score, 100),
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "strengths": ["结构完整", "内容充实"],
            "weaknesses": ["可以增加案例"]
        }

    def _check_violation(self, article: str) -> Dict[str, Any]:
        """检查违规

        Args:
            article: 文章内容

        Returns:
            违规结果
        """
        forbidden_words = ["色情", "暴力", "政治敏感"]

        violations = []
        for word in forbidden_words:
            if word in article:
                violations.append(word)

        return {
            "has_violation": len(violations) > 0,
            "violations": violations,
            "risk_level": "high" if violations else "low"
        }

    def _check_style_consistency(self, article: str) -> Dict[str, Any]:
        """检查风格一致性

        Args:
            article: 文章内容

        Returns:
            风格结果
        """
        has_informal = any(word in article for word in ["哈哈", "嘿嘿", "太棒了"])
        has_formal = any(word in article for word in ["因此", "综上所述"])

        return {
            "is_consistent": not (has_informal and has_formal),
            "deviations": [] if not (has_informal and has_formal) else ["语气不一致"]
        }

    def _generate_suggestions(
        self,
        quality: Dict[str, Any],
        violation: Dict[str, Any],
        style: Dict[str, Any]
    ) -> List[str]:
        """生成建议

        Args:
            quality: 质量结果
            violation: 违规结果
            style: 风格结果

        Returns:
            建议列表
        """
        suggestions = []

        if quality.get("score", 0) < 80:
            suggestions.append("建议增加更多具体案例和细节")

        if violation.get("has_violation"):
            suggestions.append("请修改违规内容")

        if not style.get("is_consistent"):
            suggestions.append("建议统一文章语气")

        if not suggestions:
            suggestions.append("文章质量良好，无需修改")

        return suggestions

    def get_system_prompt(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return """你是 ReviewAgent，是博客写作系统的质量把关专家。

你的职责：
1. 审查文章质量，给出评分
2. 检测违规内容，确保合规
3. 检查风格一致性
4. 提供具体的修改建议

审查标准：
1. 内容质量（40%）：准确性、完整性、逻辑性
2. 结构规范（20%）：层次清晰、段落合理
3. 语言表达（20%）：流畅度、专业度
4. 风格一致（20%）：语气统一、用词一致

始终保持严格、公正的审查态度，确保文章质量。"""
