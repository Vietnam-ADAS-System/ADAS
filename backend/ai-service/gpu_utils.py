"""
GPU/Device detection and management utilities.
Giúp xác định và quản lý GPU/CPU cho inference.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def check_cuda_available() -> bool:
    """
    Kiểm tra xem CUDA có khả dụng không.
    
    Returns:
        bool: True nếu PyTorch có thể dùng CUDA, False nếu chỉ có CPU
    """
    try:
        import torch
        available = torch.cuda.is_available()
        if available:
            device_name = torch.cuda.get_device_name(0)
            device_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"✅ CUDA Available: {device_name} ({device_memory:.1f}GB)")
        else:
            logger.warning("⚠️ CUDA not available - falling back to CPU")
        return available
    except Exception as e:
        logger.warning(f"⚠️ Error checking CUDA: {e} - using CPU")
        return False


def get_inference_device() -> Optional[int]:
    """
    Lấy device ID cho inference (0 = GPU, None = CPU auto-select).
    
    Ưu tiên:
    1. Environment variable AI_DEVICE nếu set
    2. Auto-detect CUDA nếu có
    3. Fallback CPU
    
    Returns:
        int or None:
            - 0: GPU device 0 (nếu CUDA available)
            - None: CPU (auto-select)
    """
    # Check env var trước
    env_device = os.getenv("AI_DEVICE", "").strip().lower()
    if env_device:
        if env_device == "auto":
            # Auto-detect
            if check_cuda_available():
                logger.info("🚀 Using GPU (auto-detected)")
                return 0
            else:
                logger.info("💻 Using CPU (CUDA not available)")
                return None
        elif env_device == "cpu":
            logger.info("💻 Using CPU (forced via AI_DEVICE=cpu)")
            return None
        elif env_device in ("gpu", "0", "cuda"):
            logger.info("🚀 Using GPU (forced via AI_DEVICE=gpu)")
            return 0
        else:
            try:
                device_id = int(env_device)
                logger.info(f"🚀 Using GPU device {device_id}")
                return device_id
            except ValueError:
                logger.warning(f"Invalid AI_DEVICE={env_device}, auto-detecting")
    
    # Auto-detect nếu env var không set
    if check_cuda_available():
        logger.info("🚀 Using GPU (auto-detected)")
        return 0
    else:
        logger.info("💻 Using CPU (CUDA not available)")
        return None


def log_inference_device(device: Optional[int]) -> None:
    """
    Log thông tin device được sử dụng.
    
    Args:
        device: Device ID (0 = GPU 0, None = CPU)
    """
    if device is None:
        logger.debug("Inference device: CPU (auto-selected)")
    elif isinstance(device, int):
        logger.debug(f"Inference device: GPU {device}")
    else:
        logger.debug(f"Inference device: {device}")
