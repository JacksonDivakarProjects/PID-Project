from pipeline.base import BasePipeline
from utils.bbox_utils import BBoxUtils
from utils.few_shot_dataset_builder import FewShotDatasetBuilder
from utils.few_shot_trainer import FewShotTrainer
from utils.few_shot_Siamese_Network import TripletNet, EmbeddingNet
from utils.few_shots_triplets_generator import EpisodicTripletDatasetFromDir
from torch.utils.data import DataLoader
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision.transforms import v2
from typing import Dict, Any


class Stage2FewShotPipeline(BasePipeline):
    def __init__(self, config_path: str = "configs/config.yaml"):
        super().__init__(config_path)
        # self.few_shot_classifier = None
        self.dataset_builder = None
        
    def validate(self) -> bool:
        """Validate stage 2 pipeline inputs."""
        paths = self.get_data_paths()
        model_paths = self.get_model_paths()
        
        # Check if stage 1 model dir exists
        if not model_paths['stage1_class_agnostic_weights_dir'].exists():
            raise FileNotFoundError("Stage 1 model directory not found")
            
        # Check if raw data directories exist
        if not paths['raw_images_dir'].exists() or not paths['raw_class_aware_labels_dir'].exists():
            raise FileNotFoundError("Raw data directories not found")
            
        return True
    
    def prepare_symbol_crops(self) -> None:
        """Extract symbol crops from detected bounding boxes."""
        paths = self.get_data_paths()
        
        # Extract symbol crops
        BBoxUtils.extract_bbox_crops(
            image_dir=paths['raw_images_dir'],
            label_dir=paths['raw_class_aware_labels_dir'],
            output_dir=paths['symbol_crops_dir']
            
        )
    
    def prepare_few_shot_data(self) -> None:
        """Prepare data for few-shot classification."""
        config = self.get_few_shot_config()
        paths = self.get_data_paths()
        
        # Initialize dataset builder
        self.dataset_builder = FewShotDatasetBuilder(crops_root_dir=paths['symbol_crops_dir'])
        
        # Create support set
        self.dataset_builder.create_support_set(k=config['support_set_size'], output_dir=paths['few_shot_dir'])
    
    def train_model(self) -> None:
        """Train the few-shot model."""
        paths = self.get_data_paths()
        model_paths = self.get_model_paths()
        config = self.get_few_shot_config()

        # Initialize model
        embedding_net = EmbeddingNet(embedding_size=config['embedding_size'])
        device = "cuda" if torch.cuda.is_available() else "cpu"
        embedding_net.to(device)
        model = TripletNet(embedding_net)
        model.to(device)

        # Initialize parameters        
        train_val_split = config['train_val_split']
        epochs = config['epochs']
        batch_size = config['batch_size']
        criterion = nn.TripletMarginLoss(margin=config['margin'], p=2)
        optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])
        apn_transform = v2.Compose([
            v2.Resize(size=(128, 128), antialias=True),
            # v2.ToDtype(torch.float32, scale=True),
            v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            v2.RandomHorizontalFlip(p=0.2),
            v2.RandomVerticalFlip(p=0.2),
            v2.RandomRotation(degrees=15),
        ])

        # Initialize dataset and dataloader
        num_train_episodes = int(config['num_episodes'] * train_val_split[0])
        num_val_episodes = int(config['num_episodes'] * train_val_split[1])

        train_dataset = EpisodicTripletDatasetFromDir(paths['few_shot_dir'], apn_transform, num_train_episodes)
        val_dataset = EpisodicTripletDatasetFromDir(paths['few_shot_dir'], apn_transform, num_val_episodes)

        train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_dataloader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Initialize trainer
        output_dir = model_paths['stage2_few_shot_weights_dir']
        trainer = FewShotTrainer(model, train_dataloader, val_dataloader, output_dir)
        trainer.train(epochs, criterion, optimizer)

    
    def run(self) -> None:
        """Run the complete stage 2 pipeline."""
        if not self.validate():
            raise ValueError("Pipeline validation failed")
            
        print("Extracting symbol crops...")
        self.prepare_symbol_crops()
        
        print("Preparing few-shot data...")
        self.prepare_few_shot_data()
        
        print("Training few-shot classifier...")
        self.train_model()
        
        print("Stage 2 pipeline completed successfully") 