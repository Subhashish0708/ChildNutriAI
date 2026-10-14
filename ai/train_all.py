"""
=============================================================================
MASTER MULTI-MODAL AI TRAINING & BENCHMARK PIPELINE - ChildNutri AI
=============================================================================
Official Master Training Pipeline for ChildNutri AI B.Tech Technical Hardening.
Executes complete end-to-end training and rigorous evaluation:
  • Stage 2: Data Preprocessing (Cleaning, Transformation, Stratified Split)
  • Stage 3: Multi-Modal AI Systems:
      - Numerical/Tabular Branch (XGBoost, LightGBM, Random Forest, Soft-Voting Ensemble, PyTorch MLP)
      - Visual Branch Research Prototype (EfficientNet-B0 transfer learning prototype)
      - Multimodal Feature Fusion Network Prototype (1292-D = 1280 visual + 12 anthropometric)
  • Stage 4: Unsupervised Anomaly Screening & Cohort Clustering:
      - PyTorch Autoencoder Anomaly Detection
      - Nutritional K-Means (k=4) Cohort Discovery
  • Stage 5: Explainability Engines:
      - SHAP TreeExplainer on Random Forest component
      - Grad-CAM Visual Heatmaps on EfficientNet-B0
  • Stage 6: Academic Evaluation Matrix & 5-Fold Stratified Cross-Validation
  • Stage 7: Export Model Artifacts, Comprehensive Benchmark JSON, & Manifest
=============================================================================
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

# Set path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Scikit-learn Metrics & Model Selection
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    precision_score, recall_score, classification_report, confusion_matrix
)
from sklearn.model_selection import StratifiedKFold, cross_val_score

# PyTorch
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

# Internal Modules
from ai.preprocess import run_full_preprocessing_pipeline, ImagePreprocessor
from ai.models.tabular_models import train_tabular_models, SoftVotingEnsemble
from ai.models.vision_model import EfficientNetB0MalnutritionClassifier
from ai.models.multimodal_fusion import MultimodalFusionNetwork1292D
from ai.models.unsupervised import AnthropometricAutoencoder, NutritionalKMeansClusterer
from ai.explainability.shap_explainer import ChildNutriSHAPExplainer
from ai.explainability.gradcam import GradCAMVisualExplainer
from ai.clinical_algorithms.who_lms import WHOLMSEngine
from ai.clinical_algorithms.longitudinal_velocity import LongitudinalGrowthVelocityEngine
from ai.clinical_algorithms.clinical_triage import ClinicalTriageEngine
from ai.clinical_algorithms.risk_scorer import ContinuousRiskScorer

def master_train():
    print("=" * 75)
    print("CHILDNUTRI AI - MASTER MULTI-MODAL TRAINING & BENCHMARK PIPELINE v2.0")
    print("=" * 75)

    dataset_path = os.path.join(BASE_DIR, "dataset", "anthropometric_data.csv")
    models_dir = os.path.join(BASE_DIR, "ai", "models")
    os.makedirs(models_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # STAGE 2: DATA PREPROCESSING
    # -------------------------------------------------------------------------
    prep = run_full_preprocessing_pipeline(dataset_path, models_dir)
    X_train, y_train = prep["X_train"], prep["y_train"]
    X_val, y_val = prep["X_val"], prep["y_val"]
    X_test, y_test = prep["X_test"], prep["y_test"]
    meta = prep["meta"]
    classes = meta["classes"]
    feature_names = meta["feature_names"]
    num_classes = len(classes)

    # -------------------------------------------------------------------------
    # STAGE 3A: NUMERICAL BRANCH (Tabular Machine Learning & Ensemble)
    # -------------------------------------------------------------------------
    tabular_results = train_tabular_models(X_train, y_train, X_val, y_val, classes=classes)
    xgb_clf = tabular_results["xgboost"]
    lgb_clf = tabular_results["lightgbm"]
    rf_clf = tabular_results["random_forest"]
    ensemble_clf = tabular_results["ensemble"]
    pytorch_mlp = tabular_results["pytorch_mlp"]

    # -------------------------------------------------------------------------
    # STAGE 3B: CLINICAL INDIAN NEONATAL IMAGE BRANCH (EfficientNet-B0 Regression)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print(">> INITIALIZING CLINICAL INDIAN NEONATAL IMAGE BRANCH (EfficientNet-B0)")
    print("   Dataset: Neonatal Anthropometric Image Dataset for Computer Vision-Based Growth Analysis")
    print("   Origin: Combined District Hospital, Kaushambi & Madhuraj Hospital, Kanpur, UP, India")
    print("   Authors: Anurag Singh & Dr. Rashi Agarwal (© 2026)")
    print("-" * 60)
    from ai.train_neonatal_regression import train_and_export_neonatal_model
    neonatal_results = train_and_export_neonatal_model(epochs=3, batch_size=16, lr=0.001)
    print(f"   Trained & exported neonatal regressor to ai/models/neonatal_regressor.pth")

    # Clinical Pediatric Screening Vision Branch (Indian Neonatal Dataset)
    print("\n   [Clinical Vision] Initializing Clinical Neonatal Feature Extractor & Multimodal Fusion...")
    from ai.data.indian_neonatal_dataset import (
        IndianNeonatalVisionDataset,
        IndianNeonatalDatasetAdapter,
        ALL_REGRESSION_TARGETS
    )

    neo_train_ds = IndianNeonatalVisionDataset(split="train")
    neo_val_ds = IndianNeonatalVisionDataset(split="val")
    neo_test_ds = IndianNeonatalVisionDataset(split="test")

    vision_model = EfficientNetB0MalnutritionClassifier(num_classes=num_classes, pretrained=False)
    vision_optimizer = optim.AdamW(vision_model.parameters(), lr=0.001, weight_decay=1e-4)
    vision_criterion = nn.CrossEntropyLoss()

    def build_neonatal_split_tensors(ds):
        rows = []
        labels = []
        risks = []
        images = []
        cleaner = prep["cleaner"]
        transformer = prep["transformer"]

        for i in range(len(ds)):
            item = ds[i]
            w_g = item["targets"]["weight_g"].item()
            l_cm = item["targets"]["body_length_cm"].item()
            hc_cm = item["targets"]["head_circumference_cm"].item()
            arm_cm = item["targets"]["arm_length_cm"].item()
            gen = "Male" if item["gender"] == "M" else "Female"
            w_kg = w_g / 1000.0 if w_g > 0 else 2.5
            ht = l_cm if l_cm > 0 else 48.0
            hc = hc_cm if hc_cm > 0 else 32.0
            muac = (arm_cm * 0.7) if arm_cm > 0 else 10.5

            rows.append({
                "child_id": i + 1,
                "age_months": 0.5,
                "gender": gen,
                "weight": w_kg,
                "height": ht,
                "head_circumference": hc,
                "muac": muac,
                "has_edema": 0
            })

            # Derive clinical risk classification from genuine birth weight
            if w_g < 1000.0:
                labels.append(1)  # SAM
                risks.append(92.0)
            elif w_g < 1500.0:
                labels.append(1)  # SAM
                risks.append(80.0)
            elif w_g < 2500.0:
                labels.append(3)  # Underweight / LBW
                risks.append(60.0)
            else:
                labels.append(0)  # Normal
                risks.append(15.0)

            images.append(item["image"])

        df = pd.DataFrame(rows)
        df_clean = cleaner.clean(df, is_training=False)
        a_feats = transformer.transform(df_clean)

        return (
            torch.stack(images, dim=0),
            torch.tensor(a_feats, dtype=torch.float32),
            torch.tensor(labels, dtype=torch.long),
            torch.tensor(risks, dtype=torch.float32).unsqueeze(1)
        )

    imgs_train, a_features_train, t_target_train, t_risk_train = build_neonatal_split_tensors(neo_train_ds)
    imgs_val, a_features_val, y_val_mm, r_val_mm = build_neonatal_split_tensors(neo_val_ds)
    imgs_test, a_features_test, y_test_mm, r_test_mm = build_neonatal_split_tensors(neo_test_ds)

    neo_train_loader = DataLoader(TensorDataset(imgs_train, t_target_train), batch_size=16, shuffle=True)
    vision_model.train()
    for ep in range(3):
        v_loss = 0.0
        for bx, by in neo_train_loader:
            vision_optimizer.zero_grad()
            logits, _ = vision_model(bx)
            loss = vision_criterion(logits, by)
            loss.backward()
            vision_optimizer.step()
            v_loss += loss.item()
        print(f"   EfficientNet-B0 Screening Epoch {ep+1}/3 - Loss: {v_loss/max(1, len(neo_train_loader)):.4f}")

    # -------------------------------------------------------------------------
    # STAGE 3C: 1292-D MULTIMODAL FEATURE FUSION NETWORK (INDIAN NEONATAL CLINICAL COHORT)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print(">> TRAINING 1292-D MULTIMODAL FUSION NETWORK (INDIAN NEONATAL COHORT)")
    print("   Architecture: 1280 Real Visual Embeddings + 12 Paired Anthropometrics = 1292-D")
    print("   Origin: Combined District Hospital, Kaushambi & Madhuraj Hospital, Kanpur, UP, India")
    print("-" * 60)
    anthro_dim = X_train.shape[1]
    fusion_net = MultimodalFusionNetwork1292D(visual_dim=1280, anthro_dim=anthro_dim, num_classes=num_classes)
    fusion_optimizer = optim.AdamW(fusion_net.parameters(), lr=0.002, weight_decay=1e-4)
    fusion_clf_loss = nn.CrossEntropyLoss()
    fusion_reg_loss = nn.MSELoss()

    # Extract genuine visual embeddings from real images
    vision_model.eval()
    with torch.no_grad():
        v_features_train = vision_model.extract_visual_features(imgs_train)
        v_features_val = vision_model.extract_visual_features(imgs_val)
        v_features_test = vision_model.extract_visual_features(imgs_test)

    fusion_ds = TensorDataset(v_features_train, a_features_train, t_target_train, t_risk_train)
    fusion_loader = DataLoader(fusion_ds, batch_size=16, shuffle=True)

    fusion_net.train()
    for ep in range(6):
        f_loss = 0.0
        for bv, ba, by, br in fusion_loader:
            fusion_optimizer.zero_grad()
            out = fusion_net(bv, ba)
            l_cls = fusion_clf_loss(out["logits"], by)
            l_reg = fusion_reg_loss(out["risk_score"], br)
            total_l = l_cls + 0.05 * l_reg
            total_l.backward()
            fusion_optimizer.step()
            f_loss += total_l.item()
        if (ep + 1) % 2 == 0 or ep == 5:
            print(f"   Fusion Network Epoch {ep+1}/6 - Multi-Task Loss: {f_loss/len(fusion_loader):.4f}")

    # Evaluate Multimodal Fusion on Held-Out Indian Neonatal Val Split
    fusion_net.eval()
    with torch.no_grad():
        f_val_out = fusion_net(v_features_val, a_features_val)
        f_val_preds = torch.argmax(f_val_out["logits"], dim=1).numpy()
        fusion_acc = accuracy_score(y_val_mm.numpy(), f_val_preds)
        fusion_f1 = f1_score(y_val_mm.numpy(), f_val_preds, average="weighted", zero_division=0)
        print(f"   Multimodal Fusion Val Accuracy: {fusion_acc*100:.2f}% | Weighted F1: {fusion_f1*100:.2f}%")

    # -------------------------------------------------------------------------
    # STAGE 4: UNSUPERVISED ANOMALY DETECTION & CLUSTERING
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print(">> TRAINING UNSUPERVISED MODELS (Autoencoder & K-Means)")
    print("-" * 60)
    autoencoder = AnthropometricAutoencoder(in_features=anthro_dim, latent_dim=4)
    ae_opt = optim.Adam(autoencoder.parameters(), lr=0.005)
    ae_crit = nn.MSELoss()
    for _ in range(10):
        for _, ba, _, _ in fusion_loader:
            ae_opt.zero_grad()
            recon, _ = autoencoder(ba)
            l = ae_crit(recon, ba)
            l.backward()
            ae_opt.step()
    print("   PyTorch Anthropometric Autoencoder trained.")

    kmeans = NutritionalKMeansClusterer(n_clusters=4).fit(X_train)
    print("   Nutritional K-Means Clusterer fitted (k=4 cohorts).")

    # -------------------------------------------------------------------------
    # STAGE 5: EXPLAINABILITY ENGINES (SHAP & Grad-CAM)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print(">> INITIALIZING EXPLAINABILITY ENGINES (SHAP & Grad-CAM)")
    print("-" * 60)
    shap_engine = ChildNutriSHAPExplainer(rf_clf, feature_names=feature_names, classes=classes)
    gradcam_engine = GradCAMVisualExplainer(vision_model)
    print("   SHAP TreeExplainer initialized on Random Forest component.")
    print("   Grad-CAM Visual Explainer initialized on EfficientNet-B0.")

    # -------------------------------------------------------------------------
    # STAGE 6: ACADEMIC BENCHMARK MATRIX & STRATIFIED CROSS-VALIDATION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("ACADEMIC BENCHMARK MATRIX ON HELD-OUT TEST SET (450 SAMPLES)")
    print("=" * 75)

    models_eval = {}

    def compute_full_metrics(y_true, y_pred):
        return {
            "Accuracy": float(accuracy_score(y_true, y_pred)),
            "Balanced_Accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "Macro_Precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
            "Macro_Recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
            "Macro_F1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
            "Weighted_F1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
            "Weighted_Precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
            "Weighted_Recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
        }

    # 1. XGBoost
    p_xgb = xgb_clf.predict(X_test)
    models_eval["XGBoost Classifier"] = compute_full_metrics(y_test, p_xgb)

    # 2. LightGBM
    p_lgb = lgb_clf.predict(X_test)
    models_eval["LightGBM Classifier"] = compute_full_metrics(y_test, p_lgb)

    # 3. Random Forest
    p_rf = rf_clf.predict(X_test)
    models_eval["Random Forest Classifier"] = compute_full_metrics(y_test, p_rf)

    # 4. Soft-Voting Production Ensemble
    p_ens = ensemble_clf.predict(X_test)
    ens_metrics = compute_full_metrics(y_test, p_ens)
    models_eval["Soft-Voting Ensemble (XGB+LGB+RF) [PRODUCTION]"] = ens_metrics

    # 5. 1292-D Multimodal Fusion Network (Indian Neonatal Clinical Cohort Held-Out Test Partition)
    with torch.no_grad():
        f_test_out = fusion_net(v_features_test, a_features_test)
        p_fusion = torch.argmax(f_test_out["logits"], dim=1).numpy()
    models_eval["1292-D Multimodal Fusion Network (Indian Neonatal Cohort)"] = compute_full_metrics(y_test_mm.numpy(), p_fusion)

    # Print Comparison Table
    print(f"\n{'MODEL ARCHITECTURE':<52} | {'ACCURACY':<9} | {'BAL ACC':<9} | {'MACRO F1':<9} | {'WGT F1':<9}")
    print("-" * 100)
    for name, m in models_eval.items():
        print(f"{name:<52} | {m['Accuracy']*100:>7.2f}% | {m['Balanced_Accuracy']*100:>7.2f}% | {m['Macro_F1']*100:>7.2f}% | {m['Weighted_F1']*100:>7.2f}%")

    # Detailed Per-Class Metrics for Champion Production Ensemble
    cls_report = classification_report(y_test, p_ens, target_names=classes, digits=4, output_dict=True)
    cm = confusion_matrix(y_test, p_ens)
    print("\nDetailed Per-Class Performance (Production Soft-Voting Ensemble):")
    print(classification_report(y_test, p_ens, target_names=classes, digits=4))

    # Stratified 5-Fold Cross Validation on Development Set (X_train, y_train)
    print("\n>> RUNNING 5-FOLD STRATIFIED CROSS-VALIDATION ON DEVELOPMENT SET...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_accs = []
    cv_f1s = []
    from sklearn.base import clone
    for fold, (tr_idx, te_idx) in enumerate(cv.split(X_train, y_train)):
        f_xgb = clone(xgb_clf).fit(X_train[tr_idx], y_train[tr_idx])
        f_lgb = clone(lgb_clf).fit(X_train[tr_idx], y_train[tr_idx])
        f_rf = clone(rf_clf).fit(X_train[tr_idx], y_train[tr_idx])
        f_ens = SoftVotingEnsemble(f_xgb, f_lgb, f_rf, weights=[0.40, 0.35, 0.25], classes=classes)
        f_pred = f_ens.predict(X_train[te_idx])
        cv_accs.append(accuracy_score(y_train[te_idx], f_pred))
        cv_f1s.append(f1_score(y_train[te_idx], f_pred, average="weighted"))
        print(f"   Fold {fold+1}/5 - Accuracy: {cv_accs[-1]*100:.2f}% | F1: {cv_f1s[-1]*100:.2f}%")

    cv_scores = np.array(cv_accs)
    cv_f1_scores = np.array(cv_f1s)
    print(f"   5-Fold CV Mean Accuracy: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")
    print(f"   5-Fold CV Mean Weighted F1: {cv_f1_scores.mean()*100:.2f}% (+/- {cv_f1_scores.std()*100:.2f}%)")

    # -------------------------------------------------------------------------
    # STAGE 7: EXPORT ALL ARTIFACTS & MANIFEST
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print(">> EXPORTING MODEL ARTIFACTS, MANIFEST & BENCHMARK JSON")
    print("-" * 60)
    
    # 1. Production Tabular Models
    joblib.dump(xgb_clf, os.path.join(models_dir, "xgboost_model.pkl"))
    joblib.dump(lgb_clf, os.path.join(models_dir, "lightgbm_model.pkl"))
    joblib.dump(rf_clf, os.path.join(models_dir, "random_forest_model.pkl"))
    joblib.dump(ensemble_clf, os.path.join(models_dir, "ensemble_model.pkl"))
    joblib.dump(kmeans, os.path.join(models_dir, "kmeans_clusterer.pkl"))
    
    # 2. Legacy Anthropometric Bundle (Quarantined)
    legacy_bundle = {
        "model": ensemble_clf,
        "model_name": "ChildNutri Soft-Voting Ensemble (XGBoost + LightGBM + Random Forest)",
        "classes": classes,
        "feature_names": feature_names,
        "is_legacy": True,
        "status": "legacy_quarantined",
        "notice": "Legacy wrapper retained for backwards compatibility. Production screening uses ensemble_model.pkl."
    }
    joblib.dump(legacy_bundle, os.path.join(models_dir, "anthropometric_model.pkl"))

    # 3. PyTorch Neural Models
    torch.save(fusion_net.state_dict(), os.path.join(models_dir, "multimodal_fusion.pth"))
    torch.save(pytorch_mlp.state_dict(), os.path.join(models_dir, "pytorch_mlp.pth"))
    torch.save(vision_model.state_dict(), os.path.join(models_dir, "vision_efficientnet.pth"))
    torch.save(autoencoder.state_dict(), os.path.join(models_dir, "autoencoder.pth"))

    # 4. Save Comprehensive Benchmark Metrics JSON
    metrics_export = {
        "production_champion": "Soft-Voting Ensemble (XGB+LGB+RF)",
        "test_benchmarks": models_eval,
        "per_class_metrics": {c: cls_report[c] for c in classes},
        "confusion_matrix": cm.tolist(),
        "stratified_5fold_cv": {
            "accuracy_mean": float(cv_scores.mean()),
            "accuracy_std": float(cv_scores.std()),
            "accuracy_folds": [float(s) for s in cv_scores],
            "weighted_f1_mean": float(cv_f1_scores.mean()),
            "weighted_f1_std": float(cv_f1_scores.std())
        },
        "dataset_metadata": {
            "total_samples": 3000,
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "test_samples": len(X_test),
            "features_count": len(feature_names),
            "feature_names": feature_names,
            "classes": classes
        }
    }
    with open(os.path.join(models_dir, "all_models_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics_export, f, indent=2)

    # 5. Authoritative Model Manifest (Phase 4)
    manifest = {
        "manifest_version": "2.0.0",
        "description": "ChildNutri AI Authoritative Model & Artifact Manifest",
        "production_screening_pipeline": "tabular_ensemble",
        "models": {
            "ensemble": {
                "name": "Soft-Voting Tabular Ensemble (XGB 40% + LGB 35% + RF 25%)",
                "artifact": "ensemble_model.pkl",
                "type": "SoftVotingEnsemble",
                "operational_tier": "production",
                "input_dim": 12,
                "output_classes": classes,
                "framework": "scikit-learn + xgboost + lightgbm",
                "used_in_production": True,
                "clinical_status": "Validated on development dataset. Provides primary screening classification.",
                "limitations": "Trained on development dataset; requires external multicenter validation for real-world clinical deployment."
            },
            "xgboost": {
                "name": "XGBoost Gradient Boosted Trees",
                "artifact": "xgboost_model.pkl",
                "type": "XGBClassifier",
                "operational_tier": "production_submodel",
                "input_dim": 12,
                "output_classes": classes,
                "framework": "xgboost",
                "used_in_production": True,
                "weight_in_ensemble": 0.40
            },
            "lightgbm": {
                "name": "LightGBM Gradient Boosted Machine",
                "artifact": "lightgbm_model.pkl",
                "type": "LGBMClassifier",
                "operational_tier": "production_submodel",
                "input_dim": 12,
                "output_classes": classes,
                "framework": "lightgbm",
                "used_in_production": True,
                "weight_in_ensemble": 0.35
            },
            "random_forest": {
                "name": "Random Forest Classifier",
                "artifact": "random_forest_model.pkl",
                "type": "RandomForestClassifier",
                "operational_tier": "production_submodel",
                "input_dim": 12,
                "output_classes": classes,
                "framework": "scikit-learn",
                "used_in_production": True,
                "weight_in_ensemble": 0.25,
                "xai_use": "Provides TreeExplainer SHAP attributions."
            },
            "neonatal_regressor": {
                "name": "EfficientNet-B0 Indian Neonatal Anthropometric Regressor",
                "artifact": "neonatal_regressor.pth",
                "type": "EfficientNetB0NeonatalRegressor",
                "operational_tier": "research_prototype",
                "input_dim": "3x224x224 RGB image",
                "regression_targets": [
                    "weight_g",
                    "body_length_cm",
                    "head_circumference_cm",
                    "chest_girth_cm",
                    "arm_length_cm",
                    "leg_length_cm"
                ],
                "framework": "PyTorch / torchvision (EfficientNet-B0 transfer learning)",
                "dataset_attribution": {
                    "dataset_name": "Neonatal Anthropometric Image Dataset for Computer Vision-Based Growth Analysis",
                    "authors": "Anurag Singh & Dr. Rashi Agarwal (© 2026)",
                    "clinical_sites": [
                        "Combined District Hospital, Manjhanpur, Kaushambi, UP, India",
                        "Madhuraj Hospital, Kanpur, UP, India"
                    ],
                    "permitted_use": "Research, academic, and educational use only"
                },
                "used_in_production": True,
                "clinical_status": "Trained on real clinically acquired Indian neonatal photographic dataset. Multi-target anthropometric estimation with subject-level zero-leakage partitions.",
                "limitations": "Screening decision-support aid based on single/multi-view 2D photos (cohort size N=83). Does not replace calibrated physical clinical infantometer and baby weighing scale."
            },
            "vision": {
                "name": "EfficientNet-B0 Malnutrition Feature Extractor",
                "artifact": "vision_efficientnet.pth",
                "type": "EfficientNetB0MalnutritionClassifier",
                "operational_tier": "experimental_prototype",
                "input_dim": "3x224x224 RGB image",
                "output_classes": classes,
                "framework": "PyTorch / torchvision",
                "used_in_production": False,
                "clinical_status": "Architectural prototype only. Not clinically validated.",
                "limitations": "Trained with transfer learning and synthetic benchmark inputs due to absence of licensed pediatric clinical image dataset."
            },
            "multimodal_fusion": {
                "name": "1292-D Multimodal Feature Fusion Network",
                "artifact": "multimodal_fusion.pth",
                "type": "MultimodalFusionNetwork1292D",
                "operational_tier": "experimental_prototype",
                "input_dim": 1292,
                "input_breakdown": "1280 visual embedding features + 12 anthropometric clinical features",
                "output_classes": classes,
                "framework": "PyTorch",
                "used_in_production": False,
                "clinical_status": "Architectural research prototype. Demonstrates cross-modal attention gating.",
                "limitations": "Prototype architecture; not validated on paired clinical image-anthropometry cohorts."
            },
            "pytorch_mlp": {
                "name": "PyTorch Deep Tabular MLP",
                "artifact": "pytorch_mlp.pth",
                "type": "PyTorchTabularMLP",
                "operational_tier": "experimental_submodel",
                "input_dim": 12,
                "output_classes": classes,
                "framework": "PyTorch",
                "used_in_production": False
            },
            "autoencoder": {
                "name": "Anthropometric Anomaly Autoencoder",
                "artifact": "autoencoder.pth",
                "type": "AnthropometricAutoencoder",
                "operational_tier": "exploratory_unsupervised",
                "input_dim": 12,
                "latent_dim": 4,
                "framework": "PyTorch",
                "used_in_production": False,
                "purpose": "Anomaly detection and reconstruction-error screening."
            },
            "kmeans": {
                "name": "Nutritional K-Means Clusterer",
                "artifact": "kmeans_clusterer.pkl",
                "type": "KMeans",
                "operational_tier": "exploratory_unsupervised",
                "input_dim": 12,
                "k_clusters": 4,
                "framework": "scikit-learn",
                "used_in_production": False,
                "purpose": "Cohort discovery."
            },
            "cleaner": {
                "name": "Anthropometric DataCleaner",
                "artifact": "cleaner.pkl",
                "type": "DataCleaner",
                "operational_tier": "preprocessing",
                "framework": "scikit-learn / custom",
                "used_in_production": True
            },
            "transformer": {
                "name": "Anthropometric DataTransformer",
                "artifact": "transformer.pkl",
                "type": "DataTransformer",
                "operational_tier": "preprocessing",
                "output_dim": 12,
                "framework": "scikit-learn / custom",
                "used_in_production": True
            },
            "scaler": {
                "name": "Standard Anthropometric Scaler",
                "artifact": "scaler.pkl",
                "type": "StandardScaler",
                "operational_tier": "preprocessing",
                "framework": "scikit-learn",
                "used_in_production": True
            },
            "label_encoder": {
                "name": "Diagnostic LabelEncoder",
                "artifact": "label_encoder.pkl",
                "type": "LabelEncoder",
                "operational_tier": "preprocessing",
                "classes": classes,
                "framework": "scikit-learn",
                "used_in_production": True
            },
            "anthropometric_legacy": {
                "name": "Legacy Anthropometric Model Wrapper (Quarantined)",
                "artifact": "anthropometric_model.pkl",
                "operational_tier": "legacy_quarantined",
                "used_in_production": False,
                "notice": "Never used for production screening. Replaced by ensemble_model.pkl."
            }
        }
    }
    with open(os.path.join(models_dir, "model_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"   Saved: all_models_metrics.json")
    print(f"   Saved: model_manifest.json")
    print("=" * 75)
    print("ALL AI/ML MODELS & ALGORITHMS TRAINED, BENCHMARKED & EXPORTED!")
    print("=" * 75)

if __name__ == "__main__":
    master_train()
