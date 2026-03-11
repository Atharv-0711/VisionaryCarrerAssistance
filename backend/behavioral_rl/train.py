import os
import random
from dataclasses import asdict, dataclass

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset, random_split

from .model import BehavioralScoreNet


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


@dataclass
class TrainingConfig:
    seed: int = 42
    hidden_dim: int = 128
    dropout: float = 0.15
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    epochs: int = 200
    batch_size: int = 32
    early_stopping_patience: int | None = 20
    val_ratio: float = 0.2
    variance_lambda: float = 0.02
    variance_head_weight: float = 0.05
    min_train_samples: int = 8


def prepare_training_data(
    embeddings: np.ndarray,
    academic_scores: np.ndarray,
) -> tuple[torch.Tensor, torch.Tensor]:
    x = torch.from_numpy(embeddings.astype(np.float32, copy=False))
    y = torch.from_numpy(academic_scores.astype(np.float32, copy=False))
    return x, y


def _build_loaders(
    x: torch.Tensor,
    y: torch.Tensor,
    batch_size: int,
    val_ratio: float,
    seed: int,
) -> tuple[DataLoader, DataLoader]:
    dataset = TensorDataset(x, y)
    n_total = len(dataset)
    if n_total < 5:
        loader = DataLoader(dataset, batch_size=min(batch_size, n_total), shuffle=True)
        return loader, loader

    n_val = max(1, int(round(n_total * val_ratio)))
    n_train = n_total - n_val
    if n_train < 2:
        n_train = n_total - 1
        n_val = 1

    generator = torch.Generator().manual_seed(seed)
    train_ds, val_ds = random_split(dataset, [n_train, n_val], generator=generator)
    train_loader = DataLoader(train_ds, batch_size=min(batch_size, n_train), shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=min(batch_size, n_val), shuffle=False)
    return train_loader, val_loader


def _mean_loss_for_loader(
    model: BehavioralScoreNet,
    loader: DataLoader,
    variance_lambda: float,
    variance_head_weight: float,
    device: torch.device,
) -> float:
    model.eval()
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            pred, log_var = model(xb)
            mse = F.mse_loss(pred, yb)
            score_var = torch.var(pred, unbiased=False)
            nll = 0.5 * (torch.exp(-log_var) * torch.square(pred - yb) + log_var).mean()
            loss = mse - variance_lambda * score_var + variance_head_weight * nll
            losses.append(float(loss.item()))
    return float(np.mean(losses)) if losses else 0.0


def train_behavioral_model(
    embeddings: np.ndarray,
    academic_scores: np.ndarray,
    config: TrainingConfig,
    device: str | None = None,
    initial_state_dict: dict | None = None,
    initial_history: dict[str, list[float]] | None = None,
) -> dict:
    set_global_seed(config.seed)
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_device = torch.device(device)

    x, y = prepare_training_data(embeddings, academic_scores)
    if len(x) < config.min_train_samples:
        raise ValueError(
            f"Need at least {config.min_train_samples} matched samples to train; got {len(x)}."
        )

    train_loader, val_loader = _build_loaders(
        x,
        y,
        batch_size=config.batch_size,
        val_ratio=config.val_ratio,
        seed=config.seed,
    )
    model = BehavioralScoreNet(
        input_dim=x.shape[1],
        hidden_dim=config.hidden_dim,
        dropout=config.dropout,
    ).to(torch_device)
    if initial_state_dict:
        try:
            model.load_state_dict(initial_state_dict, strict=False)
        except Exception:
            # If checkpoint shape/version does not align, train from scratch.
            pass
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    best_state = None
    best_val_loss = float("inf")
    patience_count = 0
    history = {"train_loss": [], "val_loss": []}
    if initial_history:
        history["train_loss"] = list(initial_history.get("train_loss", []))
        history["val_loss"] = list(initial_history.get("val_loss", []))

    for _ in range(config.epochs):
        model.train()
        train_losses = []
        for xb, yb in train_loader:
            xb = xb.to(torch_device)
            yb = yb.to(torch_device)
            optimizer.zero_grad(set_to_none=True)
            pred, log_var = model(xb)
            mse = F.mse_loss(pred, yb)
            score_var = torch.var(pred, unbiased=False)
            nll = 0.5 * (torch.exp(-log_var) * torch.square(pred - yb) + log_var).mean()
            loss = mse - config.variance_lambda * score_var + config.variance_head_weight * nll
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.item()))

        train_loss = float(np.mean(train_losses)) if train_losses else 0.0
        val_loss = _mean_loss_for_loader(
            model,
            val_loader,
            variance_lambda=config.variance_lambda,
            variance_head_weight=config.variance_head_weight,
            device=torch_device,
        )
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_count = 0
        else:
            patience_count += 1
            if (
                config.early_stopping_patience is not None
                and config.early_stopping_patience > 0
                and patience_count >= config.early_stopping_patience
            ):
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    with torch.no_grad():
        pred_all, log_var_all = model(x.to(torch_device))
        pred_all_np = pred_all.detach().cpu().numpy()
        log_var_all_np = log_var_all.detach().cpu().numpy()

    residual_std = float(np.std(pred_all_np - y.numpy()))
    return {
        "model": model,
        "train_history": history,
        "best_val_loss": best_val_loss,
        "residual_std": residual_std,
        "fitted_pred": pred_all_np,
        "fitted_log_var": log_var_all_np,
        "config": asdict(config),
        "input_dim": int(x.shape[1]),
        "device": str(torch_device),
    }


def save_checkpoint(
    path: str,
    model: BehavioralScoreNet,
    config_dict: dict,
    model_name: str,
    input_dim: int,
    residual_std: float,
    train_history: dict[str, list[float]],
) -> None:
    payload = {
        "state_dict": model.state_dict(),
        "config": config_dict,
        "embedding_model_name": model_name,
        "input_dim": input_dim,
        "residual_std": residual_std,
        "train_history": train_history,
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    torch.save(payload, path)


def load_checkpoint(path: str, map_location: str | torch.device = "cpu") -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        ckpt = torch.load(path, map_location=map_location)
    except Exception:
        return None
    required_keys = {"state_dict", "config", "embedding_model_name", "input_dim"}
    if not required_keys.issubset(set(ckpt.keys())):
        return None
    return ckpt
