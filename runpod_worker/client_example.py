#!/usr/bin/env python3
"""
CharForgex RunPod Client Example
Demonstrates how to interact with the CharForgex RunPod worker
"""

import requests
import base64
import time
import json
import os
from typing import Dict, Any, List, Optional
from PIL import Image
from io import BytesIO

class CharForgexClient:
    """Client for interacting with CharForgex RunPod worker"""
    
    def __init__(self, endpoint_id: str, api_key: str):
        """
        Initialize the client
        
        Args:
            endpoint_id: RunPod endpoint ID
            api_key: RunPod API key
        """
        self.endpoint_id = endpoint_id
        self.api_key = api_key
        self.base_url = f"https://api.runpod.ai/v2/{endpoint_id}"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, data: dict, timeout: int = 300) -> dict:
        """Make a request to the RunPod worker"""
        url = f"{self.base_url}/{endpoint}"
        
        response = requests.post(
            url,
            headers=self.headers,
            json={"input": data},
            timeout=timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string"""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _save_base64_image(self, base64_data: str, output_path: str):
        """Save base64 image data to file"""
        image_data = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_data))
        image.save(output_path)
    
    def health_check(self) -> dict:
        """Check worker health and system status"""
        return self._make_request("runsync", {"operation": "system_status"}, timeout=30)
    
    def list_characters(self) -> List[str]:
        """Get list of available trained characters"""
        result = self._make_request("runsync", {"operation": "list_characters"}, timeout=30)
        
        if result.get('status') == 'completed':
            return [char['name'] for char in result.get('characters', [])]
        else:
            raise Exception(f"Failed to list characters: {result.get('error', 'Unknown error')}")
    
    def train_character(
        self,
        character_name: str,
        image_path: str,
        steps: int = 800,
        learning_rate: float = 8e-4,
        rank_dim: int = 8,
        pulidflux_images: int = 0,
        poll_completion: bool = True
    ) -> dict:
        """
        Train a new character LoRA
        
        Args:
            character_name: Name for the character
            image_path: Path to reference image
            steps: Training steps
            learning_rate: Learning rate
            rank_dim: LoRA rank dimension
            pulidflux_images: Number of PuLID-Flux images to include
            poll_completion: Whether to wait for training completion
            
        Returns:
            Training result
        """
        # Convert image to base64
        image_b64 = self._image_to_base64(image_path)
        
        # Prepare training data
        training_data = {
            "operation": "training",
            "character_name": character_name,
            "input_image": image_b64,
            "steps": steps,
            "learning_rate": learning_rate,
            "rank_dim": rank_dim,
            "pulidflux_images": pulidflux_images
        }
        
        print(f"🚀 Starting training for character: {character_name}")
        
        # Submit training job (async)
        result = self._make_request("run", training_data, timeout=60)
        job_id = result.get('id')
        
        if not job_id:
            raise Exception("Failed to start training job")
        
        print(f"📋 Training job started with ID: {job_id}")
        
        if not poll_completion:
            return {"job_id": job_id, "status": "started"}
        
        # Poll for completion
        print("⏳ Waiting for training to complete (this may take 30-40 minutes)...")
        return self._poll_job_completion(job_id, max_wait_minutes=60)
    
    def generate_images(
        self,
        character_name: str,
        prompt: str,
        lora_weight: float = 0.73,
        image_size: int = 1024,
        batch_size: int = 1,
        num_inference_steps: int = 30,
        face_enhance: bool = False,
        save_to_dir: Optional[str] = None
    ) -> List[str]:
        """
        Generate images with a trained character
        
        Args:
            character_name: Name of trained character
            prompt: Text prompt for generation
            lora_weight: LoRA strength (0.1-2.0)
            image_size: Image dimensions
            batch_size: Number of images to generate
            num_inference_steps: Inference steps
            face_enhance: Enable face enhancement
            save_to_dir: Directory to save images (optional)
            
        Returns:
            List of paths to saved images
        """
        inference_data = {
            "operation": "inference",
            "character_name": character_name,
            "prompt": prompt,
            "lora_weight": lora_weight,
            "test_dim": image_size,
            "batch_size": batch_size,
            "num_inference_steps": num_inference_steps,
            "face_enhance": face_enhance
        }
        
        print(f"🎨 Generating {batch_size} image(s) for character: {character_name}")
        print(f"📝 Prompt: {prompt}")
        
        # Generate images
        result = self._make_request("runsync", inference_data, timeout=300)
        
        if result.get('status') != 'completed':
            raise Exception(f"Image generation failed: {result.get('error', 'Unknown error')}")
        
        # Save images if directory specified
        saved_paths = []
        if save_to_dir:
            os.makedirs(save_to_dir, exist_ok=True)
            
            for i, image_data in enumerate(result.get('images', [])):
                filename = image_data.get('filename', f'{character_name}_{i+1}.jpg')
                output_path = os.path.join(save_to_dir, filename)
                self._save_base64_image(image_data['image_data'], output_path)
                saved_paths.append(output_path)
                print(f"💾 Saved: {output_path}")
        
        print(f"✅ Generated {len(result.get('images', []))} images successfully")
        return saved_paths if save_to_dir else result.get('images', [])
    
    def _poll_job_completion(self, job_id: str, max_wait_minutes: int = 60) -> dict:
        """Poll job status until completion"""
        status_url = f"{self.base_url}/status/{job_id}"
        max_attempts = max_wait_minutes * 2  # Check every 30 seconds
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(status_url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
                
                status = result.get('status')
                
                if status == 'COMPLETED':
                    print("✅ Training completed successfully!")
                    return result
                elif status == 'FAILED':
                    error = result.get('error', 'Training failed')
                    raise Exception(f"Training failed: {error}")
                elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                    elapsed_minutes = (attempt + 1) * 0.5
                    print(f"⏳ Training in progress... {elapsed_minutes:.1f} minutes elapsed")
                    # Use exponential backoff for polling
                    poll_interval = min(30 + attempt * 5, 120)  # 30s to 2min max
                    time.sleep(poll_interval)
                else:
                    print(f"🔄 Status: {status}")
                    time.sleep(30)

            except requests.RequestException as e:
                if attempt == max_attempts - 1:
                    raise Exception(f"Failed to check job status: {e}")
                # Exponential backoff on error
                error_wait = min(5 * (2 ** (attempt % 4)), 60)  # 5s to 60s max
                time.sleep(error_wait)
        
        raise Exception(f"Training timed out after {max_wait_minutes} minutes")

def main():
    """Example usage of the CharForgex client"""
    
    # Configuration - replace with your values
    ENDPOINT_ID = "your_endpoint_id_here"
    API_KEY = "your_api_key_here"
    
    if ENDPOINT_ID == "your_endpoint_id_here" or API_KEY == "your_api_key_here":
        print("❌ Please configure ENDPOINT_ID and API_KEY in the script")
        return
    
    # Initialize client
    client = CharForgexClient(ENDPOINT_ID, API_KEY)
    
    try:
        # Test connection
        print("🔍 Testing connection...")
        health = client.health_check()
        print(f"✅ Worker is healthy: {health.get('status')}")
        
        # List existing characters
        print("\n📋 Listing available characters...")
        characters = client.list_characters()
        print(f"Found {len(characters)} trained characters: {characters}")
        
        # Example: Train a character (uncomment to use)
        """
        print("\n🎓 Training example character...")
        training_result = client.train_character(
            character_name="test_character",
            image_path="path/to/your/reference_image.jpg",
            steps=400,  # Reduced for testing
            learning_rate=8e-4,
            rank_dim=8
        )
        print(f"Training result: {training_result}")
        """
        
        # Example: Generate images (uncomment and modify)
        """
        if characters:
            character_name = characters[0]  # Use first available character
            print(f"\n🎨 Generating images for character: {character_name}")
            
            images = client.generate_images(
                character_name=character_name,
                prompt=f"portrait of {character_name}, detailed face, high quality",
                batch_size=2,
                save_to_dir="./generated_images"
            )
            print(f"Generated {len(images)} images")
        """
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
