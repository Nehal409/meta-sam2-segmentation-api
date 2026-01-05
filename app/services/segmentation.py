import json
import os
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry

from app.core.config import settings
from app.core.logger import logger
from app.utils.mask import is_valid_mask, save_mask_image

model_path = settings.sam_model_path
model_type = "vit_h"
_mask_generator = None


def get_cached_mask_generator():
    global _mask_generator

    if _mask_generator is None:
        try:
            logger.info("Loading SAM model into memory...")

            sam = sam_model_registry[model_type](checkpoint=model_path)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            sam.to(device)
            logger.info(f"SAM model loaded on {device}")

            _mask_generator = SamAutomaticMaskGenerator(
                model=sam,
                points_per_side=32,
                pred_iou_thresh=0.86,
                stability_score_thresh=0.92,
                crop_n_layers=1,
                crop_n_points_downscale_factor=2,
                min_mask_region_area=100,
            )

        except Exception as e:
            logger.error(f"Failed to load SAM model: {e}")
            raise

    return _mask_generator


def build_segment_info(index: int, uuid: str, filename: str, data: dict) -> dict:
    """Create segment metadata for the frontend."""
    x, y, w, h = data["bbox"]
    return {
        "segment_id": index,
        "mask_url": f"{settings.base_url}/assets/{uuid}/mask_images/{filename}",
        "bbox": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
        "area": int(data["area"]),
        "stability_score": float(data["stability_score"]),
        "predicted_iou": float(data["predicted_iou"]),
        "center_point": {"x": int(x + w / 2), "y": int(y + h / 2)},
    }


def run_segmentation(image: Image.Image, uuid: str):
    """
    Run SAM segmentation on image and return mask buffers and segment data
    """
    logger.info(f"Starting automatic segmentation for job {uuid}")

    try:
        # Load SAM model
        mask_generator = get_cached_mask_generator()

        # Convert image to numpy RGB array
        image_np = np.array(image.convert("RGB"))
        logger.info(f"Image shape: {image_np.shape}")

        # Generate masks using SAM
        masks = mask_generator.generate(image_np)
        logger.info(f"Generated {len(masks)} initial masks")

        # Filter and process masks
        valid_masks = []
        for mask_data in masks:
            if is_valid_mask(mask_data):
                valid_masks.append(mask_data)
        logger.info(f"Filtered to {len(valid_masks)} valid masks")

        segments_data = []
        save_dir = os.path.join("assets", uuid, "mask_images")
        os.makedirs(save_dir, exist_ok=True)

        for i, mask_data in enumerate(valid_masks):
            try:
                # Extract mask data
                mask = mask_data["segmentation"]
                if not mask.any():
                    logger.warning(f"Skipping empty mask {i}")
                    continue

                # Create mask image
                filename = f"mask_{i:03d}.png"
                file_path = os.path.join(save_dir, filename)
                save_mask_image(mask, Path(file_path))

                segment_info = build_segment_info(i, uuid, filename, mask_data)
                segments_data.append(segment_info)

            except Exception as e:
                logger.error(f"Failed to process mask {i}: {e}")
                continue

        logger.info(f"Successfully processed {len(valid_masks)} masks for job {uuid}")

        return segments_data

    except Exception as e:
        logger.error(f"Segmentation failed for job {uuid}: {e}")
        raise
