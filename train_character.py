#!/usr/bin/env python3

import argparse
import gc
import os
import sys
import torch
from dataclasses import dataclass
from dotenv import load_dotenv

from helpers import run_subprocess
from training.generate_sheet import timing

load_dotenv()

from training.generate_sheet import generate_char_sheet


@dataclass
class CharacterConfig:
    """Configuration for character generation and training."""
    name: str
    input_image: str
    work_dir: str = None
    steps: int = 800
    batch_size: int = 1
    learning_rate: float = 8e-4
    train_dim: int = 512
    rank_dim: int = 8
    log_file: str = None
    pulidflux_images: int = 0

    # Model configuration
    base_model: str = "RunDiffusion/Juggernaut-XL-v9"
    vae_model: str = "madebyollin/sdxl-vae-fp16-fix"
    unet_model: str = None
    scheduler: str = "ddpm"
    dtype: str = "float16"

    # MV Adapter configuration
    use_mv_adapter: bool = False
    adapter_path: str = "huanngzh/mv-adapter"
    num_views: int = 6
    mv_height: int = 768
    mv_width: int = 768
    guidance_scale: float = 3.0
    reference_conditioning_scale: float = 1.0
    azimuth_degrees: list = None
    remove_background: bool = True

    # Advanced training configuration
    optimizer: str = "adamw"
    weight_decay: float = 0.01
    lr_scheduler: str = "constant"
    gradient_accumulation: int = 1
    mixed_precision: str = "fp16"
    save_every: int = 250
    max_saves: int = 5
    gradient_checkpointing: bool = False
    train_text_encoder: bool = False

    # ComfyUI model paths
    comfyui_checkpoint: str = None
    comfyui_vae: str = None
    comfyui_lora: str = None

    def __post_init__(self):
        if self.azimuth_degrees is None:
            self.azimuth_degrees = [0, 45, 90, 180, 270, 315]


def build_charsheet(config: CharacterConfig):
    """
    Process a character through the complete workflow:
    1. Generate character sheet
    2. Caption the generated images
    
    Args:
        name (str): Character name
        input_image (str): Path to input image
        work_dir (str, optional): Working directory path. If None, uses ./scratch/{name}/
    
    Returns:
        str: Path to directory containing all generated images and captions
    """
    # Step 1: Generate character sheet
    print(f"Step 1: Generating character sheet for '{config.name}'")
    if config.work_dir is None:
        app_path = os.environ.get('APP_PATH', os.getcwd())
        config.work_dir = os.path.join(app_path, 'scratch', config.name)

    sheet_dir = os.path.join(config.work_dir, "sheet")
    os.makedirs(sheet_dir, exist_ok=True)

    # Set up log file if not provided
    if config.log_file is None:
        config.log_file = os.path.join(config.work_dir, "timing.log")
        # Clear previous log if exists
        if os.path.exists(config.log_file):
            open(config.log_file, 'w').close()

    with timing("Character sheet", config.log_file):
        sheet_images = generate_char_sheet(
            name=config.name,
            input_image=config.input_image,
            work_dir=sheet_dir,
            log_file=config.log_file,
            pulidflux_images=config.pulidflux_images
        )

    print(f"Generated {len(sheet_images)} character sheet images")

    # Step 2: Caption the generated images
    print("\nStep 2: Captioning character sheet images")

    # Get absolute path of the sheet directory
    abs_sheet_dir = os.path.abspath(sheet_dir)

    # Get path to image_info.json
    json_path = os.path.join(abs_sheet_dir, "image_info.json")
    if not os.path.exists(json_path):
        print(f"Warning: image_info.json not found at {json_path}")
        json_path = None

    # Make the bash script executable
    script_path = os.path.join(os.environ.get('APP_PATH', os.getcwd()), "scripts/run_captioner.sh")
    os.chmod(script_path, 0o755)  # rwxr-xr-x permissions

    # Build the command
    cmd = [
        script_path,
        abs_sheet_dir,
        abs_sheet_dir,
        "yes" if config.pulidflux_images == 0 else "no"
    ]
    # Only add partial captions if available
    if json_path:
        cmd.append(json_path)
        print(f"Using partial captions from: {json_path}")

    try:
        print(f"Running image captioner for '{config.name}'")
        with timing("Image captioning", config.log_file):
            run_subprocess(cmd)

        # Check for caption files
        captions = []
        for img_path in sheet_images:
            caption_path = os.path.splitext(img_path)[0] + ".txt"
            if os.path.exists(caption_path):
                with open(caption_path, 'r', encoding='utf-8') as f:
                    captions.append(f.read().strip())
                print(f"Captioned: {os.path.basename(img_path)}")
            else:
                print(f"Warning: No caption found for {os.path.basename(img_path)}")
                captions.append("")
    except Exception as e:
        print(f"Error running image captioner: {e}")
        captions = [""] * len(sheet_images)

    print(f"\nWorkflow complete for character '{config.name}'")
    print(f"All files saved to: {config.work_dir}")

    return config.work_dir


def train_lora(config: CharacterConfig):
    """
    Train a LoRA model for a character.
    
    Args:
        name (str): Character name
        work_dir (str, optional): Working directory path. If None, uses ./scratch/{name}/
    
    Returns:
        str: Path to directory containing LoRA weights
    """
    # Set default work_dir if not provided
    if config.work_dir is None:
        app_path = os.environ.get('APP_PATH', os.getcwd())
        config.work_dir = os.path.join(app_path, 'scratch', config.name)

    # Ensure work_dir exists
    os.makedirs(config.work_dir, exist_ok=True)

    sheet_dir = os.path.join(config.work_dir, "sheet")

    # Path for the customized YAML config
    config_path = os.path.join(config.work_dir, f"config.yaml")

    template_path = os.path.join(os.environ.get('APP_PATH', os.getcwd()), "scripts/character_lora.yaml")

    # Read the template config
    with open(template_path, 'r', encoding='utf-8') as f:
        config_content = f.read()

    # Convert paths to absolute paths
    abs_work_dir = os.path.abspath(config.work_dir)
    abs_sheet_dir = os.path.abspath(sheet_dir)

    # Replace placeholders with actual absolute values
    config_content = config_content.replace("TRAINING_DIR", abs_work_dir)
    config_content = config_content.replace("DATASET_DIR", abs_sheet_dir)
    config_content = config_content.replace("TRAIN_DIM", str(config.train_dim))
    config_content = config_content.replace("BATCH_SIZE", str(config.batch_size))
    config_content = config_content.replace("STEPS", str(config.steps))
    config_content = config_content.replace("LEARNING_RATE", str(config.learning_rate))
    config_content = config_content.replace("RANK_DIM", str(config.rank_dim))

    # Write the customized config to the working directory
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"Created LoRA training config at: {config_path}")

    # Convert config_path to absolute path
    abs_config_path = os.path.abspath(config_path)

    try:
        # Make the bash script executable
        script_path = os.path.join(os.environ.get('APP_PATH', os.getcwd()), "scripts/run_ai_toolkit.sh")
        os.chmod(script_path, 0o755)  # rwxr-xr-x permissions

        # Run the bash script
        cmd = [
            script_path, abs_config_path
        ]

        print(f"Training LoRA for character '{config.name}'")
        training_output = run_subprocess(cmd)
        print(training_output)

    except Exception as e:
        print(f"Error training LoRA: {e}")

    print(f"\nLoRA training complete for character '{config.name}'")
    print(f"LoRA weights saved to: {config.work_dir}")

    return config.work_dir


def clear_cuda_memory():
    """Clear CUDA memory to free up resources."""
    print("\nClearing CUDA memory...")
    run_subprocess(["nvidia-smi"])

    # Use the centralized cleanup function from generate_sheet
    from training.generate_sheet import cleanup_generation_models
    cleanup_generation_models()

    # Additional memory cleanup specific to this script
    gc.collect()
    torch.cuda.empty_cache()

    run_subprocess(["nvidia-smi"])
    print("CUDA memory cleared successfully")


def build_character(config: CharacterConfig):
    """
    Complete character workflow:
    1. Create working directory
    2. Generate character sheet and captions
    3. Train LoRA model
    
    Args:
        config (CharacterConfig): Configuration object containing all parameters
    
    Returns:
        str: Path to working directory containing all generated assets
    """
    # Set default work_dir if not provided
    if config.work_dir is None:
        app_path = os.environ.get('APP_PATH', os.getcwd())
        config.work_dir = os.path.join(app_path, 'scratch', config.name)

    # Ensure work_dir exists
    os.makedirs(config.work_dir, exist_ok=True)

    # Set up log file if not provided
    if config.log_file is None:
        config.log_file = os.path.join(config.work_dir, "timing.log")
        # Clear previous log if exists
        if os.path.exists(config.log_file):
            open(config.log_file, 'w').close()

    print(f"Starting complete workflow for character '{config.name}'")
    print(f"Working directory: {config.work_dir}")

    with timing("Total workflow", config.log_file):
        # Step 1 & 2: Generate character sheet and captions
        print("\nGenerating character sheet and captions...")
        build_charsheet(config)

        # Clear CUDA memory before training
        print("\nExplicitly clearing CUDA memory before training...")
        with timing("memory cleanup", config.log_file):
            clear_cuda_memory()

        # Step 3: Preprocess dataset before training
        print("\nPreprocessing dataset before training...")
        from training.utilities import preprocess_dataset_before_training
        sheet_dir = os.path.join(config.work_dir, "sheet")
        with timing("Dataset preprocessing", config.log_file):
            preprocess_dataset_before_training(sheet_dir)

        # Step 4: Train LoRA model
        print("\nTraining LoRA model...")
        with timing("LoRA training", config.log_file):
            train_lora(config)

    print(f"\nComplete workflow finished for character '{config.name}'")
    print(f"All assets saved to: {config.work_dir}")

    return config.work_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a character")
    parser.add_argument("--name", type=str, help="Character name")
    parser.add_argument("--input", type=str, help="Path to input image")
    parser.add_argument("--work_dir", type=str, help="Working directory (optional)")
    parser.add_argument("--steps", type=int, default=800, help="Number of steps to train the LoRA model")
    parser.add_argument("--batch_size", type=int, default=1, help="Batch size for training the LoRA model")
    parser.add_argument("--lr", type=float, default=8e-4, help="Learning rate for training the LoRA model")
    parser.add_argument("--train_dim", type=int, default=512, help="Training image dimension")
    parser.add_argument("--rank_dim", type=int, default=8, help="Rank dimension for the LoRA model")
    parser.add_argument("--pulidflux_images", type=int, default=0, help="Number of Pulid-Flux images to include")

    # Model configuration
    parser.add_argument("--base_model", type=str, default="RunDiffusion/Juggernaut-XL-v9", help="Base model to use")
    parser.add_argument("--vae_model", type=str, default="madebyollin/sdxl-vae-fp16-fix", help="VAE model to use")
    parser.add_argument("--unet_model", type=str, help="UNet model to use (optional)")
    parser.add_argument("--scheduler", type=str, default="ddpm", help="Noise scheduler")
    parser.add_argument("--dtype", type=str, default="float16", help="Data type for training")

    # MV Adapter configuration
    parser.add_argument("--use_mv_adapter", action="store_true", help="Enable MV Adapter")
    parser.add_argument("--adapter_path", type=str, default="huanngzh/mv-adapter", help="MV Adapter path")
    parser.add_argument("--num_views", type=int, default=6, help="Number of views for MV Adapter")
    parser.add_argument("--mv_height", type=int, default=768, help="MV Adapter image height")
    parser.add_argument("--mv_width", type=int, default=768, help="MV Adapter image width")
    parser.add_argument("--guidance_scale", type=float, default=3.0, help="Guidance scale for MV Adapter")
    parser.add_argument("--reference_conditioning_scale", type=float, default=1.0, help="Reference conditioning scale")
    parser.add_argument("--azimuth_degrees", type=str, default="0,45,90,180,270,315", help="Azimuth degrees (comma-separated)")
    parser.add_argument("--remove_background", action="store_true", help="Remove background for MV Adapter")

    # Advanced training configuration
    parser.add_argument("--optimizer", type=str, default="adamw", help="Optimizer to use")
    parser.add_argument("--weight_decay", type=float, default=0.01, help="Weight decay")
    parser.add_argument("--lr_scheduler", type=str, default="constant", help="Learning rate scheduler")
    parser.add_argument("--gradient_accumulation", type=int, default=1, help="Gradient accumulation steps")
    parser.add_argument("--mixed_precision", type=str, default="fp16", help="Mixed precision training")
    parser.add_argument("--save_every", type=int, default=250, help="Save checkpoint every N steps")
    parser.add_argument("--max_saves", type=int, default=5, help="Maximum number of checkpoints to keep")
    parser.add_argument("--gradient_checkpointing", action="store_true", help="Enable gradient checkpointing")
    parser.add_argument("--train_text_encoder", action="store_true", help="Train text encoder")

    # ComfyUI model paths
    parser.add_argument("--comfyui_checkpoint", type=str, help="ComfyUI checkpoint path")
    parser.add_argument("--comfyui_vae", type=str, help="ComfyUI VAE path")
    parser.add_argument("--comfyui_lora", type=str, help="ComfyUI LoRA path")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input image '{args.input}' does not exist.")
        sys.exit(1)

    # Parse azimuth degrees
    azimuth_degrees = [int(x.strip()) for x in args.azimuth_degrees.split(',')]

    config = CharacterConfig(
        name=args.name,
        input_image=args.input,
        work_dir=args.work_dir,
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        train_dim=args.train_dim,
        rank_dim=args.rank_dim,
        pulidflux_images=args.pulidflux_images,

        # Model configuration
        base_model=args.base_model,
        vae_model=args.vae_model,
        unet_model=args.unet_model,
        scheduler=args.scheduler,
        dtype=args.dtype,

        # MV Adapter configuration
        use_mv_adapter=args.use_mv_adapter,
        adapter_path=args.adapter_path,
        num_views=args.num_views,
        mv_height=args.mv_height,
        mv_width=args.mv_width,
        guidance_scale=args.guidance_scale,
        reference_conditioning_scale=args.reference_conditioning_scale,
        azimuth_degrees=azimuth_degrees,
        remove_background=args.remove_background,

        # Advanced training configuration
        optimizer=args.optimizer,
        weight_decay=args.weight_decay,
        lr_scheduler=args.lr_scheduler,
        gradient_accumulation=args.gradient_accumulation,
        mixed_precision=args.mixed_precision,
        save_every=args.save_every,
        max_saves=args.max_saves,
        gradient_checkpointing=args.gradient_checkpointing,
        train_text_encoder=args.train_text_encoder,

        # ComfyUI model paths
        comfyui_checkpoint=args.comfyui_checkpoint,
        comfyui_vae=args.comfyui_vae,
        comfyui_lora=args.comfyui_lora
    )

    output_dir = build_character(config)
    print(f"Character assets directory: {output_dir}")
