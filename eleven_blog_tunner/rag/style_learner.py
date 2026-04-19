"""
风格学习模块

从文本中提取写作风格特征，包括词汇、句式、结构和写作习惯等维度
支持混合模式：规则统计 + LLM语义分析 + Embedding向量
"""
import re
import jieba
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from eleven_blog_tunner.rag.embedding import EmbeddingService


@dataclass
class SemanticStyleFeatures:
    """LLM语义分析风格特征"""
    language_style: str = ""  # 语言风格：幽默/严肃/活泼/沉稳等
    tone: str = ""  # 语气特征：正式/非正式/学术/口语化等
    vocabulary_level: str = ""  # 词汇水平：通俗/专业/学术/文学等
    sentence_rhythm: str = ""  # 句式节奏：长短句交替/短句为主等
    rhetoric_devices: List[str] = field(default_factory=list)  # 修辞手法
    emotional_tendency: str = ""  # 情感倾向：积极/消极/中性等
    perspective: str = ""  # 叙述视角：第一人称/第三人称/客观等
    logic_structure: str = ""  # 逻辑结构：总分总/递进/对比等
    unique_habits: List[str] = field(default_factory=list)  # 独特表达习惯
    target_audience: str = ""  # 目标读者群体
    domain_characteristics: str = ""  # 领域特征
    writing_quirks: str = ""  # 其他显著特点


@dataclass
class StyleFeatures:
    """风格特征"""
    # 词汇特征
    vocabulary_diversity: float  # 词汇多样性 (0-1)
    average_word_length: float   # 平均词长
    unique_words_ratio: float    # 独特词比例 (0-1)
    
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
    """风格学习器 - 混合模式
    
    结合规则统计 + LLM语义分析 + Embedding向量
    """
    
    def __init__(self, use_llm: bool = True, llm_provider: str = "openai"):
        self.embedding_service = EmbeddingService()
        self.use_llm = use_llm
        self.llm_provider = llm_provider
        self._summary_agent = None  # 延迟初始化
        
        self.transition_words = {
            '连接词': ['因此', '所以', '然而', '但是', '此外', '另外', '同时', '而且', '不过', '总之'],
            '转折词': ['但是', '然而', '不过', '可是', '却', '反而'],
            '递进词': ['而且', '并且', '此外', '另外', '不仅', '甚至'],
            '因果词': ['因为', '所以', '因此', '由于', '结果', '导致']
        }
        self.first_person_pronouns = ['我', '我们', '咱', '咱们', 'my', 'our', 'mine', 'ours']
        self.passive_markers = ['被', '由', '让', '使', '叫', '遭', '受', 'is', 'was', 'were', 'been']
    
    def _get_summary_agent(self):
        """延迟初始化 SummaryAgent"""
        if self._summary_agent is None and self.use_llm:
            from eleven_blog_tunner.agents.summary_agent import SummaryAgent
            self._summary_agent = SummaryAgent(llm_provider=self.llm_provider)
        return self._summary_agent
    
    async def learn_style(
        self, 
        text: str, 
        use_statistical: bool = True,
        use_semantic: bool = True,
        use_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        学习文本风格 - 混合模式
        
        Args:
            text: 文本内容
            use_statistical: 是否使用规则统计特征
            use_semantic: 是否使用LLM语义分析
            use_embedding: 是否使用Embedding向量
        
        Returns:
            完整的风格特征和向量
        """
        result = {
            'statistical_features': None,
            'semantic_features': None,
            'vector': None
        }
        
        # 1. 规则统计特征
        if use_statistical:
            statistical_features = self._extract_features(text)
            result['statistical_features'] = asdict(statistical_features)
        else:
            statistical_features = None
        
        # 2. LLM语义分析特征
        if use_semantic and self.use_llm:
            semantic_features = await self._extract_semantic_features(text)
            result['semantic_features'] = asdict(semantic_features)
        else:
            semantic_features = None
        
        # 3. 生成融合向量
        if use_embedding:
            style_vector = await self._generate_fusion_vector(
                text, statistical_features, semantic_features
            )
            result['vector'] = style_vector
        
        return result
    
    async def _extract_semantic_features(self, text: str) -> SemanticStyleFeatures:
        """
        使用 SummaryAgent 进行 LLM 语义分析
        
        Args:
            text: 文本内容
            
        Returns:
            语义风格特征
        """
        try:
            summary_agent = self._get_summary_agent()
            if summary_agent is None:
                return SemanticStyleFeatures()
            
            # 调用 SummaryAgent 的 analyze_writing_style 方法
            llm_result = await summary_agent.analyze_writing_style(text)
            
            # 映射 LLM 结果到 SemanticStyleFeatures
            return SemanticStyleFeatures(
                language_style=llm_result.get('language_style', ''),
                tone=llm_result.get('tone', ''),
                vocabulary_level=llm_result.get('vocabulary_level', ''),
                sentence_rhythm=llm_result.get('sentence_rhythm', ''),
                rhetoric_devices=llm_result.get('rhetoric_devices', []),
                emotional_tendency=llm_result.get('emotional_tendency', ''),
                perspective=llm_result.get('perspective', ''),
                logic_structure=llm_result.get('logic_structure', ''),
                unique_habits=llm_result.get('unique_habits', []),
                target_audience=llm_result.get('target_audience', ''),
                domain_characteristics=llm_result.get('domain_characteristics', ''),
                writing_quirks=llm_result.get('writing_quirks', '')
            )
        except Exception as e:
            print(f"LLM语义分析失败: {e}")
            return SemanticStyleFeatures()
    
    async def _generate_fusion_vector(
        self, 
        text: str, 
        statistical_features: Optional[StyleFeatures],
        semantic_features: Optional[SemanticStyleFeatures]
    ) -> List[float]:
        """
        生成融合风格向量
        
        结合：
        1. 文本语义向量 (Embedding)
        2. 统计特征向量
        3. 语义特征编码
        """
        # 1. 获取文本语义向量
        try:
            text_vector = await self.embedding_service.embed(text)
        except Exception as e:
            print(f"Embedding 失败: {e}，使用零向量")
            text_vector = [0.0] * 1536  # OpenAI embedding 默认维度
        
        # 2. 统计特征向量
        statistical_vector = []
        if statistical_features:
            statistical_vector = [
                statistical_features.vocabulary_diversity,
                statistical_features.average_word_length,
                statistical_features.unique_words_ratio,
                statistical_features.average_sentence_length,
                statistical_features.sentence_complexity,
                statistical_features.punctuation_density,
                statistical_features.paragraph_average_length,
                statistical_features.transition_words_ratio,
                statistical_features.passive_voice_ratio,
                statistical_features.first_person_ratio,
                statistical_features.emoji_usage
            ]
        else:
            statistical_vector = [0.0] * 11
        
        # 3. 语义特征编码（简化处理，将文本特征转为数值）
        semantic_vector = self._encode_semantic_features(semantic_features)
        
        # 融合向量：语义向量 + 统计特征 + 语义编码
        fusion_vector = text_vector + statistical_vector + semantic_vector
        return fusion_vector
    
    def _encode_semantic_features(self, semantic_features: Optional[SemanticStyleFeatures]) -> List[float]:
        """
        将语义特征编码为数值向量
        
        使用简单的 one-hot / 权重编码方式
        """
        if semantic_features is None:
            return [0.0] * 50  # 占位向量
        
        # 预定义的分类和权重
        language_styles = ['幽默', '严肃', '活泼', '沉稳', '犀利', '温和', '文艺', '朴实', '讽刺', '热情']
        tones = ['正式', '非正式', '学术', '口语化', '亲切', '客观', '主观', '专业']
        vocab_levels = ['通俗', '专业', '学术', '文学', '口语', '技术']
        rhythms = ['长短句交替', '短句为主', '长句为主', '节奏明快', '舒缓', '紧凑']
        emotions = ['积极', '消极', '中性', '热情', '冷静', '讽刺', '幽默']
        perspectives = ['第一人称', '第三人称', '客观', '主观', '全局', '个人']
        logic_structures = ['总分总', '递进', '对比', '并列', '因果', '时间顺序']
        
        vector = []
        
        # 编码各类特征（使用简单的匹配权重）
        vector.extend(self._encode_category(semantic_features.language_style, language_styles))
        vector.extend(self._encode_category(semantic_features.tone, tones))
        vector.extend(self._encode_category(semantic_features.vocabulary_level, vocab_levels))
        vector.extend(self._encode_category(semantic_features.sentence_rhythm, rhythms))
        vector.extend(self._encode_category(semantic_features.emotional_tendency, emotions))
        vector.extend(self._encode_category(semantic_features.perspective, perspectives))
        vector.extend(self._encode_category(semantic_features.logic_structure, logic_structures))
        
        # 修辞手法数量（归一化）
        rhetoric_count = len(semantic_features.rhetoric_devices) if semantic_features.rhetoric_devices else 0
        vector.append(min(rhetoric_count / 10.0, 1.0))
        
        # 独特习惯数量（归一化）
        habits_count = len(semantic_features.unique_habits) if semantic_features.unique_habits else 0
        vector.append(min(habits_count / 5.0, 1.0))
        
        return vector
    
    def _encode_category(self, value: str, categories: List[str]) -> List[float]:
        """将文本类别编码为 one-hot 向量"""
        vector = [0.0] * len(categories)
        if value:
            for i, cat in enumerate(categories):
                if cat in value:
                    vector[i] = 1.0
                    break
        return vector
    
    def _extract_features(self, text: str) -> StyleFeatures:
        """
        提取风格特征
        """
        if not text or not text.strip():
            return self._get_empty_features()
        
        words = self._tokenize_text(text)
        unique_words = set(words)
        vocabulary_diversity = len(unique_words) / len(words) if words else 0
        average_word_length = sum(len(word) for word in words) / len(words) if words else 0
        unique_words_ratio = len(unique_words) / len(words) if words else 0
        
        sentences = self._split_sentences(text)
        average_sentence_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
        sentence_complexity = self._calculate_sentence_complexity(sentences)
        punctuation_density = self._calculate_punctuation_density(text)
        
        paragraphs = self._split_paragraphs(text)
        paragraph_average_length = sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        transition_words_ratio = self._calculate_transition_words_ratio(text, words)
        
        passive_voice_ratio = self._calculate_passive_voice_ratio(text, sentences)
        first_person_ratio = self._calculate_first_person_ratio(text, words)
        emoji_usage = self._calculate_emoji_usage(text)
        
        return StyleFeatures(
            vocabulary_diversity=round(vocabulary_diversity, 4),
            average_word_length=round(average_word_length, 4),
            unique_words_ratio=round(unique_words_ratio, 4),
            average_sentence_length=round(average_sentence_length, 4),
            sentence_complexity=round(sentence_complexity, 4),
            punctuation_density=round(punctuation_density, 4),
            paragraph_average_length=round(paragraph_average_length, 4),
            transition_words_ratio=round(transition_words_ratio, 4),
            passive_voice_ratio=round(passive_voice_ratio, 4),
            first_person_ratio=round(first_person_ratio, 4),
            emoji_usage=round(emoji_usage, 4)
        )
    
    def _get_empty_features(self) -> StyleFeatures:
        """返回空特征"""
        return StyleFeatures(
            vocabulary_diversity=0.0,
            average_word_length=0.0,
            unique_words_ratio=0.0,
            average_sentence_length=0.0,
            sentence_complexity=0.0,
            punctuation_density=0.0,
            paragraph_average_length=0.0,
            transition_words_ratio=0.0,
            passive_voice_ratio=0.0,
            first_person_ratio=0.0,
            emoji_usage=0.0
        )
    
    def _tokenize_text(self, text: str) -> List[str]:
        """分词处理"""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[*_~`#]+', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        words = jieba.lcut(text)
        words = [w.strip() for w in words if w.strip() and not re.match(r'^[^\w\s]+$', w)]
        
        return words
    
    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        sentences = re.split(r'[。！？.!?;；]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """分割段落"""
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs
    
    def _calculate_sentence_complexity(self, sentences: List[str]) -> float:
        """
        计算句式复杂度
        基于从句数量和标点符号计算
        """
        if not sentences:
            return 0.0
        
        total_complexity = 0.0
        for sentence in sentences:
            clause_markers = len(re.findall(r'[，,；;：:]', sentence))
            for category, words in self.transition_words.items():
                for word in words:
                    if word in sentence:
                        clause_markers += 1
            
            total_complexity += clause_markers
        
        return total_complexity / len(sentences)
    
    def _calculate_punctuation_density(self, text: str) -> float:
        """计算标点密度"""
        if not text:
            return 0.0
        
        punctuation_count = len(re.findall(r'[。！？.!?，,；;：:""''""（）()【\]\\[\]{}]', text))
        total_chars = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        
        return punctuation_count / total_chars if total_chars > 0 else 0.0
    
    def _calculate_transition_words_ratio(self, text: str, words: List[str]) -> float:
        """计算过渡词比例"""
        if not words:
            return 0.0
        
        transition_count = 0
        for category, trans_words in self.transition_words.items():
            for word in trans_words:
                transition_count += words.count(word)
        
        return transition_count / len(words)
    
    def _calculate_passive_voice_ratio(self, text: str, sentences: List[str]) -> float:
        """计算被动语态比例"""
        if not sentences:
            return 0.0
        
        passive_count = 0
        for sentence in sentences:
            for marker in self.passive_markers:
                if marker in sentence:
                    passive_count += 1
                    break
        
        return passive_count / len(sentences)
    
    def _calculate_first_person_ratio(self, text: str, words: List[str]) -> float:
        """计算第一人称比例"""
        if not words:
            return 0.0
        
        first_person_count = sum(words.count(p) for p in self.first_person_pronouns)
        
        return first_person_count / len(words)
    
    def _calculate_emoji_usage(self, text: str) -> float:
        """计算表情符号使用率"""
        if not text:
            return 0.0
        
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U00002600-\U000027BF"
            "]+",
            flags=re.UNICODE
        )
        
        emoji_count = len(emoji_pattern.findall(text))
        total_chars = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        
        return emoji_count / total_chars if total_chars > 0 else 0.0
    
    async def _generate_style_vector(self, text: str, features: StyleFeatures) -> List[float]:
        """
        生成风格向量
        结合文本语义向量和风格特征向量
        """
        try:
            text_vector = await self.embedding_service.embed(text)
        except Exception as e:
            print(f"Embedding 失败: {e}，使用特征向量")
            text_vector = [0.0] * 128
        
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
        
        style_vector = text_vector + feature_values
        return style_vector
    
    def compare_styles(self, style1: Dict[str, Any], style2: Dict[str, Any]) -> float:
        """
        比较两种风格的相似度
        使用余弦相似度
        """
        try:
            import numpy as np
            from scipy.spatial.distance import cosine
            
            vector1 = np.array(style1['vector'])
            vector2 = np.array(style2['vector'])
            
            similarity = 1 - cosine(vector1, vector2)
            return float(similarity)
        except Exception as e:
            print(f"风格比较失败: {e}")
            return 0.0
