from abc import ABC, abstractmethod
from typing import List, Dict

class BaseOptimizer(ABC):
    """所有优化器的基础抽象类"""
    
    @abstractmethod
    def optimize(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """接收并返回优化后的 messages"""
        pass