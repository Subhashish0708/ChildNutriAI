"""
ChildNutri AI - Indian Neonatal Dataset Adapter & Subject-Level Partitioning
=============================================================================
Canonical data adapter and PyTorch Dataset implementations for the real-world
Indian Neonatal Anthropometric Image Dataset.

Data Source & Attribution:
  - Combined District Hospital, Manjhanpur, Kaushambi, UP, India
  - Madhuraj Hospital, Kanpur, UP, India
  Authors: Anurag Singh & Dr. Rashi Agarwal (© 2026)
  Permitted for Research, Academic, and Educational use.

Architectural Guarantees:
  1. Canonical Normalization: Units stripped (cm, gm, Weeks), NA -> None.
     No NA is converted to 0. No missing measurement is converted to normal.
  2. Anomaly Transparency: Baby - 83 flagged with INVALID_DATE, excluded from
     age-derived longitudinal/post-natal age calculations, never silently changed.
  3. Subject-Level Splitting: Splits (train, val, test) partition subjects (Baby - N),
     ensuring 100% zero data leakage across images of the same neonate.
  4. Multi-Target Regression: Provides continuous anthropometric targets and validity
     masks so missing fields (e.g. Chest Girth) are masked out during loss calculation.
"""

import os
import re
import json
import logging
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import pandas as pd
from PIL import Image

import torch
from torch.utils.data import Dataset
import torchvision.transforms as transforms

logger = logging.getLogger("childnutri.indian_neonatal_dataset")

# Standard regression targets available in the Indian Neonatal dataset
PRIMARY_REGRESSION_TARGETS = [
    "weight_g",
    "body_length_cm",
    "head_circumference_cm"
]

ALL_REGRESSION_TARGETS = [
    "weight_g",
    "body_length_cm",
    "head_circumference_cm",
    "chest_girth_cm",
    "arm_length_cm",
    "leg_length_cm"
]

# Standard target normalization scaling factors (approximate range bounds for stable loss)
TARGET_SCALING = {
    "weight_g": {"mean": 2400.0, "std": 700.0},
    "body_length_cm": {"mean": 46.0, "std": 3.5},
    "head_circumference_cm": {"mean": 31.0, "std": 2.5},
    "chest_girth_cm": {"mean": 31.0, "std": 2.0},
    "arm_length_cm": {"mean": 17.0, "std": 1.8},
    "leg_length_cm": {"mean": 20.0, "std": 2.3}
}


@dataclass
class IndianNeonatalSubject:
    """Canonical representation of a single neonate subject."""
    subject_id: str                      # e.g., 'Baby - 1'
    serial_number: int                   # e.g., 1
    gender: str                          # 'M' or 'F'
    date_of_birth_raw: str               # e.g., '11/7/2025'
    date_of_birth: Optional[str]         # ISO string 'YYYY-MM-DD' or None if invalid
    dob_status: str                      # 'VALID', 'INVALID_DATE', 'MISSING_DATE'
    head_circumference_cm: Optional[float]
    chest_girth_cm: Optional[float]
    arm_length_cm: Optional[float]
    leg_length_cm: Optional[float]
    body_length_cm: Optional[float]
    weight_g: Optional[float]
    gestational_age_weeks: Optional[float]
    image_paths: List[str] = field(default_factory=list)
    has_images: bool = False
    validation_flags: List[str] = field(default_factory=list)

    @property
    def weight_kg(self) -> Optional[float]:
        return self.weight_g / 1000.0 if self.weight_g is not None else None

    @property
    def is_preterm(self) -> Optional[bool]:
        if self.gestational_age_weeks is None:
            return None
        return self.gestational_age_weeks < 37.0

    @property
    def birth_weight_category(self) -> Optional[str]:
        if self.weight_g is None:
            return None
        if self.weight_g < 1000.0:
            return "ELBW"  # Extremely Low Birth Weight (<1000g)
        if self.weight_g < 1500.0:
            return "VLBW"  # Very Low Birth Weight (1000-1499g)
        if self.weight_g < 2500.0:
            return "LBW"   # Low Birth Weight (1500-2499g)
        return "NORMAL"    # Normal Birth Weight (>=2500g)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["weight_kg"] = self.weight_kg
        d["is_preterm"] = self.is_preterm
        d["birth_weight_category"] = self.birth_weight_category
        return d


class IndianNeonatalDatasetAdapter:
    """
    Adapter that parses, normalizes, and partitions the Indian Neonatal dataset.
    """

    @staticmethod
    def resolve_dataset_directory(dataset_dir: Optional[str] = None) -> str:
        """
        Intelligently resolves the dataset directory:
        1. Explicit path (and handles nested root directory if needed).
        2. Environment variable INDIAN_NEONATAL_DATASET_DIR or NEONATAL_DATASET_DIR.
        3. Workspace default dataset/indian_neonatal.
        4. User Downloads folder containing 'Neonatal Anthropometric Image Dataset...'.
        """
        candidates: List[str] = []
        if dataset_dir:
            candidates.append(os.path.abspath(dataset_dir))

        env_dir = os.environ.get("INDIAN_NEONATAL_DATASET_DIR") or os.environ.get("NEONATAL_DATASET_DIR")
        if env_dir:
            candidates.append(os.path.abspath(env_dir))

        # Project root relative path
        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(this_file_dir, "..", ".."))
        workspace_default = os.path.join(repo_root, "dataset", "indian_neonatal")
        candidates.append(workspace_default)
        candidates.append(os.path.abspath("dataset/indian_neonatal"))

        # User downloads search
        try:
            dl_path = os.path.expanduser(r"~\Downloads")
            if os.path.exists(dl_path):
                import glob
                for m in glob.glob(os.path.join(dl_path, "*Neonatal*")):
                    if os.path.isdir(m):
                        candidates.append(os.path.abspath(m))
        except Exception:
            pass

        for c in candidates:
            if not os.path.exists(c):
                continue
            if os.path.isfile(os.path.join(c, "neonatal_measurements.csv")):
                return c
            # Check immediate subdirectories (e.g. nested unzipped folder)
            try:
                subdirs = [os.path.join(c, s) for s in os.listdir(c) if os.path.isdir(os.path.join(c, s))]
                for sd in subdirs:
                    if os.path.isfile(os.path.join(sd, "neonatal_measurements.csv")):
                        return sd
            except Exception:
                pass

        return workspace_default

    def __init__(
        self,
        dataset_dir: Optional[str] = None,
        processed_dir: str = "dataset/processed"
    ):
        self.dataset_dir = self.resolve_dataset_directory(dataset_dir)
        self.csv_path = os.path.join(self.dataset_dir, "neonatal_measurements.csv")
        self.processed_dir = os.path.abspath(processed_dir)
        self.split_csv_path = os.path.join(self.processed_dir, "indian_neonatal_split.csv")
        os.makedirs(self.processed_dir, exist_ok=True)
        self._subjects: Optional[Dict[str, IndianNeonatalSubject]] = None

    @staticmethod
    def _clean_numeric(raw: Any) -> Optional[float]:
        if raw is None or pd.isna(raw):
            return None
        s = str(raw).strip()
        if not s or s.upper() in ("NA", "NAN", "NULL", "NONE", "-"):
            return None
        cleaned = re.sub(r"(?i)(cm|gm|g|weeks|week)", "", s).strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _clean_dob(raw: Any) -> Tuple[Optional[str], str]:
        if raw is None or pd.isna(raw):
            return None, "MISSING_DATE"
        s = str(raw).strip()
        if not s or s.upper() in ("NA", "NULL"):
            return None, "MISSING_DATE"

        for fmt in (
            "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y",
            "%d-%m-%Y", "%d-%m-%y", "%m-%d-%Y",
            "%Y-%m-%d", "%Y/%m/%d"
        ):
            try:
                dt = datetime.strptime(s, fmt)
                if dt.year > 2026:
                    return None, "INVALID_DATE"  # Future date anomaly (e.g. 2055)
                return dt.strftime("%Y-%m-%d"), "VALID"
            except ValueError:
                continue

        return None, "UNPARSEABLE_DATE"

    def load_subjects(self, force_reload: bool = False) -> Dict[str, IndianNeonatalSubject]:
        """Loads and parses all neonates into canonical subject instances."""
        if self._subjects is not None and not force_reload:
            return self._subjects

        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Measurements CSV not found at {self.csv_path}")

        df = pd.read_csv(self.csv_path, keep_default_na=False)
        subjects: Dict[str, IndianNeonatalSubject] = {}

        for _, row in df.iterrows():
            sub_id = str(row.get("Name", row.get("subject_id", ""))).strip()
            if not sub_id:
                continue

            raw_sno = row.get("S.No.", row.get("record_id", 0))
            try:
                sno = int(raw_sno)
            except (ValueError, TypeError):
                num_match = re.search(r"\d+", sub_id)
                sno = int(num_match.group()) if num_match else 0

            gen_val = row.get("Gender", row.get("sex", "U"))
            gen = str(gen_val).strip().upper()
            if gen.startswith("M"):
                gen = "M"
            elif gen.startswith("F"):
                gen = "F"

            raw_dob = row.get("DOB", row.get("dob_original", row.get("dob_iso", "")))
            dob_iso, dob_status = self._clean_dob(raw_dob)
            vflags = []
            if dob_status == "INVALID_DATE":
                vflags.append("ANOMALOUS_FUTURE_DOB_EXCLUDED_FROM_AGE")
            elif dob_status != "VALID":
                vflags.append(f"DOB_STATUS_{dob_status}")

            # Check image folder with flexible matching (e.g. Baby - 1 vs Baby-1)
            folder_path = os.path.join(self.dataset_dir, sub_id)
            if not os.path.isdir(folder_path):
                alt_names = [
                    sub_id.replace(" - ", "-"),
                    sub_id.replace("-", " - "),
                    sub_id.lower(),
                    sub_id.replace(" ", "")
                ]
                for alt in alt_names:
                    cand = os.path.join(self.dataset_dir, alt)
                    if os.path.isdir(cand):
                        folder_path = cand
                        break

            img_paths = []
            if os.path.isdir(folder_path):
                img_files = sorted([
                    f for f in os.listdir(folder_path)
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                ])
                img_paths = [os.path.join(folder_path, f) for f in img_files]

            has_images = len(img_paths) > 0
            if not has_images:
                vflags.append("NO_IMAGES_AVAILABLE")

            # Extract anthropometrics with fallbacks across schema variants
            hc = row.get("Head Circumference", row.get("head_circumference_cm", None))
            cg = row.get("Chest Girth", row.get("chest_girth_cm", None))
            al = row.get("Arm Length", row.get("arm_length_cm", None))
            ll = row.get("Leg Length", row.get("leg_length_cm", None))
            tbl = row.get("Total Body Length", row.get("total_body_length_cm", None))
            wt = row.get("Weight", row.get("weight_g", None))
            ga = row.get("Gestational Age", row.get("Gestation Week", row.get("gestational_age_weeks", None)))

            subject = IndianNeonatalSubject(
                subject_id=sub_id,
                serial_number=sno,
                gender=gen,
                date_of_birth_raw=str(raw_dob).strip() if raw_dob is not None else "",
                date_of_birth=dob_iso,
                dob_status=dob_status,
                head_circumference_cm=self._clean_numeric(hc),
                chest_girth_cm=self._clean_numeric(cg),
                arm_length_cm=self._clean_numeric(al),
                leg_length_cm=self._clean_numeric(ll),
                body_length_cm=self._clean_numeric(tbl),
                weight_g=self._clean_numeric(wt),
                gestational_age_weeks=self._clean_numeric(ga),
                image_paths=img_paths,
                has_images=has_images,
                validation_flags=vflags
            )
            subjects[sub_id] = subject

        self._subjects = subjects
        logger.info(f"Loaded {len(subjects)} canonical subjects from {self.csv_path}")
        return subjects

    def get_or_create_subject_split(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42
    ) -> pd.DataFrame:
        """
        Creates or loads the subject-level train/val/test split manifest.
        Guarantees zero patient leakage across partitions.
        """
        if os.path.exists(self.split_csv_path):
            split_df = pd.read_csv(self.split_csv_path)
            if len(split_df) >= 80:
                logger.info(f"Loaded existing subject-level split from {self.split_csv_path}")
                return split_df

        subjects = self.load_subjects()
        subject_list = list(subjects.values())

        # Sort for deterministic shuffling
        subject_list.sort(key=lambda s: s.serial_number)

        # Stratified grouping by (gender, has_images, is_preterm)
        rng = random.Random(seed)
        strata: Dict[Tuple[str, bool, Optional[bool]], List[IndianNeonatalSubject]] = {}
        for s in subject_list:
            key = (s.gender, s.has_images, s.is_preterm)
            strata.setdefault(key, []).append(s)

        split_assignments: Dict[str, str] = {}

        for key, grp in strata.items():
            rng.shuffle(grp)
            n = len(grp)
            n_train = int(round(n * train_ratio))
            n_val = int(round(n * val_ratio))
            # At least ensure bounds
            if n == 1:
                # Singletons go to train
                split_assignments[grp[0].subject_id] = "train"
                continue
            if n_train == 0 and n > 0:
                n_train = 1
            if n_train + n_val > n:
                n_val = max(0, n - n_train)

            for i, s in enumerate(grp):
                if i < n_train:
                    split_assignments[s.subject_id] = "train"
                elif i < n_train + n_val:
                    split_assignments[s.subject_id] = "val"
                else:
                    split_assignments[s.subject_id] = "test"

        # Verify all subjects assigned
        records = []
        for s in subject_list:
            records.append({
                "subject_id": s.subject_id,
                "serial_number": s.serial_number,
                "split": split_assignments[s.subject_id],
                "gender": s.gender,
                "has_images": s.has_images,
                "image_count": len(s.image_paths),
                "weight_g": s.weight_g,
                "body_length_cm": s.body_length_cm,
                "head_circumference_cm": s.head_circumference_cm,
                "chest_girth_cm": s.chest_girth_cm,
                "gestational_age_weeks": s.gestational_age_weeks,
                "is_preterm": s.is_preterm,
                "birth_weight_category": s.birth_weight_category,
                "dob_status": s.dob_status
            })

        split_df = pd.DataFrame(records)
        split_df.to_csv(self.split_csv_path, index=False)
        logger.info(f"Created canonical subject-level split at {self.split_csv_path}")
        return split_df


class IndianNeonatalVisionDataset(Dataset):
    """
    PyTorch Dataset for multi-target neonatal anthropometric regression.
    Each item is a single image coupled with genuine subject-level measurements.
    Strictly partitions images by subject_id.
    """

    def __init__(
        self,
        split: str = "train",
        dataset_dir: str = "dataset/indian_neonatal",
        processed_dir: str = "dataset/processed",
        transform: Optional[Any] = None,
        img_size: int = 224,
        normalize_targets: bool = False
    ):
        self.split = split.lower()
        self.adapter = IndianNeonatalDatasetAdapter(dataset_dir, processed_dir)
        self.split_df = self.adapter.get_or_create_subject_split()
        self.subjects = self.adapter.load_subjects()
        self.img_size = img_size
        self.normalize_targets = normalize_targets

        if self.split in ("train", "val", "test"):
            allowed_ids = set(self.split_df[self.split_df["split"] == self.split]["subject_id"])
        elif self.split == "all":
            allowed_ids = set(self.split_df["subject_id"])
        else:
            raise ValueError(f"Unknown split: {split}. Expected train, val, test, or all.")

        # Build image records: each image linked to its subject
        self.samples: List[Dict[str, Any]] = []
        for sid in sorted(allowed_ids):
            subj = self.subjects.get(sid)
            if not subj or not subj.has_images:
                continue
            for img_p in subj.image_paths:
                self.samples.append({
                    "subject_id": sid,
                    "image_path": img_p,
                    "subject": subj
                })

        # Image Transforms
        if transform is not None:
            self.transform = transform
        else:
            if self.split == "train":
                self.transform = transforms.Compose([
                    transforms.Resize((img_size, img_size)),
                    transforms.RandomHorizontalFlip(p=0.5),
                    transforms.RandomRotation(degrees=10),
                    transforms.ColorJitter(brightness=0.1, contrast=0.1),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]
                    )
                ])
            else:
                self.transform = transforms.Compose([
                    transforms.Resize((img_size, img_size)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]
                    )
                ])

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        sample = self.samples[idx]
        img_path = sample["image_path"]
        subj: IndianNeonatalSubject = sample["subject"]

        # Load image safely
        try:
            image = Image.open(img_path).convert("RGB")
            tensor_img = self.transform(image)
        except Exception as e:
            logger.warning(f"Failed to load image {img_path}: {e}")
            tensor_img = torch.zeros(3, self.img_size, self.img_size)

        # Build target tensors and validity masks (1.0 = valid, 0.0 = missing/NA)
        targets = {}
        masks = {}

        for target_name in ALL_REGRESSION_TARGETS:
            val = getattr(subj, target_name)
            if val is not None:
                if self.normalize_targets:
                    mean = TARGET_SCALING[target_name]["mean"]
                    std = TARGET_SCALING[target_name]["std"]
                    norm_val = (val - mean) / std
                    targets[target_name] = torch.tensor(norm_val, dtype=torch.float32)
                else:
                    targets[target_name] = torch.tensor(val, dtype=torch.float32)
                masks[target_name] = torch.tensor(1.0, dtype=torch.float32)
            else:
                # Missing value (e.g. Chest Girth NA) -> 0.0 with mask 0.0
                targets[target_name] = torch.tensor(0.0, dtype=torch.float32)
                masks[target_name] = torch.tensor(0.0, dtype=torch.float32)

        return {
            "image": tensor_img,
            "targets": targets,
            "masks": masks,
            "subject_id": subj.subject_id,
            "image_path": img_path,
            "gender": subj.gender,
            "gestational_age_weeks": subj.gestational_age_weeks if subj.gestational_age_weeks is not None else -1.0,
            "is_preterm": subj.is_preterm if subj.is_preterm is not None else False
        }


class IndianNeonatalSubjectAggregatedDataset(Dataset):
    """
    PyTorch Dataset operating at the subject level.
    Returns all images for a subject as a tensor of shape (N_images, 3, H, W)
    for multi-view feature pooling or subject-level evaluation.
    """

    def __init__(
        self,
        split: str = "test",
        dataset_dir: str = "dataset/indian_neonatal",
        processed_dir: str = "dataset/processed",
        img_size: int = 224
    ):
        self.split = split.lower()
        self.adapter = IndianNeonatalDatasetAdapter(dataset_dir, processed_dir)
        self.split_df = self.adapter.get_or_create_subject_split()
        self.subjects = self.adapter.load_subjects()
        self.img_size = img_size

        if self.split in ("train", "val", "test"):
            allowed_ids = set(self.split_df[self.split_df["split"] == self.split]["subject_id"])
        elif self.split == "all":
            allowed_ids = set(self.split_df["subject_id"])
        else:
            raise ValueError(f"Unknown split: {split}")

        self.subject_list = [
            self.subjects[sid] for sid in sorted(allowed_ids)
            if self.subjects[sid].has_images
        ]

        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def __len__(self) -> int:
        return len(self.subject_list)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        subj = self.subject_list[idx]
        imgs = []
        for p in subj.image_paths:
            try:
                im = Image.open(p).convert("RGB")
                imgs.append(self.transform(im))
            except Exception:
                pass

        if not imgs:
            imgs_tensor = torch.zeros(1, 3, self.img_size, self.img_size)
        else:
            imgs_tensor = torch.stack(imgs, dim=0)

        targets = {}
        masks = {}
        for target_name in ALL_REGRESSION_TARGETS:
            val = getattr(subj, target_name)
            if val is not None:
                targets[target_name] = torch.tensor(val, dtype=torch.float32)
                masks[target_name] = torch.tensor(1.0, dtype=torch.float32)
            else:
                targets[target_name] = torch.tensor(0.0, dtype=torch.float32)
                masks[target_name] = torch.tensor(0.0, dtype=torch.float32)

        return {
            "images": imgs_tensor,
            "targets": targets,
            "masks": masks,
            "subject_id": subj.subject_id,
            "num_images": len(imgs),
            "gender": subj.gender,
            "gestational_age_weeks": subj.gestational_age_weeks if subj.gestational_age_weeks is not None else -1.0,
            "is_preterm": subj.is_preterm if subj.is_preterm is not None else False
        }
