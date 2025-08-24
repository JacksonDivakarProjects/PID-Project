from pathlib import Path
import random
import shutil
from typing import List, Dict, Tuple, Optional
from utils.helpers import get_files
import logging


class FewShotDatasetBuilder:
    def __init__(self, crops_root_dir: Path):
        """
        Initialize the FewShotDatasetBuilder.

        Args:
            crops_root_dir (Path): Path to the root directory containing symbol crops.
        """
        self.crops_root_dir = crops_root_dir
        self.logger = logging.getLogger(__name__)

    def _validate_data(self) -> bool:
        """
        Validate the data in the crops directory.

        Returns:
            bool: True if validation is successful, False otherwise.
        """
        if len(get_files(self.crops_root_dir, extensions=['.jpg', '.png', '.jpeg'])) == 0:
            raise FileNotFoundError(f"Directory {self.crops_root_dir} is empty.")
        
        # Check if there are any subdirectories (classes) in the crops directory
        class_dirs = [d for d in self.crops_root_dir.iterdir() if d.is_dir()]
        if not class_dirs:
            raise ValueError("No class directories found in the symbol crops directory.")

        return True

    def create_support_set(self, k: int, output_dir: Path) -> None:
        """
        Create a k-shot dataset from the symbol crops.

        Args:
            k (int): Number of samples per class in the support set.
            output_dir (Path): Directory to save the k-shot dataset.
        """

        if not self._validate_data():
            self.logger.error("Data validation failed. Please check your images and labels.")
            return
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        class_dirs = [d for d in self.crops_root_dir.iterdir() if d.is_dir()]
        for class_dir in class_dirs:
            class_id = class_dir.name
            image_paths = get_files(class_dir, extensions=['.jpg', '.png', '.jpeg'])
            if len(image_paths) == 0:
                print(f"❌ No images found in class '{class_id}' — skipping this class.")
                continue
            elif len(image_paths) < k:
                print(f"⚠️ Class '{class_id}' has only {len(image_paths)} images — using all available.")
                selected = image_paths
            else:
                selected = random.sample(image_paths, k)

            saved_dir = output_dir / class_id
            saved_dir.mkdir(parents=True, exist_ok=True)
            for image_path in selected:
                shutil.copy2(image_path, saved_dir / image_path.name)

        print(f"✅ Support set created at: {output_dir}")

