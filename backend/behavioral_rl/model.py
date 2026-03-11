import torch
import torch.nn as nn


class BehavioralScoreNet(nn.Module):
    """
    Behavioral score policy head:
    s = 1 + 4 * sigmoid(f_theta(x))
    Optionally predicts log variance for uncertainty estimates.
    """

    def __init__(self, input_dim: int, hidden_dim: int = 128, dropout: float = 0.15):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.mean_head = nn.Linear(hidden_dim // 2, 1)
        self.log_var_head = nn.Linear(hidden_dim // 2, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.backbone(x)
        score = 1.0 + 4.0 * torch.sigmoid(self.mean_head(h))
        log_var = torch.clamp(self.log_var_head(h), min=-6.0, max=3.0)
        return score.squeeze(-1), log_var.squeeze(-1)
