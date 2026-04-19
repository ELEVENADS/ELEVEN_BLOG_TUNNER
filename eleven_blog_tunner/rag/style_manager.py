"""
风格管理模块

负责风格的存储、检索、更新和删除
支持将风格注册为技能供 Agent 使用
"""
import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
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
        style_info = await self.learner.learn_style(text)
        
        style_data = {
            'name': style_name,
            'features': style_info['features'],
            'vector': style_info['vector'],
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'sample_count': 1,
            'total_chars': len(text)
        }
        
        await self._save_style(style_name, style_data)
        await self._register_style_as_skill(style_name, style_data)
        
        return style_data
    
    async def update_style(self, style_name: str, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        更新风格（增量学习）
        
        Args:
            style_name: 风格名称
            text: 新的文本内容
            metadata: 元数据
        
        Returns:
            更新后的风格信息
        """
        existing_style = await self.load_style(style_name)
        
        new_features = await self.learner.learn_style(text)
        
        existing_features = existing_style['features']
        new_features_dict = new_features['features']
        
        sample_count = existing_style.get('sample_count', 1) + 1
        total_chars = existing_style.get('total_chars', 0) + len(text)
        
        alpha = 1.0 / sample_count
        
        averaged_features = {}
        for key in existing_features:
            old_val = existing_features.get(key, 0.0)
            new_val = new_features_dict.get(key, 0.0)
            averaged_features[key] = round(old_val * (1 - alpha) + new_val * alpha, 4)
        
        existing_vector = existing_style['vector']
        new_vector = new_features['vector']
        
        min_len = min(len(existing_vector), len(new_vector))
        averaged_vector = [
            round(existing_vector[i] * (1 - alpha) + new_vector[i] * alpha, 4)
            for i in range(min_len)
        ]
        
        if len(new_vector) > min_len:
            averaged_vector.extend(new_vector[min_len:])
        
        if metadata:
            existing_style['metadata'].update(metadata)
        
        existing_style['features'] = averaged_features
        existing_style['vector'] = averaged_vector
        existing_style['sample_count'] = sample_count
        existing_style['total_chars'] = total_chars
        existing_style['updated_at'] = datetime.now().isoformat()
        
        await self._save_style(style_name, existing_style)
        
        return existing_style
    
    async def load_style(self, style_name: str) -> Dict[str, Any]:
        """
        加载风格
        """
        style_path = self.style_storage / f"{style_name}.json"
        if not style_path.exists():
            raise FileNotFoundError(f"风格 {style_name} 不存在")
        
        with open(style_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def list_styles(self) -> List[Dict[str, Any]]:
        """
        列出所有风格
        """
        styles = []
        for style_file in self.style_storage.glob("*.json"):
            try:
                with open(style_file, 'r', encoding='utf-8') as f:
                    style_data = json.load(f)
                    styles.append({
                        'name': style_data.get('name', style_file.stem),
                        'created_at': style_data.get('created_at'),
                        'updated_at': style_data.get('updated_at'),
                        'sample_count': style_data.get('sample_count', 0),
                        'total_chars': style_data.get('total_chars', 0)
                    })
            except Exception as e:
                continue
        
        styles.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return styles
    
    async def delete_style(self, style_name: str) -> bool:
        """
        删除风格
        """
        style_path = self.style_storage / f"{style_name}.json"
        if not style_path.exists():
            return False
        
        try:
            style_path.unlink()
            await self._unregister_style_skill(style_name)
            return True
        except Exception:
            return False
    
    async def get_style_references(self, style_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        获取风格参考段落
        
        从风格的样本中提取代表性段落
        """
        style_data = await self.load_style(style_name)
        
        references = []
        
        sample_file = self.style_storage / f"{style_name}_samples.json"
        if sample_file.exists():
            try:
                with open(sample_file, 'r', encoding='utf-8') as f:
                    samples = json.load(f)
                    references = samples[:top_k]
            except Exception:
                pass
        
        return references
    
    async def add_style_sample(self, style_name: str, text: str) -> Dict[str, Any]:
        """
        添加风格样本
        """
        style_data = await self.load_style(style_name)
        
        sample_file = self.style_storage / f"{style_name}_samples.json"
        samples = []
        if sample_file.exists():
            try:
                with open(sample_file, 'r', encoding='utf-8') as f:
                    samples = json.load(f)
            except Exception:
                samples = []
        
        sample_entry = {
            'text': text[:500],
            'char_count': len(text),
            'added_at': datetime.now().isoformat()
        }
        samples.append(sample_entry)
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
        
        return await self.update_style(style_name, text)
    
    async def compare_styles(self, style_name1: str, style_name2: str) -> float:
        """
        比较两种风格的相似度
        """
        style1 = await self.load_style(style_name1)
        style2 = await self.load_style(style_name2)
        
        return self.learner.compare_styles(style1, style2)
    
    async def _save_style(self, style_name: str, style_data: Dict[str, Any]):
        """
        保存风格到文件
        """
        style_path = self.style_storage / f"{style_name}.json"
        
        save_data = {
            'name': style_data['name'],
            'features': style_data['features'],
            'vector': style_data['vector'],
            'metadata': style_data.get('metadata', {}),
            'created_at': style_data.get('created_at', datetime.now().isoformat()),
            'updated_at': style_data.get('updated_at', datetime.now().isoformat()),
            'sample_count': style_data.get('sample_count', 1),
            'total_chars': style_data.get('total_chars', 0)
        }
        
        with open(style_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    
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
        
        try:
            await self.skill_manager.add_skill(skill_data)
        except Exception as e:
            print(f"注册风格技能失败: {e}")
    
    async def _unregister_style_skill(self, style_name: str):
        """
        注销风格技能
        """
        try:
            skill_name = f"style_{style_name}"
            await self.skill_manager.remove_skill(skill_name)
        except Exception as e:
            print(f"注销风格技能失败: {e}")
    
    async def extract_style_from_notes(self, notes_dir: str, style_name: str) -> Dict[str, Any]:
        """
        从笔记目录提取风格
        """
        combined_text = ""
        metadata = {
            'source': 'notes',
            'notes_dir': notes_dir
        }
        
        for root, dirs, files in os.walk(notes_dir):
            for file in files:
                if file.endswith(('.md', '.txt')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            combined_text += f.read() + "\n\n"
                    except Exception as e:
                        print(f"读取文件 {file_path} 失败: {e}")
        
        if not combined_text:
            raise ValueError("没有找到有效的笔记文件")
        
        return await self.extract_style(combined_text, style_name, metadata)
    
    async def preview_style(self, text: str, style_name: str = None) -> Dict[str, Any]:
        """
        预览风格特征（不保存）
        """
        features = await self.learner.learn_style(text)
        
        result = {
            'features': features['features'],
            'vector_length': len(features['vector'])
        }
        
        if style_name:
            try:
                existing_style = await self.load_style(style_name)
                similarity = self.learner.compare_styles(existing_style, features)
                result['similarity'] = round(similarity, 4)
            except FileNotFoundError:
                result['similarity'] = None
        
        return result
