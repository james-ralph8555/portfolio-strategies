"""
Base Strategy Interface

All strategies must implement this interface to ensure compatibility
with the backtesting framework and portfolio management system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This interface ensures that all strategies can be used consistently
    across the portfolio management and backtesting systems.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize strategy with configuration.
        
        Args:
            config: Strategy-specific configuration dictionary
        """
        self.config = config or {}
        self.name = ""
        self.assets = []
        self.rebalance_frequency = "monthly"
        self.drift_bands = 10
        
    @abstractmethod
    def calculate_weights(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate target weights for all assets in the strategy.
        
        Args:
            data: Market data with returns and other required metrics
            
        Returns:
            Dictionary mapping asset symbols to target weights
        """
        pass
    
    @abstractmethod
    def should_rebalance(self, current_weights: Dict[str, float], 
                        target_weights: Dict[str, float]) -> bool:
        """
        Determine if rebalancing is required.
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target weights from strategy
            
        Returns:
            True if rebalancing should occur
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate strategy configuration.
        
        Returns:
            True if configuration is valid
        """
        pass
    
    def get_assets(self) -> List[str]:
        """
        Get list of assets used by this strategy.
        
        Returns:
            List of asset symbols
        """
        return self.assets.copy()
    
    def get_name(self) -> str:
        """
        Get strategy name.
        
        Returns:
            Strategy name
        """
        return self.name
    
    def get_config(self) -> Dict:
        """
        Get strategy configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def update_config(self, new_config: Dict) -> None:
        """
        Update strategy configuration.
        
        Args:
            new_config: New configuration parameters
        """
        self.config.update(new_config)
        self.validate_config()
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess market data before weight calculation.
        
        Args:
            data: Raw market data
            
        Returns:
            Preprocessed data
        """
        # Default implementation - can be overridden by strategies
        return data.copy()
    
    def postprocess_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Postprocess calculated weights before returning.
        
        Args:
            weights: Raw calculated weights
            
        Returns:
            Final weights after processing
        """
        # Default implementation - can be overridden by strategies
        return weights.copy()