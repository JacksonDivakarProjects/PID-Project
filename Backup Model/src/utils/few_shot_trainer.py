from pathlib import Path
from utils.few_shot_Siamese_Network import TripletNet, EmbeddingNet
from utils.few_shots_triplets_generator import EpisodicTripletDatasetFromDir
from torch.utils.data import DataLoader
import torch
import torch.nn as nn
import torch.optim as optim
import pickle
import logging
from typing import List, Tuple, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FewShotTrainer:
    """
    A class to train few-shot learning models using triplet loss.
    """
    def __init__(self, model: nn.Module, train_dataloader: DataLoader, val_dataloader: DataLoader, output_dir: Path):
        """
        Initializes the FewShotTrainer.

        Args:
            model (nn.Module): The triplet network model to train.
            train_dataloader (DataLoader): DataLoader for the training set.
            val_dataloader (DataLoader): DataLoader for the validation set.
            output_dir (Path): Directory to save training outputs.
        """
        self.model = model
        self.train_dataloader = train_dataloader
        self.val_dataloader = val_dataloader
        self.output_dir = output_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def train(self, epochs: int, criterion: nn.Module, optimizer: optim.Optimizer) -> None:
        """
        Trains the model for a specified number of epochs.

        Args:
            epochs (int): The number of training epochs.
            criterion (nn.Module): The loss function (e.g., TripletLoss).
            optimizer (optim.Optimizer): The optimization algorithm (e.g., Adam).
        """
        best_val_accuracy = 0
        train_losses: List[float] = []
        train_accuracies: List[float] = []
        val_losses: List[float] = []
        val_accuracies: List[float] = []

        logging.info(f"Starting training for {epochs} epochs on {self.device}.")

        for epoch in range(epochs):
            logging.info(f"Epoch {epoch+1}/{epochs}")
            train_loss, train_accuracy = self._train_one_epoch(criterion, optimizer)
            train_losses.append(train_loss)
            train_accuracies.append(train_accuracy)
            logging.info(f"Train Loss: {train_loss:.4f}, Train Accuracy: {train_accuracy:.4f}")

            val_loss, val_accuracy = self._test_one_epoch(criterion)
            val_losses.append(val_loss)
            val_accuracies.append(val_accuracy)
            logging.info(f"Val Loss: {val_loss:.4f}, Val Accuracy: {val_accuracy:.4f}")

            self._save_model(epoch, optimizer)

            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                self._save_best_model(optimizer)

        self._save_training_history(train_losses, train_accuracies, val_losses, val_accuracies)
        logging.info("Training finished.")

    def _train_one_epoch(self, criterion: nn.Module, optimizer: optim.Optimizer) -> Tuple[float, float]:
        """
        Performs one training epoch.

        Args:
            criterion (nn.Module): The loss function.
            optimizer (optim.Optimizer): The optimizer.

        Returns:
            Tuple[float, float]: The average training loss and accuracy for the epoch.
        """
        self.model.train()
        epoch_loss = 0
        epoch_correct = 0

        for A_tensors, P_tensors, N_tensors in self.train_dataloader:
            A_tensors, P_tensors, N_tensors = A_tensors.to(self.device), P_tensors.to(self.device), N_tensors.to(self.device)

            dist_AP, dist_AN, embedded_A, embedded_P, embedded_N = self.model(A_tensors, P_tensors, N_tensors)
            loss = criterion(embedded_A, embedded_P, embedded_N)  # Assuming TripletLoss expects distances and margin
            epoch_loss += loss.item()

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            correct = (dist_AP < dist_AN).sum().item()
            epoch_correct += correct

        avg_loss = epoch_loss / len(self.train_dataloader)
        avg_accuracy = epoch_correct / len(self.train_dataloader.dataset)
        return avg_loss, avg_accuracy

    def _test_one_epoch(self, criterion: nn.Module) -> Tuple[float, float]:
        """
        Performs one validation/testing epoch.

        Args:
            criterion (nn.Module): The loss function.

        Returns:
            Tuple[float, float]: The average validation/testing loss and accuracy for the epoch.
        """
        self.model.eval()
        epoch_loss = 0
        epoch_correct = 0

        with torch.no_grad():
            for A_tensors, P_tensors, N_tensors in self.val_dataloader:
                A_tensors, P_tensors, N_tensors = A_tensors.to(self.device), P_tensors.to(self.device), N_tensors.to(self.device)

                dist_AP, dist_AN, embedded_A, embedded_P, embedded_N = self.model(A_tensors, P_tensors, N_tensors)
                loss = criterion(embedded_A, embedded_P, embedded_N) # Assuming TripletLoss expects distances and margin
                epoch_loss += loss.item()

                correct = (dist_AP < dist_AN).sum().item()
                epoch_correct += correct

        avg_loss = epoch_loss / len(self.val_dataloader)
        avg_accuracy = epoch_correct / len(self.val_dataloader.dataset)
        return avg_loss, avg_accuracy

    def _save_best_model(self, optimizer: optim.Optimizer) -> None:
        """Saves the best model state, optimizer state, and entire model."""
        torch.save(self.model.state_dict(), self.output_dir / "best_fewshot_model_state_dict.pth")
        torch.save(optimizer.state_dict(), self.output_dir / "best_fewshot_optimizer_state_dict.pth")
        torch.save(self.model, self.output_dir / "best_fewshot_model.pth")
        logging.info("Best model saved.")

    def _save_model(self, epoch: int, optimizer: optim.Optimizer) -> None:
        """Saves the model state, optimizer state, and entire model for the current epoch."""
        torch.save(self.model.state_dict(), self.output_dir / f"fewshot_model_state_dict_epoch_{epoch}.pth")
        torch.save(optimizer.state_dict(), self.output_dir / f"fewshot_optimizer_state_dict_epoch_{epoch}.pth")
        torch.save(self.model, self.output_dir / f"fewshot_model_epoch_{epoch}.pth")
        logging.info(f"Model saved at epoch {epoch+1}.")

    def _save_training_history(self, train_losses: List[float], train_accuracies: List[float], val_losses: List[float], val_accuracies: List[float]) -> None:
        """Saves the training history to a pickle file."""
        history = {
            "train_losses": train_losses,
            "train_accuracies": train_accuracies,
            "val_losses": val_losses,
            "val_accuracies": val_accuracies
        }
        with open(self.output_dir / "training_history.pkl", "wb") as f:
            pickle.dump(history, f)
        logging.info("Training history saved.")
