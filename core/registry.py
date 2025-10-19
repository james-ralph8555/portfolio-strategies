"""
Strategy Registry

Central registry for discovering and managing all available strategies.
This allows independent contributors to add strategies without conflicts.
"""

from typing import Dict, Type, List, Optional
import importlib
import os
from pathlib import Path


class StrategyRegistry:
    """
    Registry for managing strategy classes and instances.
    
    This registry automatically discovers strategies in the strategies/
    directory and provides a centralized way to access them.
    """
    
    def __init__(self):
        self._strategies: Dict[str, Type] = {}
        self._instances: Dict[str, object] = {}
        self.strategies_path = Path(__file__).parent.parent / "strategies"
        
    def discover_strategies(self) -> None:
        """
        Automatically discover all strategies in the strategies directory.
        """
        if not self.strategies_path.exists():
            return
            
        for strategy_dir in self.strategies_path.iterdir():
            if strategy_dir.is_dir() and not strategy_dir.name.startswith("__"):
                self._load_strategy_from_directory(strategy_dir)
    
    def _load_strategy_from_directory(self, strategy_dir: Path) -> None:
        """
        Load strategy class from a strategy directory.
        
        Args:
            strategy_dir: Path to strategy directory
        """
        strategy_name = strategy_dir.name
        strategy_file = strategy_dir / "strategy.py"
        
        if not strategy_file.exists():
            return
            
        try:
            # Import the strategy module
            module_name = f"strategies.{strategy_name}.strategy"
            module = importlib.import_module(module_name)
            
            # Find strategy class (convention: CamelCase version of directory name)
            class_name = "".join(word.capitalize() for word in strategy_name.split("_"))
            if hasattr(module, class_name):
                strategy_class = getattr(module, class_name)
                self._strategies[strategy_name] = strategy_class
                
        except ImportError as e:
            print(f"Warning: Could not import strategy {strategy_name}: {e}")
    
    def register_strategy(self, name: str, strategy_class: Type) -> None:
        """
        Manually register a strategy class.
        
        Args:
            name: Strategy name
            strategy_class: Strategy class
        """
        self._strategies[name] = strategy_class
    
    def get_strategy_class(self, name: str) -> Optional[Type]:
        """
        Get strategy class by name.
        
        Args:
            name: Strategy name
            
        Returns:
            Strategy class or None if not found
        """
        return self._strategies.get(name)
    
    def create_strategy(self, name: str, config: Optional[Dict] = None) -> Optional[object]:
        """
        Create an instance of a strategy.
        
        Args:
            name: Strategy name
            config: Strategy configuration
            
        Returns:
            Strategy instance or None if not found
        """
        strategy_class = self.get_strategy_class(name)
        if strategy_class:
            return strategy_class(config)
        return None
    
    def list_strategies(self) -> List[str]:
        """
        List all available strategy names.
        
        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())
    
    def get_strategy_info(self, name: str) -> Optional[Dict]:
        """
        Get information about a strategy.
        
        Args:
            name: Strategy name
            
        Returns:
            Dictionary with strategy information
        """
        strategy_class = self.get_strategy_class(name)
        if not strategy_class:
            return None
            
        # Try to get info from strategy instance
        try:
            instance = strategy_class()
            return {
                "name": getattr(instance, "name", name),
                "assets": getattr(instance, "assets", []),
                "rebalance_frequency": getattr(instance, "rebalance_frequency", "unknown"),
                "description": getattr(instance, "__doc__", "").strip()
            }
        except Exception:
            return {
                "name": name,
                "assets": [],
                "rebalance_frequency": "unknown",
                "description": "Strategy information unavailable"
            }


# Global registry instance
registry = StrategyRegistry()