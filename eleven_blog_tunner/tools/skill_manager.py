"""
Skill 管理器
负责存储总结的 Skill 列表
"""
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    examples: List[str]
    parameters: Dict[str, Any]


class SkillManager:
    """Skill 管理器"""
    
    def __init__(self, storage_path: str = "./data/skills.json"):
        self.storage_path = storage_path
        self._skills: Dict[str, Skill] = {}
    
    def add_skill(self, skill: Skill):
        """添加技能"""
        self._skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Skill:
        """获取技能"""
        return self._skills.get(name)
    
    def list_skills(self) -> List[Skill]:
        """列出所有技能"""
        return list(self._skills.values())
    
    def save(self):
        """保存到文件"""
        data = {name: asdict(skill) for name, skill in self._skills.items()}
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for name, skill_data in data.items():
                self._skills[name] = Skill(**skill_data)
        except FileNotFoundError:
            pass
