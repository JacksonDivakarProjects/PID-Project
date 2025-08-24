import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision

class TripletNet(nn.Module):
    def __init__(self, embedding_net):
        super(TripletNet, self).__init__()
        self.embedding_net = embedding_net

    def forward(self, a, p, n):
        embedded_A = self.embedding_net(a)
        embedded_P = self.embedding_net(p)
        embedded_N = self.embedding_net(n)

        dist_AP = F.pairwise_distance(embedded_A, embedded_P, 2) # 2 is for L2 norm
        dist_AN = F.pairwise_distance(embedded_A, embedded_N, 2)

        return dist_AP, dist_AN, embedded_A, embedded_P, embedded_N

class EmbeddingNet(nn.Module):
    def __init__(self, embedding_size: int, use_pretrained: bool=True):
        super(EmbeddingNet, self).__init__()
        self.embedding_size = embedding_size
        if use_pretrained:
            self.convnet = torchvision.models.resnet50(weights='IMAGENET1K_V1')
        else:
            self.convnet = torchvision.models.resnet50(weights=None)

        # Get the input dimension of last layer
        self.fc_in_features = self.convnet.fc.in_features
        
        # Remove the last layer
        self.convnet = nn.Sequential(*list(self.convnet.children())[:-1])

        # Add linear layers
        self.fc = nn.Sequential(
            nn.Linear(self.fc_in_features, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, self.embedding_size)   
        )

    def forward(self, x):
        x = self.convnet(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x
