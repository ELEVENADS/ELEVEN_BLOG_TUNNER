import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from eleven_blog_tunner.rag.style_learner import StyleLearner, StyleFeatures


class TestStyleLearner:
    """StyleLearner 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.learner = StyleLearner()

    @pytest.mark.asyncio
    async def test_learn_style_returns_features(self):
        """测试学习风格返回特征"""
        mock_embedder = MagicMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        with patch.object(self.learner, 'embedding_service', mock_embedder):
            result = await self.learner.learn_style("这是测试文本")
            
            assert 'features' in result
            assert 'vector' in result
            assert isinstance(result['features'], dict)

    @pytest.mark.asyncio
    async def test_learn_style_vector_generation(self):
        """测试风格向量生成"""
        mock_embedder = MagicMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        with patch.object(self.learner, 'embedding_service', mock_embedder):
            result = await self.learner.learn_style("测试文本")
            
            assert len(result['vector']) > 3

    def test_extract_features_basic(self):
        """测试提取基本风格特征"""
        text = "这是一个测试句子。这是一个又一个句子。短的"
        features = self.learner._extract_features(text)
        
        assert isinstance(features, StyleFeatures)
        assert hasattr(features, 'vocabulary_diversity')
        assert hasattr(features, 'average_word_length')
        assert hasattr(features, 'average_sentence_length')

    def test_extract_features_vocabulary(self):
        """测试词汇特征提取"""
        text = "测试 测试 文本 文本 文本"
        features = self.learner._extract_features(text)
        
        assert features.unique_words_ratio < 1.0
        assert features.vocabulary_diversity > 0

    def test_extract_features_sentence_length(self):
        """测试句长计算"""
        text = "短句。" * 5 + "这是一个稍微长一点的句子。" * 3
        features = self.learner._extract_features(text)
        
        assert features.average_sentence_length > 0

    def test_extract_features_transition_words(self):
        """测试过渡词比例"""
        text = "因此，所以，然而，但是，此外，另外"
        features = self.learner._extract_features(text)
        
        assert features.transition_words_ratio >= 0

    def test_extract_features_first_person(self):
        """测试第一人称比例"""
        text = "我认为我们大家觉得我觉得我认为"
        features = self.learner._extract_features(text)
        
        assert features.first_person_ratio > 0

    def test_extract_features_empty_text(self):
        """测试空文本"""
        features = self.learner._extract_features("")
        
        assert features.vocabulary_diversity == 0
        assert features.average_word_length == 0

    def test_calculate_sentence_complexity(self):
        """测试句子复杂度计算"""
        simple = "短句。短句。"
        complex_text = "这是一个，稍微，长一点，的句子，含有，从句。"
        
        simple_features = self.learner._calculate_sentence_complexity(["短句。", "短句。"])
        complex_features = self.learner._calculate_sentence_complexity(["这是一个，稍微，长一点，的句子，含有，从句。"])
        
        assert complex_features >= simple_features

    def test_calculate_transition_words_ratio(self):
        """测试过渡词比例计算"""
        text = "因此，所以，然而，但是，此外，另外"
        ratio = self.learner._calculate_transition_words_ratio(text)
        
        assert ratio > 0

    def test_calculate_first_person_ratio(self):
        """测试第一人称比例计算"""
        text = "我我们我觉得我认为"
        ratio = self.learner._calculate_first_person_ratio(text)
        
        assert ratio > 0

    def test_calculate_passive_voice_ratio(self):
        """测试被动语态比例计算"""
        text = "这本书被我读了。文章让他写了。"
        ratio = self.learner._calculate_passive_voice_ratio(text)
        
        assert ratio > 0


class TestStyleFeatures:
    """StyleFeatures 数据类测试"""

    def test_style_features_creation(self):
        """测试 StyleFeatures 创建"""
        features = StyleFeatures(
            vocabulary_diversity=0.5,
            average_word_length=4.0,
            unique_words_ratio=0.3,
            average_sentence_length=20.0,
            sentence_complexity=1.5,
            punctuation_density=0.1,
            paragraph_average_length=100.0,
            transition_words_ratio=0.05,
            passive_voice_ratio=0.1,
            first_person_ratio=0.15,
            emoji_usage=0.0
        )
        
        assert features.vocabulary_diversity == 0.5
        assert features.average_word_length == 4.0
        assert features.average_sentence_length == 20.0

    def test_style_features_to_dict(self):
        """测试 StyleFeatures 转为字典"""
        features = StyleFeatures(
            vocabulary_diversity=0.5,
            average_word_length=4.0,
            unique_words_ratio=0.3,
            average_sentence_length=20.0,
            sentence_complexity=1.5,
            punctuation_density=0.1,
            paragraph_average_length=100.0,
            transition_words_ratio=0.05,
            passive_voice_ratio=0.1,
            first_person_ratio=0.15,
            emoji_usage=0.0
        )
        
        features_dict = features.__dict__
        
        assert isinstance(features_dict, dict)
        assert 'vocabulary_diversity' in features_dict
        assert 'average_word_length' in features_dict
