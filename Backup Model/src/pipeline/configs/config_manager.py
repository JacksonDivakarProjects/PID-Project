import yaml
from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import logging

class ConfigManager:
    def __init__(self, config_path: Union[str, Path]):
        """
        Initializes the ConfigManager with a YAML configuration file.

        Args:
            config_path (Union[str, Path]): Path to the YAML configuration file.
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._create_directories()

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads the YAML configuration file.

        Returns:
            Dict[str, Any]: The loaded configuration as a dictionary.
        """
        try: 
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            logging.error(f"❌ Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"❌ Error parsing YAML file: {self.config_path}\n{e}")
            raise
    
    def _create_directories(self) -> None:
        """
        Creates necessary directories specified in the configuration.
        """
        paths = self.get_data_paths()
        model_paths = self.get_model_paths()

        # create data directories
        for path in paths.values():
            if not Path(path).exists():
                Path(path).mkdir(parents=True, exist_ok=True)
        
        # create model directories
        for path in model_paths.values():
            # check if the path is a directory
            if not Path(path).is_dir() and not Path(path).exists():
                Path(path).mkdir(parents=True, exist_ok=True)
    
    def get_data_paths(self) -> Dict[str, Path]:
        """
        Retrieves data paths from the configuration.

        Returns:
            Dict[str, Path]: A dictionary of data paths.
        """
        root_dir = Path(self.config['data']['root_dir'])
        return {
            'raw_images_dir': root_dir / self.config['data']['raw']['raw_images_dir'],
            'raw_class_aware_labels_dir': root_dir / self.config['data']['raw']['raw_class_aware_labels_dir'],
            'raw_class_agnostic_labels_dir': root_dir / self.config['data']['raw']['raw_class_agnostic_labels_dir'],
            'class_agnostic_patches_dir': root_dir / self.config['data']['processed']['stage_1']['class_agnostic_patches_dir'],
            'class_aware_patches_dr': root_dir / self.config['data']['processed']['stage_1']['class_aware_patches_dir'],
            'class_agnostic_yolo_train_dir': root_dir / self.config['data']['processed']['stage_1']['class_agnostic_yolo_train_dir'],
            'class_aware_yolo_train_dir': root_dir / self.config['data']['processed']['stage_1']['class_aware_yolo_train_dir'],
            'symbol_crops_dir': root_dir / self.config['data']['processed']['stage_2']['symbol_crops_dir'],
            'few_shot_dir': root_dir / self.config['data']['processed']['stage_2']['few_shot_dir'],
            'class_agnostic_results_dir': self.config['data']['results']['stage_1']['class_agnostic_results_dir'],
            'class_aware_results_dir': self.config['data']['results']['stage_1']['class_aware_results_dir'],
            'few_shot_results_dir': self.config['data']['results']['stage_2']['few_shot_results_dir'],

        }
    
    def get_model_paths(self) -> Dict[str, Path]:
        """
        Retrieves model paths from the configuration.

        Returns:
            Dict[str, Path]: A dictionary of model paths.
        """
        root_dir = Path(self.config['models']['root_dir'])
        return {
            'base_yolo_path': root_dir / self.config['models']['base_yolo_path'],
            'stage1_class_agnostic_weights_dir': root_dir / self.config['models']['stage1_class_agnostic_weights_dir'],
            'stage1_class_aware_weights_dir': root_dir / self.config['models']['stage1_class_aware_weights_dir'],
            'stage2_few_shot_weights_dir': root_dir / self.config['models']['stage2_few_shot_weights_dir']
        }

    def get_training_config(self) -> Dict[str, Any]:
        """Get training configuration."""
        return self.config['training']
    
    def get_symbol_detection_config(self) -> Dict[str, Any]:
        """Get symbol detection configuration."""
        return self.config['symbol_detection']
    
    def get_few_shot_config(self) -> Dict[str, Any]:
        """Get few-shot classification configuration."""
        return self.config['few_shot']
    
    def create_directories(self) -> None:
        """Create all necessary directories."""
        paths = self.get_data_paths()
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True) 
        
        model_paths = self.get_model_paths()
        for path in model_paths.values():
            path.mkdir(parents=True, exist_ok=True)
        logging.info("✅ All necessary directories have been created.")

    def get_stage1_inference_config(self) -> Dict[str, Any]:
        """Get stage 1 inference configuration."""
        return self.config['stage1_inference']
    
    def get_stage2_inference_config(self) -> Dict[str, Any]:
        """Get stage 2 few-shot inference configuration."""
        return self.config['stage2_inference']
    

        