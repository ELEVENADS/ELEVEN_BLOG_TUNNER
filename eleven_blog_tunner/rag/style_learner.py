"""
风格学习模块
"""
import re
from typing import Dict, List, Any
from dataclasses import dataclass
from eleven_blog_tunner.rag.embedding import EmbeddingService


@dataclass
class StyleFeatures:
    """风格特征"""
    # 词汇特征
    vocabulary_diversity: float  # 词汇多样性
    average_word_length: float   # 平均词长
    unique_words_ratio: float    # 独特词比例
    
    # 句式特征
    average_sentence_length: float  # 平均句长
    sentence_complexity: float      # 句式复杂度
    punctuation_density: float       # 标点密度
    
    # 结构特征
    paragraph_average_length: float  # 平均段落长度
    transition_words_ratio: float    # 过渡词比例
    
    # 写作习惯
    passive_voice_ratio: float       # 被动语态比例
    first_person_ratio: float        # 第一人称比例
    emoji_usage: float               # 表情符号使用


class StyleLearner:
    """风格学习器"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.transition_words = {
            '连接词': ['因此', '所以', '然而', '但是', '此外', '另外', '同时', '而且', '不过', '总之'],
            '转折词': ['但是', '然而', '不过', '可是', '却', '反而'],
            '递进词': ['而且', '并且', '此外', '另外', '不仅', '甚至'],
            '因果词': ['因为', '所以', '因此', '由于', '结果', '导致']
        }
    
    async def learn_style(self, text: str) -> Dict[str, Any]:
        """
        学习文本风格
        
        Args:
            text: 文本内容
        
        Returns:
            风格特征和向量
        """
        # 提取风格特征
        features = self._extract_features(text)
        
        # 生成风格向量
        style_vector = await self._generate_style_vector(text, features)
        
        return {
            'features': features.__dict__,
            'vector': style_vector
        }
    
    def _extract_features(self, text: str) -> StyleFeatures:
        """
        提取风格特征
        """
        # 词汇特征
        words = re.findall(r'\b\w+\b', text)
        unique_words = set(words)
        vocabulary_diversity = len(unique_words) / len(words) if words else 0
        average_word_length = sum(len(word) for word in words) / len(words) if words else 0
        unique_words_ratio = len(unique_words) / len(words) if words else 0
        
        # 句式特征
        sentences = re.split(r'[。！？.!?]\s*', text)
        sentences = [s for s in sentences if s.strip()]
        average_sentence_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
        sentence_complexity = self._calculate_sentence_complexity(sentences)
        punctuation_density = len(re.findall(r'[。！？.,!?]', text)) / len(text) if text else 0
        
        # 结构特征
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p for p in paragraphs if p.strip()]
        paragraph_average_length = sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        transition_words_ratio = self._calculate_transition_words_ratio(text)
        
        # 写作习惯
        passive_voice_ratio = self._calculate_passive_voice_ratio(text)
        first_person_ratio = self._calculate_first_person_ratio(text)
        emoji_usage = len(re.findall(r'[\u2600-\u27BF\uD83C-\uDBFF\uDC00-\uDFFF]', text)) / len(text) if text else 0
        
        return StyleFeatures(
            vocabulary_diversity=vocabulary_diversity,
            average_word_length=average_word_length,
            unique_words_ratio=unique_words_ratio,
            average_sentence_length=average_sentence_length,
            sentence_complexity=sentence_complexity,
            punctuation_density=punctuation_density,
            paragraph_average_length=paragraph_average_length,
            transition_words_ratio=transition_words_ratio,
            passive_voice_ratio=passive_voice_ratio,
            first_person_ratio=first_person_ratio,
            emoji_usage=emoji_usage
        )
    
    def _calculate_sentence_complexity(self, sentences: List[str]) -> float:
        """
        计算句式复杂度
        """
        if not sentences:
            return 0
        
        complexity = 0
        for sentence in sentences:
            # 基于从句数量和标点符号计算复杂度
            clause_count = len(re.findall(r'[，,；;]', sentence))
            complexity += clause_count
        
        return complexity / len(sentences)
    
    def _calculate_transition_words_ratio(self, text: str) -> float:
        """
        计算过渡词比例
        """
        transition_count = 0
        for category, words in self.transition_words.items():
            for word in words:
                transition_count += text.count(word)
        
        total_words = len(re.findall(r'\b\w+\b', text))
        return transition_count / total_words if total_words else 0
    
    def _calculate_passive_voice_ratio(self, text: str) -> float:
        """
        计算被动语态比例
        """
        # 简单检测被动语态（基于"被"、"由"等标记）
        passive_markers = ['被', '由', '让', '使', '叫']
        passive_count = 0
        for marker in passive_markers:
            passive_count += text.count(marker)
        
        total_sentences = len(re.split(r'[。！？.!?]\s*', text))
        return passive_count / total_sentences if total_sentences else 0
    
    def _calculate_first_person_ratio(self, text: str) -> float:
        """
        计算第一人称比例
        """
        first_person_pronouns = ['我', '我们', '咱', '咱们']
        first_person_count = 0
        for pronoun in first_person_pronouns:
            first_person_count += text.count(pronoun)
        
        total_words = len(re.findall(r'\b\w+\b', text))
        return first_person_count / total_words if total_words else 0
    
    async def _generate_style_vector(self, text: str, features: StyleFeatures) -> List[float]:
        """
        生成风格向量
        """
        # 使用 embedding 服务生成文本的向量表示
        # 结合风格特征作为额外维度
        text_vector = await self.embedding_service.embed(text)
        
        # 提取特征值作为向量的一部分
        feature_values = [
            features.vocabulary_diversity,
            features.average_word_length,
            features.unique_words_ratio,
            features.average_sentence_length,
            features.sentence_complexity,
            features.punctuation_density,
            features.paragraph_average_length,
            features.transition_words_ratio,
            features.passive_voice_ratio,
            features.first_person_ratio,
            features.emoji_usage
        ]
        
        # 合并文本向量和特征向量
        style_vector = text_vector + feature_values
        return style_vector
    
    def compare_styles(self, style1: Dict[str, Any], style2: Dict[str, Any]) -> float:
        """
        比较两种风格的相似度
        """
        from scipy.spatial.distance import cosine
        import numpy as np
        
        vector1 = np.array(style1['vector'])
        vector2 = np.array(style2['vector'])
        
        # 计算余弦相似度
        similarity = 1 - cosine(vector1, vector2)
        return similarity