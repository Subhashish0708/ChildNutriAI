"""
=============================================================================
Tabular AI / ML Models Suite - ChildNutri AI
=============================================================================
Includes:
  1. XGBoost Classifier (Extreme Gradient Boosting)
  2. LightGBM Classifier (Light Gradient Boosting Machine)
  3. Random Forest Classifier (Ensemble Bagging)
  4. Soft-Voting Ensemble (Weighted Blending of XGBoost + LightGBM + Random Forest)
  5. PyTorch Tabular Clinical MLP (Deep Neural Network with Residual Skip Connections)
=============================================================================
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

# Sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# XGBoost & LightGBM
try:
    import xgboost as xgb
except (ImportError, OSError):
    xgb = None

try:
    import lightgbm as lgb
except (ImportError, OSError):
    lgb = None

# PyTorch
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader


# =============================================================================
# 1. PYTORCH TABULAR CLINICAL MLP
# =============================================================================
class TabularClinicalMLP(nn.Module):
    """
    Deep Neural Network for Anthropometric Clinical Features with
    LayerNorm, GELU, Dropout, and Residual Skip Connections.
    """
    def __init__(self, in_features: int = 12, num_classes: int = 5):
        super(TabularClinicalMLP, self).__init__()
        self.input_layer = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.2)
        )
        self.block1 = nn.Sequential(
            nn.Linear(128, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.2)
        )
        self.block2 = nn.Sequential(
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.GELU(),
            nn.Dropout(0.15)
        )
        self.head = nn.Linear(64, num_classes)

    def forward(self, x):
        h1 = self.input_layer(x)
        h1_res = h1 + self.block1(h1)  # Residual skip connection
        h2 = self.block2(h1_res)
        return self.head(h2)


# =============================================================================
# 2. SOFT-VOTING ENSEMBLE CLASSIFIER
# =============================================================================
class SoftVotingEnsemble:
    """
    Blends predicted probability distributions from XGBoost, LightGBM, and Random Forest.
    Weights default: XGBoost (0.40), LightGBM (0.35), Random Forest (0.25).
    """
    def __init__(self, xgb_model, lgb_model, rf_model, weights: List[float] = [0.40, 0.35, 0.25], classes: List[str] = None):
        self.xgb_model = xgb_model
        self.lgb_model = lgb_model
        self.rf_model = rf_model
        self.weights = np.array(weights) / sum(weights)
        self.classes_ = np.array(classes) if classes is not None else np.arange(5)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        p_xgb = self.xgb_model.predict_proba(X)
        p_lgb = self.lgb_model.predict_proba(X)
        p_rf = self.rf_model.predict_proba(X)

        blended = (
            self.weights[0] * p_xgb +
            self.weights[1] * p_lgb +
            self.weights[2] * p_rf
        )
        return blended

    def fit(self, X: np.ndarray, y: np.ndarray):
        if self.xgb_model is not None:
            self.xgb_model.fit(X, y)
        if self.lgb_model is not None:
            self.lgb_model.fit(X, y)
        if self.rf_model is not None:
            self.rf_model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)


# =============================================================================
# 3. TABULAR MODEL TRAINER & FACTORY
# =============================================================================
def train_tabular_models(X_train, y_train, X_val, y_val, classes: List[str]) -> Dict[str, Any]:
    """
    Trains XGBoost, LightGBM, Random Forest, Soft-Voting Ensemble, and PyTorch MLP.
    Returns dictionary of trained models and validation metrics.
    """
    print("\n" + "-" * 55)
    print(">> TRAINING ADVANCED TABULAR ML MODELS & ENSEMBLE")
    print("-" * 55)

    num_classes = len(classes)

    # 1. XGBoost Classifier
    print("1. Training XGBoost Classifier...")
    xgb_clf = xgb.XGBClassifier(
        n_estimators=160,
        max_depth=6,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=num_classes,
        random_state=42,
        eval_metric="mlogloss",
        verbosity=0
    )
    xgb_clf.fit(X_train, y_train)
    xgb_pred = xgb_clf.predict(X_val)
    xgb_acc = accuracy_score(y_val, xgb_pred)
    xgb_f1 = f1_score(y_val, xgb_pred, average="weighted")
    print(f"   XGBoost Val Accuracy: {xgb_acc*100:.2f}% | F1: {xgb_f1*100:.2f}%")

    # 2. LightGBM Classifier
    print("\n2. Training LightGBM Classifier...")
    lgb_clf = lgb.LGBMClassifier(
        n_estimators=150,
        max_depth=6,
        num_leaves=31,
        learning_rate=0.06,
        subsample=0.85,
        random_state=42,
        verbosity=-1
    )
    lgb_clf.fit(X_train, y_train)
    lgb_pred = lgb_clf.predict(X_val)
    lgb_acc = accuracy_score(y_val, lgb_pred)
    lgb_f1 = f1_score(y_val, lgb_pred, average="weighted")
    print(f"   LightGBM Val Accuracy: {lgb_acc*100:.2f}% | F1: {lgb_f1*100:.2f}%")

    # 3. Random Forest Classifier
    print("\n3. Training Random Forest Classifier...")
    rf_clf = RandomForestClassifier(
        n_estimators=180,
        max_depth=12,
        min_samples_split=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf_clf.fit(X_train, y_train)
    rf_pred = rf_clf.predict(X_val)
    rf_acc = accuracy_score(y_val, rf_pred)
    rf_f1 = f1_score(y_val, rf_pred, average="weighted")
    print(f"   Random Forest Val Accuracy: {rf_acc*100:.2f}% | F1: {rf_f1*100:.2f}%")

    # 4. Soft-Voting Ensemble
    print("\n4. Building Soft-Voting Ensemble (XGBoost + LightGBM + Random Forest)...")
    ensemble = SoftVotingEnsemble(xgb_clf, lgb_clf, rf_clf, weights=[0.40, 0.35, 0.25], classes=classes)
    ens_pred = ensemble.predict(X_val)
    ens_acc = accuracy_score(y_val, ens_pred)
    ens_f1 = f1_score(y_val, ens_pred, average="weighted")
    print(f"   Ensemble Val Accuracy: {ens_acc*100:.2f}% | F1: {ens_f1*100:.2f}%")

    # 5. PyTorch Tabular Clinical MLP
    print("\n5. Training PyTorch Tabular Clinical MLP...")
    in_dim = X_train.shape[1]
    mlp = TabularClinicalMLP(in_features=in_dim, num_classes=num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(mlp.parameters(), lr=0.003, weight_decay=1e-4)

    t_xtrain = torch.tensor(X_train, dtype=torch.float32)
    t_ytrain = torch.tensor(y_train, dtype=torch.long)
    t_xval = torch.tensor(X_val, dtype=torch.float32)
    t_yval = torch.tensor(y_val, dtype=torch.long)

    dataset = TensorDataset(t_xtrain, t_ytrain)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)

    mlp.train()
    for epoch in range(12):
        for bx, by in loader:
            optimizer.zero_grad()
            out = mlp(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()

    mlp.eval()
    with torch.no_grad():
        mlp_logits = mlp(t_xval)
        mlp_preds = torch.argmax(mlp_logits, dim=1).numpy()
        mlp_acc = accuracy_score(y_val, mlp_preds)
        mlp_f1 = f1_score(y_val, mlp_preds, average="weighted")
    print(f"   PyTorch MLP Val Accuracy: {mlp_acc*100:.2f}% | F1: {mlp_f1*100:.2f}%")

    return {
        "xgboost": xgb_clf,
        "lightgbm": lgb_clf,
        "random_forest": rf_clf,
        "ensemble": ensemble,
        "pytorch_mlp": mlp,
        "metrics": {
            "xgboost": {"accuracy": float(xgb_acc), "f1": float(xgb_f1)},
            "lightgbm": {"accuracy": float(lgb_acc), "f1": float(lgb_f1)},
            "random_forest": {"accuracy": float(rf_acc), "f1": float(rf_f1)},
            "ensemble": {"accuracy": float(ens_acc), "f1": float(ens_f1)},
            "pytorch_mlp": {"accuracy": float(mlp_acc), "f1": float(mlp_f1)}
        }
    }
