"""
State Machine - Simple state management system

This module provides a basic state machine for managing game states/scenes.
"""

class StateMachine:
    """
    Simple state machine for managing game states.
    """
    
    def __init__(self):
        self.current_state = None
        self.previous_state = None
    
    def change_state(self, new_state):
        """
        Change to a new state.
        
        Args:
            new_state: The new state object to switch to
        """
        if self.current_state:
            self.current_state.exit()
        
        self.previous_state = self.current_state
        self.current_state = new_state
        
        if self.current_state:
            self.current_state.enter()
    
    def revert_state(self):
        """
        Revert to the previous state.
        """
        if self.previous_state:
            self.change_state(self.previous_state)