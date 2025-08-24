import os
import random
from pathlib import Path
from typing import Union, Optional, Callable, Tuple, List
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision.io import decode_image
from torchvision.transforms import v2

#####################################
# # 2 ways to generate triplets:
####################################
# # 1. EpisodicTripletDatasetFromDir: Generates a fixed number of triplets (episodes) randomly sampled from the entire dataset.
# # 2. TripletDatasetFromDir: Number of triplets = number of images in the dataset.

class EpisodicTripletDatasetFromDir(Dataset):
    """
    PyTorch Dataset for generating triplets (anchor, positive, negative) for Siamese network training.
    
    Expects a directory structure where each subfolder is a class containing images.
    The anchor and positive samples come from the same class, while the negative sample is drawn
    from a different class.
    
    Instead of one triplet per anchor image, the dataset produces a fixed number (episodes)
    of triplets randomly sampled from the entire dataset.
    
    Args:
        root_dir (Union[str, Path]): Root directory containing subfolders for each class.
        transform (Optional[Callable], optional): A function/transform to apply to the images.
        episodes (int, optional): Total number of triplets (episodes) to be generated.
            Default is 1000.
    
    Returns:
        Tuple[torch.Tensor, torch.Tensor, torch.Tensor]: A triplet (anchor, positive, negative).
    """
    def __init__(self, root_dir: Union[str, Path], transform: Optional[Callable] = None, episodes: int = 1000) -> None:
        self.root_dir = Path(root_dir) if not isinstance(root_dir, Path) else root_dir
        self.transform = transform
        self.episodes = episodes
        self.class_to_images = {}  # Mapping from class label to list of image paths
        self.image_list: List[Tuple[str, Path]] = []  # List of tuples: (class_label, image_path)
        
        for class_folder in self.root_dir.iterdir():
            if class_folder.is_dir():
                class_label = class_folder.name
                images = list(class_folder.glob("*"))
                if images:
                    self.class_to_images[class_label] = images
                    for img_path in images:
                        self.image_list.append((class_label, img_path))
                else:
                    print(f"⚠️ Warning: No images found in class folder {class_folder}")
        
        if not self.image_list:
            raise ValueError(f"No images found in any subfolder of {self.root_dir}")
            
    def __len__(self) -> int:
        return self.episodes
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # Randomly sample an anchor from the full list
        anchor_label, anchor_path = random.choice(self.image_list)
        # anchor_img = decode_image(str(anchor_path))
        anchor_img = decode_image_from_path(str(anchor_path)) # C,H,W and uint8
        anchor_img = anchor_img.float()/ 255.0 # normalize to [0,1]
        
        # Choose a positive sample from the same class, ensuring it's different if possible
        positive_candidates = self.class_to_images[anchor_label].copy()
        if anchor_path in positive_candidates:
            positive_candidates.remove(anchor_path)
        if positive_candidates:
            positive_path = random.choice(positive_candidates)
        else:
            positive_path = anchor_path
            print(f"⚠️ Only one image in class '{anchor_label}'. Using anchor as positive.")
        # positive_img = decode_image(str(positive_path))
        positive_img = decode_image_from_path(str(positive_path))
        positive_img = positive_img.float()/ 255.0 # normalize to [0,1]
        
        # Choose a negative sample from a different class
        negative_classes = [cls for cls in self.class_to_images.keys() if cls != anchor_label]
        if not negative_classes:
            raise ValueError("Only one class available in dataset; cannot sample negative.")
        negative_class = random.choice(negative_classes)
        negative_path = random.choice(self.class_to_images[negative_class])
        # negative_img = decode_image(str(negative_path))
        negative_img = decode_image_from_path(str(negative_path))
        negative_img = negative_img.float()/255.0 # normalize to [0,1]
        
        if self.transform:
            anchor_img = self.transform(anchor_img)
            positive_img = self.transform(positive_img)
            negative_img = self.transform(negative_img)
        
        return anchor_img, positive_img, negative_img
    

class TripletDatasetFromDir(Dataset):
    """
    PyTorch Dataset for generating triplets (anchor, positive, negative) for Siamese network training.
    
    Expects a directory structure where each subfolder is a class containing images. 
    The anchor and positive samples come from the same class, while the negative sample is drawn
    from a different class.
    
    Args:
        root_dir (Union[str, Path]): Root directory containing subfolders for each class.
        transform (Optional[Callable], optional): A function/transform to apply to the images.
    
    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: A triplet (anchor, positive, negative).
    """
    def __init__(self, root_dir: Union[str, Path], transform: Optional[Callable] = None) -> None:
        self.root_dir = Path(root_dir) if not isinstance(root_dir, Path) else root_dir
        self.transform = transform
        self.class_to_images = {}  # Mapping from class label to list of image paths
        self.image_list: List[Tuple[str, Path]] = []  # List of tuples: (class_label, image_path)
        
        for class_folder in self.root_dir.iterdir():
            if class_folder.is_dir():
                class_label = class_folder.name
                images = list(class_folder.glob("*"))
                if images:
                    self.class_to_images[class_label] = images
                    for img_path in images:
                        self.image_list.append((class_label, img_path))
                else:
                    print(f"⚠️ Warning: No images found in class folder {class_folder}")
                    
        if not self.image_list:
            raise ValueError(f"No images found in any subfolder of {self.root_dir}")
            
    def __len__(self) -> int:
        return len(self.image_list)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # Get the anchor sample
        anchor_label, anchor_path = self.image_list[idx]
        # anchor_img = decode_image(str(anchor_path))
        anchor_img = decode_image_from_path(str(anchor_path))
        
        # Choose a positive sample from the same class (different file, if available)
        positive_candidates = self.class_to_images[anchor_label].copy()
        if anchor_path in positive_candidates:
            positive_candidates.remove(anchor_path)
        if positive_candidates:
            positive_path = random.choice(positive_candidates)
        else:
            positive_path = anchor_path
            print(f"⚠️ Only one image in class '{anchor_label}'. Using anchor as positive.")
        # positive_img = decode_image(str(positive_path))
        positive_img = decode_image_from_path(str(positive_path))

        # Choose a negative sample from a different class
        negative_classes = [cls for cls in self.class_to_images.keys() if cls != anchor_label]
        if not negative_classes:
            raise ValueError("Only one class available in dataset; cannot sample negative.")
        negative_class = random.choice(negative_classes)
        negative_path = random.choice(self.class_to_images[negative_class])
        # negative_img = decode_image(str(negative_path))
        negative_img = decode_image_from_path(str(negative_path))
        
        # Optionally apply the transform
        if self.transform:
            anchor_img = self.transform(anchor_img)
            positive_img = self.transform(positive_img)
            negative_img = self.transform(negative_img)

        return anchor_img, positive_img, negative_img


## helper function to decode image from path
def decode_image_from_path(image_path):
    with open(image_path, 'rb') as f:
        img_bytes = f.read()
    img_tensor = torch.tensor(list(img_bytes), dtype=torch.uint8)
    image = decode_image(img_tensor) 

    return image