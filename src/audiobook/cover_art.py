"""
Cover Art Generation for Audiobooks

Uses Stable Diffusion XL (via diffusers) for AI cover art generation.
Includes trade dress avoidance via negative prompts from production kits.
Optimized for RTX 5080 (16GB VRAM).
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CoverArtConfig:
    """Configuration for cover art generation."""
    prompt: str
    negative_prompt: str = ""
    width: int = 1024
    height: int = 1536  # Book cover ratio ~2:3
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    num_variations: int = 4


# Trade dress avoidance negative prompts from production kits
TRADE_DRESS_NEGATIVES: Dict[str, str] = {
    "maltese_falcon": (
        "film noir lighting, 1940s aesthetic, fedora shadows, "
        "Humphrey Bogart style, Warner Bros movie poster style, "
        "black and white photography, movie still, film scene"
    ),
    "strong_poison": (
        "yellow book spine, Hodder Stoughton style, "
        "TV adaptation imagery, Ian Carmichael, "
        "Edward Petherbridge"
    ),
    "last_and_first_men": "",  # No significant trade dress concerns
}

BASE_NEGATIVE = (
    "low quality, blurry, text, watermark, logo, "
    "photograph, photorealistic face, celebrity likeness, "
    "nsfw, ugly, deformed, noisy, grainy"
)

# Cover art prompts from production kits
BOOK_COVER_PROMPTS: Dict[str, str] = {
    "last_and_first_men": (
        "Elegant book cover for 'Last and First Men' by Olaf Stapledon. "
        "Cosmic philosophical science fiction aesthetic. Central imagery: "
        "spiral of human evolution against starfield background, suggesting "
        "vast time scales. Subtle human silhouettes transforming across deep "
        "space. Color palette: deep cosmic blue, purple nebula, golden stars. "
        "Typography: elegant, modernist, NOT pulp sci-fi style. "
        "Contemplative and grand in scale. No specific human faces."
    ),
    "maltese_falcon": (
        "Elegant book cover for 'The Maltese Falcon' by Dashiell Hammett. "
        "Art deco style, 1920s San Francisco. A dark stylized falcon statue "
        "as central element. Moody city skyline in background. "
        "Color palette: deep blacks, rich golds, dark reds. "
        "Typography: bold art deco. Classic hardboiled detective aesthetic. "
        "NOT film noir, NOT movie imagery. Based on the 1930 novel."
    ),
    "strong_poison": (
        "Elegant book cover for 'Strong Poison' by Dorothy L. Sayers. "
        "1930s London mystery aesthetic. Stylized poison bottle or arsenic "
        "imagery. Art deco framing with courtroom drama undertones. "
        "Color palette: deep greens, golds, cream. "
        "Typography: elegant 1930s style. British golden age mystery. "
        "NOT cozy mystery style, sophisticated and literary."
    ),
}


class CoverArtGenerator:
    """
    Generate cover art using Stable Diffusion XL.

    Handles model loading, generation with trade dress avoidance,
    and multi-variation output.
    """

    def __init__(
        self,
        model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
        device: str = "auto",
    ) -> None:
        """
        Args:
            model_id: HuggingFace model ID for SDXL
            device: 'cuda', 'cpu', or 'auto'
        """
        self.model_id = model_id
        self.device = device
        self._pipe = None
        self._loaded = False

    def load_model(self) -> None:
        """Load Stable Diffusion model to GPU."""
        if self._loaded:
            return

        try:
            import torch
            from diffusers import StableDiffusionXLPipeline
        except ImportError:
            raise ImportError(
                "diffusers not installed. Run:\n"
                "pip install diffusers transformers accelerate\n"
                "pip install torch torchvision --index-url "
                "https://download.pytorch.org/whl/cu121"
            )

        device = self.device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Loading SDXL model on {device}")

        self._pipe = StableDiffusionXLPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            use_safetensors=True,
            variant="fp16" if device == "cuda" else None,
        )
        self._pipe = self._pipe.to(device)

        # Enable memory optimizations for 16GB VRAM
        if device == "cuda":
            self._pipe.enable_vae_slicing()
            self._pipe.enable_vae_tiling()

        self._loaded = True
        logger.info("SDXL model loaded")

    def unload_model(self) -> None:
        """Unload model to free VRAM."""
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            self._loaded = False

            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            logger.info("SDXL model unloaded")

    def generate_cover(
        self,
        config: CoverArtConfig,
        output_path: Path,
    ) -> Path:
        """
        Generate a single cover art image.

        Args:
            config: Cover art configuration
            output_path: Output image path

        Returns:
            Path to generated image
        """
        self.load_model()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import torch

        generator = None
        if config.seed is not None:
            generator = torch.Generator(device=self._pipe.device).manual_seed(
                config.seed
            )

        logger.info(
            f"Generating cover: {config.width}x{config.height}, "
            f"{config.num_inference_steps} steps"
        )

        image = self._pipe(
            prompt=config.prompt,
            negative_prompt=f"{BASE_NEGATIVE}, {config.negative_prompt}",
            width=config.width,
            height=config.height,
            num_inference_steps=config.num_inference_steps,
            guidance_scale=config.guidance_scale,
            generator=generator,
        ).images[0]

        image.save(str(output_path))
        logger.info(f"Cover saved: {output_path}")
        return output_path

    def generate_book_covers(
        self,
        book_id: str,
        output_dir: Path,
        num_variations: int = 4,
        custom_prompt: Optional[str] = None,
    ) -> List[Path]:
        """
        Generate multiple cover variations for a book.

        Args:
            book_id: Book identifier
            output_dir: Output directory
            num_variations: Number of variations to generate
            custom_prompt: Optional custom prompt override

        Returns:
            List of generated image paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        prompt = custom_prompt or BOOK_COVER_PROMPTS.get(book_id, "")
        if not prompt:
            raise ValueError(
                f"No cover prompt for '{book_id}'. "
                f"Available: {list(BOOK_COVER_PROMPTS.keys())}"
            )

        negative = TRADE_DRESS_NEGATIVES.get(book_id, "")

        generated = []
        for i in range(num_variations):
            config = CoverArtConfig(
                prompt=prompt,
                negative_prompt=negative,
                seed=42 + i,  # Deterministic but different variations
            )

            output_path = output_dir / f"cover_v{i + 1}.png"
            self.generate_cover(config, output_path)
            generated.append(output_path)

            logger.info(f"  Variation {i + 1}/{num_variations} complete")

        return generated

    def generate_cover_upscaled(
        self,
        config: CoverArtConfig,
        output_path: Path,
        final_width: int = 3000,
        final_height: int = 4500,
    ) -> Path:
        """
        Generate and upscale cover to print resolution.

        Generates at SDXL native res then upscales with PIL.

        Args:
            config: Cover config
            output_path: Output path
            final_width: Final width in pixels
            final_height: Final height in pixels

        Returns:
            Path to upscaled image
        """
        # Generate at native resolution
        temp_path = output_path.parent / f".temp_{output_path.name}"
        self.generate_cover(config, temp_path)

        # Upscale with Lanczos resampling
        try:
            from PIL import Image
            img = Image.open(str(temp_path))
            img_upscaled = img.resize(
                (final_width, final_height),
                Image.LANCZOS,
            )
            img_upscaled.save(str(output_path), quality=95)
            logger.info(
                f"Upscaled to {final_width}x{final_height}: {output_path}"
            )
        except ImportError:
            logger.warning("PIL not available, keeping native resolution")
            temp_path.rename(output_path)
            return output_path
        finally:
            temp_path.unlink(missing_ok=True)

        return output_path
