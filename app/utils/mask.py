from pathlib import Path

import numpy as np
from PIL import Image


def create_mask_image(mask: np.ndarray) -> Image.Image:
    """Convert binary mask to RGBA image."""
    rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
    rgba[mask] = [0, 0, 0, 255]
    return Image.fromarray(rgba, "RGBA")


def is_valid_mask(mask_data: dict) -> bool:
    """Check if a mask meets quality thresholds."""
    return (
        mask_data["area"] > 100
        and mask_data["stability_score"] > 0.9
        and mask_data["predicted_iou"] > 0.8
    )


def save_mask_image(mask: np.ndarray, save_path: Path):
    """Save mask image as PNG."""
    image = create_mask_image(mask)
    image.save(save_path, format="PNG", optimize=True)
