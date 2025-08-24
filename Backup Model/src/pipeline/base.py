from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union, Any, Dict, Tuple, Callable
from pipeline.configs.config_manager import ConfigManager


class BasePipeline(ABC):
    """Base class for all pipeline stages."""
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        """Initialize pipeline stage.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        
    @abstractmethod
    def run(self) -> None:
        """Run the complete pipeline stage."""
        pass
        
    @abstractmethod
    def validate(self) -> bool:
        """Validate pipeline stage inputs and configuration.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        pass
        
    def get_data_paths(self) -> Dict[str, Path]:
        """Get data paths from configuration.
        
        Returns:
            Dict[str, Path]: Dictionary of data paths
        """
        return self.config_manager.get_data_paths()
        
    def get_model_paths(self) -> Dict[str, Path]:
        """Get model paths from configuration.
        
        Returns:
            Dict[str, Path]: Dictionary of model paths
        """
        return self.config_manager.get_model_paths()
        
    def get_training_config(self) -> Dict[str, Any]:
        """Get training configuration.
        
        Returns:
            Dict[str, Any]: Training configuration
        """
        return self.config_manager.get_training_config()
        
    def get_symbol_detection_config(self) -> Dict[str, Any]:
        """Get symbol detection configuration.
        
        Returns:
            Dict[str, Any]: Symbol detection configuration
        """
        return self.config_manager.get_symbol_detection_config()
        
    def get_few_shot_config(self) -> Dict[str, Any]:
        """Get few-shot classification configuration.
        
        Returns:
            Dict[str, Any]: Few-shot classification configuration
        """
        return self.config_manager.get_few_shot_config()
    
    def get_stage1_inference_config(self) -> Dict[str, Any]:
        """Get stage 1 inference configuration.
        
        Returns:
            Dict[str, Any]: Stage 1 inference configuration
        """
        return self.config_manager.get_stage1_inference_config()
        
    def get_stage2_inference_config(self) -> Dict[str, Any]:
        """Get stage 2 inference configuration.
        
        Returns:
            Dict[str, Any]: Stage 2 inference configuration
        """
        return self.config_manager.get_stage2_inference_config()