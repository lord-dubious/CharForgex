import os
import sys
import subprocess
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import shutil

from app.core.config import settings

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
    pulidflux_images: int = 0

@dataclass
class InferenceConfig:
    """Configuration for character inference."""
    character_name: str
    prompt: str
    work_dir: str = None
    lora_weight: float = 0.73
    test_dim: int = 1024
    do_optimize_prompt: bool = True
    output_filenames: List[str] = None
    batch_size: int = 4
    num_inference_steps: int = 30
    fix_outfit: bool = False
    safety_check: bool = True
    face_enhance: bool = False

class CharForgeIntegration:
    """Integration layer for CharForge Python scripts."""
    
    def __init__(self):
        self.charforge_root = settings.CHARFORGE_ROOT
        self.scratch_dir = settings.CHARFORGE_SCRATCH_DIR
        
        # Ensure CharForge directories exist
        os.makedirs(self.scratch_dir, exist_ok=True)
    
    def setup_environment(self, env_vars: Dict[str, str]) -> Dict[str, str]:
        """Set up environment variables for CharForge."""
        env = os.environ.copy()
        env.update({
            'APP_PATH': str(self.charforge_root),
            'HF_HOME': env_vars.get('HF_HOME', ''),
            'HF_TOKEN': env_vars.get('HF_TOKEN', ''),
            'CIVITAI_API_KEY': env_vars.get('CIVITAI_API_KEY', ''),
            'GOOGLE_API_KEY': env_vars.get('GOOGLE_API_KEY', ''),
            'FAL_KEY': env_vars.get('FAL_KEY', ''),
        })
        return env
    
    async def run_training(
        self, 
        config: CharacterConfig, 
        env_vars: Dict[str, str],
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, any]:
        """Run character training workflow."""
        
        # Set up environment
        env = self.setup_environment(env_vars)
        
        # Prepare command
        cmd = [
            sys.executable,
            str(self.charforge_root / "train_character.py"),
            "--name", config.name,
            "--input", config.input_image,
            "--steps", str(config.steps),
            "--batch_size", str(config.batch_size),
            "--lr", str(config.learning_rate),
            "--train_dim", str(config.train_dim),
            "--rank_dim", str(config.rank_dim),
            "--pulidflux_images", str(config.pulidflux_images)
        ]
        
        if config.work_dir:
            cmd.extend(["--work_dir", config.work_dir])
        
        # Run the process
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
                cwd=str(self.charforge_root)
            )
            
            output_lines = []
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                line_str = line.decode().strip()
                output_lines.append(line_str)
                
                # Parse progress if callback provided
                if progress_callback:
                    progress = self._parse_training_progress(line_str)
                    if progress is not None:
                        progress_callback(progress, line_str)
            
            await process.wait()
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "output": "\n".join(output_lines),
                "work_dir": config.work_dir or str(self.scratch_dir / config.name)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
    
    async def run_inference(
        self,
        config: InferenceConfig,
        env_vars: Dict[str, str]
    ) -> Dict[str, any]:
        """Run character inference."""
        
        # Set up environment
        env = self.setup_environment(env_vars)
        
        # Prepare command
        cmd = [
            sys.executable,
            str(self.charforge_root / "test_character.py"),
            "--character_name", config.character_name,
            "--prompt", config.prompt,
            "--lora_weight", str(config.lora_weight),
            "--test_dim", str(config.test_dim),
            "--batch_size", str(config.batch_size),
            "--num_inference_steps", str(config.num_inference_steps)
        ]
        
        # Add optional flags
        if config.work_dir:
            cmd.extend(["--work_dir", config.work_dir])
        
        if config.output_filenames:
            cmd.extend(["--output_filenames"] + config.output_filenames)
        
        if not config.do_optimize_prompt:
            cmd.append("--no_optimize_prompt")
        
        if config.fix_outfit:
            cmd.append("--fix_outfit")
        
        if not config.safety_check:
            cmd.append("--no_safety_check")
        
        if config.face_enhance:
            cmd.append("--face_enhance")
        
        # Run the process
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
                cwd=str(self.charforge_root)
            )
            
            output_lines = []
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                line_str = line.decode().strip()
                output_lines.append(line_str)
            
            await process.wait()
            
            # Parse output files
            output_files = self._parse_inference_output(output_lines, config)
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "output": "\n".join(output_lines),
                "output_files": output_files
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "output_files": []
            }
    
    def _parse_training_progress(self, line: str) -> Optional[float]:
        """Parse training progress from output line."""
        # Look for progress indicators in the output
        # This is a simplified version - you might need to adjust based on actual output
        if "Step" in line and "/" in line:
            try:
                # Extract step numbers like "Step 100/800"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "Step" and i + 1 < len(parts):
                        step_info = parts[i + 1]
                        if "/" in step_info:
                            current, total = step_info.split("/")
                            return float(current) / float(total) * 100
            except:
                pass
        return None
    
    def _parse_inference_output(self, output_lines: List[str], config: InferenceConfig) -> List[str]:
        """Parse inference output to extract generated file paths."""
        output_files = []
        for line in output_lines:
            if "Saved image to:" in line:
                # Extract file path from line like "✅ Saved image to: /path/to/file.jpg"
                path = line.split("Saved image to:")[-1].strip()
                output_files.append(path)
        return output_files
    
    def get_character_info(self, character_name: str, work_dir: str = None) -> Dict[str, any]:
        """Get information about a trained character."""
        if work_dir is None:
            work_dir = self.scratch_dir / character_name
        else:
            work_dir = Path(work_dir)
        
        info = {
            "name": character_name,
            "exists": work_dir.exists(),
            "work_dir": str(work_dir),
            "has_lora": False,
            "has_sheet": False,
            "sheet_images": [],
            "lora_path": None
        }
        
        if work_dir.exists():
            # Check for LoRA
            lora_dir = work_dir / "char"
            lora_file = lora_dir / "char.safetensors"
            if lora_file.exists():
                info["has_lora"] = True
                info["lora_path"] = str(lora_file)
            
            # Check for character sheet
            sheet_dir = work_dir / "sheet"
            if sheet_dir.exists():
                info["has_sheet"] = True
                # Get sheet images
                for ext in ["*.png", "*.jpg", "*.jpeg"]:
                    info["sheet_images"].extend([str(p) for p in sheet_dir.glob(ext)])
        
        return info
    
    def list_characters(self) -> List[Dict[str, any]]:
        """List all available characters."""
        characters = []
        if self.scratch_dir.exists():
            for char_dir in self.scratch_dir.iterdir():
                if char_dir.is_dir():
                    char_info = self.get_character_info(char_dir.name, str(char_dir))
                    characters.append(char_info)
        return characters
