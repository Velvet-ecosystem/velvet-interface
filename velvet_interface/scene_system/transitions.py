# velvet_interface/scene_system/transitions.py
"""
Scene transition effects.

Built-in transitions: fade, slide_left, slide_right, none.
"""

from typing import Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """Supported transition types."""
    NONE = "none"
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"


class Transition:
    """
    Scene transition configuration.
    
    Defines how to transition from one scene to another.
    """
    
    def __init__(
        self,
        transition_type: TransitionType = TransitionType.NONE,
        duration_ms: int = 300,
        on_complete: Optional[Callable] = None
    ):
        """
        Initialize transition.
        
        Args:
            transition_type: Type of transition
            duration_ms: Transition duration in milliseconds
            on_complete: Optional callback when transition completes
        """
        self.transition_type = transition_type
        self.duration_ms = duration_ms
        self.on_complete = on_complete
    
    @classmethod
    def from_string(cls, transition_str: str) -> 'Transition':
        """
        Create transition from string name.
        
        Args:
            transition_str: Transition name (e.g., "fade", "slide_left")
            
        Returns:
            Transition instance
        """
        try:
            transition_type = TransitionType(transition_str.lower())
        except ValueError:
            logger.warning(f"Unknown transition: {transition_str}, using 'none'")
            transition_type = TransitionType.NONE
        
        return cls(transition_type)


class TransitionManager:
    """
    Manage scene transitions.
    
    Surface implementations can use this to coordinate transitions.
    """
    
    def __init__(self):
        self.current_transition: Optional[Transition] = None
        self.is_transitioning = False
    
    def start_transition(
        self,
        transition: Transition,
        from_scene: Optional[str] = None,
        to_scene: Optional[str] = None
    ) -> None:
        """
        Start a scene transition.
        
        Args:
            transition: Transition to perform
            from_scene: Source scene name
            to_scene: Destination scene name
        """
        if self.is_transitioning:
            logger.warning("Transition already in progress")
            return
        
        self.current_transition = transition
        self.is_transitioning = True
        
        logger.info(
            f"Starting transition: {transition.transition_type.value} "
            f"({from_scene} -> {to_scene})"
        )
    
    def end_transition(self) -> None:
        """Mark transition as complete."""
        if not self.is_transitioning:
            return
        
        logger.info(f"Transition complete: {self.current_transition.transition_type.value}")
        
        if self.current_transition and self.current_transition.on_complete:
            self.current_transition.on_complete()
        
        self.current_transition = None
        self.is_transitioning = False
    
    def get_transition_config(
        self,
        scene_data: dict,
        transition_key: str = "enter"
    ) -> Transition:
        """
        Get transition config from scene data.
        
        Args:
            scene_data: Scene definition dict
            transition_key: "enter" or "exit"
            
        Returns:
            Transition instance
        """
        transitions = scene_data.get('transitions', {})
        transition_str = transitions.get(transition_key, 'none')
        
        return Transition.from_string(transition_str)
