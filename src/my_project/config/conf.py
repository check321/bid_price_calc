"""
配置类模块
包含计算相关的配置参数
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union


@dataclass
class CalculationConfig:
    """计算配置类
    
    属性:
        name (str): 配置名称
        float_a (float): 浮点参数 A
        weight_b (float): 权重参数 B
        float_c3 (float): 浮点参数 C3
    """
    name: str
    float_a: float
    weight_b: float
    float_c3: float
    
    def __post_init__(self):
        """验证参数值的合法性"""
        if not isinstance(self.name, str):
            raise TypeError("name 必须是字符串类型")
        
        for field in ['float_a', 'weight_b', 'float_c3']:
            value = getattr(self, field)
            if not isinstance(value, (int, float)):
                raise TypeError(f"{field} 必须是数值类型")
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'CalculationConfig':
        """从字典创建配置实例"""
        return cls(
            name=config_dict.get('name', '默认配置'),
            float_a=float(config_dict.get('float_a', 0.0)),
            weight_b=float(config_dict.get('weight_b', 1.0)),
            float_c3=float(config_dict.get('float_c3', 0.0))
        )
    
    @classmethod
    def load_configs(cls, json_path: Union[str, Path]) -> List['CalculationConfig']:
        """从JSON文件加载多个配置
        
        Args:
            json_path: JSON配置文件路径
            
        Returns:
            List[CalculationConfig]: 配置实例列表
            
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON格式错误
            ValueError: JSON内容不是数组格式
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {json_path}")
            
        with open(json_path, 'r', encoding='utf-8') as f:
            config_list = json.load(f)
            
        if not isinstance(config_list, list):
            raise ValueError("JSON配置文件必须是数组格式")
            
        return [cls.from_dict(config_dict) for config_dict in config_list]
    
    def to_dict(self) -> dict:
        """将配置转换为字典"""
        return {
            'name': self.name,
            'float_a': self.float_a,
            'weight_b': self.weight_b,
            'float_c3': self.float_c3
        }
    
    @staticmethod
    def save_configs(configs: List['CalculationConfig'], 
                    json_path: Union[str, Path]) -> None:
        """将多个配置保存到JSON文件
        
        Args:
            configs: 配置实例列表
            json_path: 保存配置的JSON文件路径
        """
        json_path = Path(json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_list = [config.to_dict() for config in configs]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(config_list, f, indent=4, ensure_ascii=False) 