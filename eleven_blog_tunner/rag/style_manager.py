"""
风格管理模块
"""
import json
import os
from typing import Dict, Any, List
from pathlib import Path
from eleven_blog_tunner.rag.style_learner import StyleLearner
from eleven_blog_tunner.tools.skill_manager import SkillManager


class StyleManager:
    """风格管理器"""
    
    def __init__(self):
        self.learner = StyleLearner()
        self.skill_manager = SkillManager()
        self.style_storage = Path('./data/styles')
        self.style_storage.mkdir(parents=True, exist_ok=True)
    
    async def extract_style(self, text: str, style_name: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        提取风格并存储
        
        Args:
            text: 文本内容
            style_name: 风格名称
            metadata: 元数据
        
        Returns:
            风格信息
        """
        # 学习风格
        style_info = await self.learner.learn_style(text)
        
        # 添加元数据
        style_data = {
            'name': style_name,
            'features': style_info['features'],
            'vector': style_info['vector'],
            'metadata': metadata or {},
            'created_at': os.path.getmtime(__file__)  # 简化处理
        }
        
        # 存储风格
        style_path = self.style_storage / f"{style_name}.json"
        with open(style_path, 'w', encoding='utf-8') as f:
            json.dump(style_data, f, ensure_ascii=False, indent=2)
        
        # 注册为技能
        await self._register_style_as_skill(style_name, style_data)
        
        return style_data
    
    def load_style(self, style_name: str) -> Dict[str, Any]:
        """
        加载风格
        """
        style_path = self.style_storage / f"{style_name}.json"
        if not style_path.exists():
            raise FileNotFoundError(f"风格 {style_name} 不存在")
        
        with open(style_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_styles(self) -> List[str]:
        """
        列出所有风格
        """
        styles = []
        for style_file in self.style_storage.glob("*.json"):
            styles.append(style_file.stem)
        return styles
    
    async def _register_style_as_skill(self, style_name: str, style_data: Dict[str, Any]):
        """
        将风格注册为技能
        """
        skill_data = {
            'name': f"style_{style_name}",
            'description': f"{style_name} 写作风格",
            'parameters': {
                'type': 'object',
                'properties': {
                    'topic': {
                        'type': 'string',
                        'description': '写作主题'
                    },
                    'length': {
                        'type': 'integer',
                        'description': '文章长度（字数）',
                        'default': 500
                    }
                },
                'required': ['topic']
            },
            'style_features': style_data['features'],
            'style_vector': style_data['vector']
        }
        
        # 注册技能
        await self.skill_manager.add_skill(skill_data)
    
    async def extract_style_from_notes(self, notes_dir: str, style_name: str) -> Dict[str, Any]:
        """
        从笔记目录提取风格
        """
        combined_text = ""
        metadata = {
            'source': 'notes',
            'notes_dir': notes_dir
        }
        
        # 读取所有笔记文件
        for root, dirs, files in os.walk(notes_dir):
            for file in files:
                if file.endswith(('.md', '.txt', '.pdf')):
                    file_path = os.path.join(root, file)
                    try:
                        if file.endswith('.pdf'):
                            # 简单处理，实际应该使用 PDF 读取库
                            continue
                        else:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                combined_text += f.read() + "\n\n"
                    except Exception as e:
                        print(f"读取文件 {file_path} 失败: {e}")
        
        if not combined_text:
            raise ValueError("没有找到有效的笔记文件")
        
        return await self.extract_style(combined_text, style_name, metadata)
    
    def get_style_references(self, style_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        获取风格参考段落
        """
        # 这里可以实现基于风格向量的检索
        # 从向量数据库中检索与风格向量最相似的段落
        return []