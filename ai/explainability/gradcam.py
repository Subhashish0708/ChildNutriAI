"""
=============================================================================
Grad-CAM (Gradient-Weighted Class Activation Mapping) - ChildNutri AI
=============================================================================
Provides visual explainability for infant malnutrition photo screening:
  • Computes gradients of the target class score wrt convolutional feature maps.
  • Generates a 2D activation heatmap showing which anatomical regions
    drove the prediction.

Correct behavior enforced:
  1. NO IMAGE:
     available = False, status = "no_image"
  2. VALID IMAGE + VALID VISION MODEL:
     available = True, status = "available", generate actual Grad-CAM
  3. IMAGE EXISTS BUT MODEL FAILS:
     available = False, status = "error"

No simulated silhouettes or fake heatmaps are used.
=============================================================================
"""

import os
import io
import base64
import logging
import hashlib
from datetime import datetime, timezone
import numpy as np
from typing import Dict, Any, Optional, List
from PIL import Image

logger = logging.getLogger("childnutri.gradcam")

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class GradCAMVisualExplainer:
    """
    Computes genuine Grad-CAM heatmaps for PyTorch CNN / EfficientNet models.
    """
    def __init__(self, model=None, target_layer=None):
        if model is None:
            try:
                from backend.services.model_loader import get_model_loader
                model = get_model_loader().get_vision_model()
            except Exception as e:
                logger.warning(f"Could not load vision model in GradCAMVisualExplainer: {e}")
                model = None
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._hook_handles = []

        if self.model is not None and self.target_layer is None:
            if hasattr(self.model, "backbone") and hasattr(self.model.backbone, "features"):
                self.target_layer = self.model.backbone.features[-1]
            elif hasattr(self.model, "features"):
                self.target_layer = self.model.features[-1]

        if TORCH_AVAILABLE and self.target_layer is not None:
            self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, inp, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        h1 = self.target_layer.register_forward_hook(forward_hook)
        h2 = self.target_layer.register_full_backward_hook(backward_hook)
        self._hook_handles.extend([h1, h2])

    def generate_heatmap(self, input_tensor: torch.Tensor, class_idx: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Computes exact Grad-CAM from model activations and gradients.
        Returns None if model or tensor is unavailable.
        """
        if not TORCH_AVAILABLE or self.model is None or self.target_layer is None or input_tensor is None:
            return None

        try:
            self.model.eval()
            self.model.zero_grad()

            logits = self.model(input_tensor)
            if isinstance(logits, dict):
                target_key = "body_length_cm" if "body_length_cm" in logits else list(logits.keys())[0]
                if class_idx is not None and isinstance(class_idx, str) and class_idx in logits:
                    target_key = class_idx
                target_val = logits[target_key]
                target_score = target_val[0] if target_val.dim() > 0 else target_val
            else:
                if isinstance(logits, (tuple, list)):
                    logits = logits[0]
                if isinstance(logits, dict):
                    target_key = "body_length_cm" if "body_length_cm" in logits else list(logits.keys())[0]
                    target_val = logits[target_key]
                    target_score = target_val[0] if target_val.dim() > 0 else target_val
                else:
                    if class_idx is None or not isinstance(class_idx, int):
                        class_idx = torch.argmax(logits, dim=1).item()
                    target_score = logits[0, class_idx]

            target_score.backward()

            if self.gradients is None or self.activations is None:
                return None

            weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
            cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
            cam = F.relu(cam)

            cam = F.interpolate(cam, size=(224, 224), mode="bilinear", align_corners=False)
            cam = cam.squeeze().cpu().numpy()

            cam_min, cam_max = np.min(cam), np.max(cam)
            if cam_max > cam_min:
                cam_norm = (cam - cam_min) / (cam_max - cam_min)
            else:
                cam_norm = np.zeros_like(cam)

            return cam_norm
        except Exception as e:
            logger.error(f"Grad-CAM calculation error: {e}")
            return None

    def get_clinical_focus_regions(self, heatmap: np.ndarray, is_neonatal: bool = False) -> List[str]:
        """
        Translates real heatmap activation hotspots into clinical anatomical regions.
        Supports both pediatric malnutrition and neonatal anthropometric focus zones.
        """
        if heatmap is None:
            return []
        regions = []

        if is_neonatal:
            if np.mean(heatmap[:80, 60:164]) > 0.35:
                regions.append("Cranial & Head Contour Attention Zone")
            if np.mean(heatmap[70:150, 60:164]) > 0.35:
                regions.append("Thoracic & Abdominal Trunk Contour Zone")
            if np.mean(heatmap[70:160, :70]) > 0.30 or np.mean(heatmap[70:160, 154:]) > 0.30:
                regions.append("Upper Extremity / Arm Boundary Zone")
            if np.mean(heatmap[145:, :]) > 0.35:
                regions.append("Lower Extremity / Leg Boundary Zone")
            if not regions:
                regions.append("Crown-to-Heel Longitudinal Axis / Total Body Length Contour")
            return regions

        if np.mean(heatmap[:75, 70:154]) > 0.40:
            regions.append("Cranial / Upper Body Contour Attention Zone")
        if np.mean(heatmap[75:160, :80]) > 0.35 or np.mean(heatmap[75:160, 144:]) > 0.35:
            regions.append("Mid-Torso / Upper Extremity Attention Zone")
        if np.mean(heatmap[140:210, 70:154]) > 0.35:
            regions.append("Lower Torso / Abdominal Contour Zone")

        if not regions:
            regions.append("Overall Body Silhouette & Contour Attention Zone")

        return regions

    def generate_gradcam_overlay(
        self,
        image_path_or_pil=None,
        input_tensor=None,
        class_idx=None,
        alpha: float = 0.55,
        assessment_id: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generates genuine Grad-CAM overlay or explicit unavailable states.
        Enforces 3 strict states:
          1. NOT_AVAILABLE: No image provided or image not found on disk.
          2. AVAILABLE: Real image + real model -> genuine overlay.
          3. ERROR: Image provided but processing/model fails.
        """
        target_layer_str = (
            self.target_layer.__class__.__name__
            if self.target_layer is not None
            else "backbone.features[-1]"
        )

        # STATE 1: NO IMAGE PROVIDED
        if image_path_or_pil is None:
            metadata = {
                "assessment_id": assessment_id,
                "image_hash": None,
                "model": "EfficientNet-B0 (PyTorch)",
                "model_version": "2.0.0",
                "target_layer": target_layer_str,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            return {
                "available": False,
                "status": "NOT_AVAILABLE",
                "legacy_status": "no_image",
                "reason": "No image was provided.",
                "original_image_base64": None,
                "pure_heatmap_base64": None,
                "gradcam_heatmap_base64": None,
                "gradcam_overlay_base64": None,
                "focus_regions": [],
                "metadata": metadata,
                "disclaimer": "AI explanations describe model behavior and feature attribution, not medical causation.",
                "message": "No photographic record uploaded for this assessment."
            }

        # Check file existence if string path
        if isinstance(image_path_or_pil, str) and not os.path.exists(image_path_or_pil):
            metadata = {
                "assessment_id": assessment_id,
                "image_hash": None,
                "model": "EfficientNet-B0 (PyTorch)",
                "model_version": "2.0.0",
                "target_layer": target_layer_str,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            return {
                "available": False,
                "status": "NOT_AVAILABLE",
                "legacy_status": "no_image",
                "reason": "Photographic record path not found on server.",
                "original_image_base64": None,
                "pure_heatmap_base64": None,
                "gradcam_heatmap_base64": None,
                "gradcam_overlay_base64": None,
                "focus_regions": [],
                "metadata": metadata,
                "disclaimer": "Photographic record path not found on server.",
                "message": "No photographic record uploaded for this assessment."
            }

        # Attempt to open real image and compute SHA-256 hash
        try:
            if isinstance(image_path_or_pil, str):
                base_img = Image.open(image_path_or_pil).convert("RGB")
            elif isinstance(image_path_or_pil, Image.Image):
                base_img = image_path_or_pil.convert("RGB")
            else:
                raise ValueError("Invalid image input format")

            base_resized = base_img.resize((224, 224), Image.Resampling.BILINEAR)
            buf_orig = io.BytesIO()
            base_resized.save(buf_orig, format="JPEG", quality=90)
            orig_bytes = buf_orig.getvalue()
            orig_b64 = "data:image/jpeg;base64," + base64.b64encode(orig_bytes).decode("utf-8")
            image_hash = hashlib.sha256(orig_bytes).hexdigest()
        except Exception as e:
            logger.error(f"Image load failure: {e}")
            metadata = {
                "assessment_id": assessment_id,
                "image_hash": None,
                "model": "EfficientNet-B0 (PyTorch)",
                "model_version": "2.0.0",
                "target_layer": target_layer_str,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            return {
                "available": False,
                "status": "ERROR",
                "legacy_status": "error",
                "reason": f"Image processing error: {e}",
                "original_image_base64": None,
                "pure_heatmap_base64": None,
                "gradcam_heatmap_base64": None,
                "gradcam_overlay_base64": None,
                "focus_regions": [],
                "metadata": metadata,
                "disclaimer": "Vision analysis could not be completed.",
                "message": f"Image processing error: {e}"
            }

        metadata = {
            "assessment_id": assessment_id,
            "image_hash": image_hash,
            "model": "EfficientNet-B0 (PyTorch)",
            "model_version": "2.0.0",
            "target_layer": target_layer_str,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Construct input_tensor from base_resized if not provided
        if input_tensor is None and TORCH_AVAILABLE:
            try:
                arr = np.array(base_resized).astype(np.float32) / 255.0
                mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
                std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
                norm_arr = (arr - mean) / std
                input_tensor = torch.tensor(norm_arr).permute(2, 0, 1).unsqueeze(0).float()
            except Exception as e:
                logger.error(f"Tensor conversion failed in generate_gradcam_overlay: {e}")

        # STATE 2 / 3: Run model Grad-CAM
        heatmap = self.generate_heatmap(input_tensor=input_tensor, class_idx=class_idx)
        if heatmap is None:
            # Model unavailable or backward hook failed
            return {
                "available": False,
                "status": "ERROR",
                "legacy_status": "error",
                "reason": "Vision model error: Grad-CAM could not be computed for this image.",
                "original_image_base64": orig_b64,
                "pure_heatmap_base64": None,
                "gradcam_heatmap_base64": None,
                "gradcam_overlay_base64": None,
                "focus_regions": [],
                "metadata": metadata,
                "disclaimer": "Vision analysis could not be completed.",
                "message": "Vision model error: Grad-CAM could not be computed for this image."
            }

        # Real heatmap succeeded -> blend overlay
        import matplotlib
        try:
            cmap = matplotlib.colormaps["jet"]
        except Exception:
            cmap = matplotlib.cm.get_cmap("jet")

        colored_hm = cmap(heatmap)[:, :, :3]
        colored_hm = (colored_hm * 255).astype(np.uint8)
        hm_pil = Image.fromarray(colored_hm)

        overlay_pil = Image.blend(base_resized, hm_pil, alpha=alpha)

        buf_hm = io.BytesIO()
        hm_pil.save(buf_hm, format="JPEG", quality=90)
        pure_hm_b64 = "data:image/jpeg;base64," + base64.b64encode(buf_hm.getvalue()).decode("utf-8")

        buf_overlay = io.BytesIO()
        overlay_pil.save(buf_overlay, format="JPEG", quality=92)
        overlay_b64 = "data:image/jpeg;base64," + base64.b64encode(buf_overlay.getvalue()).decode("utf-8")

        regions = self.get_clinical_focus_regions(heatmap)

        return {
            "available": True,
            "status": "AVAILABLE",
            "legacy_status": "available",
            "reason": None,
            "original_image_base64": orig_b64,
            "pure_heatmap_base64": pure_hm_b64,
            "gradcam_heatmap_base64": overlay_b64,
            "gradcam_overlay_base64": overlay_b64,
            "focus_regions": regions,
            "metadata": metadata,
            "clinical_boundary_note": "Visual saliency heatmaps indicate image contrast and edge regions utilized by the neural network for contour estimation. They reflect neural network attention patterns, NOT clinical diagnoses of muscle wasting, fat depletion, or underlying medical conditions.",
            "disclaimer": "AI explanations describe model behavior and feature attribution, not medical causation.",
            "message": "Vision assessment complete."
        }
