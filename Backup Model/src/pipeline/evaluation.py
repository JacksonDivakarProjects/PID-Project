from pipeline.base import BasePipeline
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from utils.metrics import MetricsCalculator
from utils.helpers import get_files, get_text_files

class EvaluationPipeline(BasePipeline):
    """Evaluation pipeline for the model."""

    def __init__(self, config_path: str = "configs/config.yaml"):
        """Initialize evaluation pipeline.

        Args:
            config_path: Path to configuration file
        """
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)

    def validate(self) -> bool:
        """Validate evaluation pipeline inputs.

        Returns:
            bool: True if validation passes, False otherwise
        """
        paths = self.get_data_paths()
        model_paths = self.get_model_paths()

        # Check if evaluation data directories exist
        if not paths['raw_images_dir'].exists() or not paths['raw_class_aware_labels_dir'].exists():
            raise FileNotFoundError("Evaluation data directories not found")

        # Check if model directory exists
        if not model_paths['stage2_few_shot_weights_dir'].exists():
            raise FileNotFoundError("Model directory not found")
        
        # check if gt and pred files exist
        if not Path(paths['few_shot_results_dir']).exists() or len(get_text_files(paths['few_shot_results_dir'])) == 0:
            raise FileNotFoundError("Prediction results do not exist")
        if not Path(paths['raw_class_aware_labels_dir']).exists() or len(get_text_files(paths['raw_class_aware_labels_dir'])) == 0:
            raise FileNotFoundError("Ground truth labels do not exist")
        
        return True
    
    def compute_stage1_metrics(self):
        """Compute stage 1 metrics."""
        paths = self.get_data_paths()
        metrics_calculator = MetricsCalculator()

        # compute class agnostic metrics
        self.logger.info("Computing Stage 1 metrics")
        class_agnostic_performance = metrics_calculator.calculate_overall_metrics_for_dataset_dir(paths['class_agnostic_results_dir'], paths['raw_class_agnostic_labels_dir'])
        print("Sheet-wise performance: ", class_agnostic_performance)
        overall_precision = 0
        overall_recall = 0
        overall_f1 = 0
        print("Stage 1 metrics:")
        for txt_name, metrics in class_agnostic_performance.items():
            overall_precision += metrics['precision']
            overall_recall += metrics['recall']
            overall_f1 += metrics['f1']
        
        overall_precision /= len(class_agnostic_performance)
        overall_recall /= len(class_agnostic_performance)
        overall_f1 /= len(class_agnostic_performance)

        print("Overall precision: ", overall_precision)
        print("Overall recall: ", overall_recall)
        print("Overall f1: ", overall_f1)
        self.logger.info("Stage 1 metrics computed successfully")
    
    def compute_stage2_metrics(self):
        """Compute stage 2 metrics."""
        paths = self.get_data_paths()
        metrics_calculator = MetricsCalculator()

        # compute overall metrics
        self.logger.info("Computing Stage 2 metrics")
        overall_performance = metrics_calculator.calculate_overall_metrics_for_dataset_dir(paths['few_shot_results_dir'], paths['raw_class_aware_labels_dir'])
        print("Sheet-wise performance: ", overall_performance)
        overall_precision = 0
        overall_recall = 0
        overall_f1 = 0
        print("Stage 2 metrics:")
        for txt_name, metrics in overall_performance.items():
            overall_precision += metrics['precision']
            overall_recall += metrics['recall']
            overall_f1 += metrics['f1']
        
        overall_precision /= len(overall_performance)
        overall_recall /= len(overall_performance)
        overall_f1 /= len(overall_performance)
        print("Overall precision: ", overall_precision)
        print("Overall recall: ", overall_recall)
        print("Overall f1: ", overall_f1)
        self.logger.info("Stage 2 metrics computed successfully")


    def run(self) -> None:
        """Run the evaluation pipeline."""
        self.logger.info("Starting evaluation pipeline")
        
        # Validate inputs
        if not self.validate():
            self.logger.error("Validation failed")
            return
        
        # Compute metrics for stage 1
        self.compute_stage1_metrics()
        
        # Compute metrics for stage 2 (if applicable)
        self.compute_stage2_metrics()

        self.logger.info("Evaluation pipeline completed successfully")
                                               