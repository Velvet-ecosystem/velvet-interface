# velvet_interface/scene_system/yaml_loader.py
"""
YAML-based scene definition loader.

Loads scene definitions from YAML files including backgrounds,
interaction regions, transitions, and metadata.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


class YAMLSceneLoader:
    """
    Load scene definitions from YAML files.
    
    Expected YAML format:
        name: "scene_name"
        base_resolution: [1280, 720]
        background: "path/to/background.png"
        regions:
          - name: "button_1"
            polygon: [[100, 100], [200, 100], [200, 200], [100, 200]]
            action: "navigate:next_scene"
            metadata:
              tooltip: "Click to continue"
        transitions:
          enter: "fade"
          exit: "slide_left"
        metadata:
          description: "Example scene"
    """
    
    def __init__(self):
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML not installed. Install with: pip install PyYAML")
    
    def load(self, yaml_path: str) -> Dict[str, Any]:
        """
        Load scene definition from YAML file.
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Scene definition dict
        """
        path = Path(yaml_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Scene YAML not found: {yaml_path}")
        
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError(f"Empty or invalid YAML: {yaml_path}")
        
        # Validate required fields
        self._validate(data)
        
        logger.info(f"Loaded scene: {data.get('name')} from {yaml_path}")
        
        return data
    
    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate scene definition has required fields."""
        required = ['name']
        
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate base_resolution format
        if 'base_resolution' in data:
            res = data['base_resolution']
            if not isinstance(res, (list, tuple)) or len(res) != 2:
                raise ValueError("base_resolution must be [width, height]")
        
        # Validate regions
        if 'regions' in data:
            if not isinstance(data['regions'], list):
                raise ValueError("regions must be a list")
            
            for i, region in enumerate(data['regions']):
                if 'polygon' not in region:
                    raise ValueError(f"Region {i} missing polygon")
                if 'action' not in region:
                    raise ValueError(f"Region {i} missing action")
    
    def load_multiple(self, directory: str) -> Dict[str, Dict[str, Any]]:
        """
        Load all YAML scene files from a directory.
        
        Args:
            directory: Path to directory containing YAML files
            
        Returns:
            Dict mapping scene names to scene definitions
        """
        path = Path(directory)
        
        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        scenes = {}
        
        for yaml_file in path.glob("*.yaml"):
            try:
                scene_data = self.load(str(yaml_file))
                scene_name = scene_data['name']
                scenes[scene_name] = scene_data
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
        
        logger.info(f"Loaded {len(scenes)} scenes from {directory}")
        
        return scenes
