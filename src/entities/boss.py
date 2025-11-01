"""
Boss Entity - Perfectionist Boss

Terraria Twins-inspired boss with FSM-based AI and phase transitions.
Uses configuration from globals.py.
"""

#region Imports

import pygame
import math
import random
import globals as g
#endregion Imports


#region State Base
class BossState:
    """Base class for boss states"""
    def __init__(self, boss):
        self.boss = boss
    
    def enter(self):
        """Called when entering this state"""
        pass
    
    def exit(self):
        """Called when exiting this state"""
        pass
    
    def update(self, dt: float, player, bullet_manager):
        """Update state logic"""
        pass
#endregion State Base


#region IdleState
class IdleState(BossState):
    """Boss idle state - positioning and preparation"""
    def __init__(self, boss):
        super().__init__(boss)
        self.idle_time = 0.0
        self.move_target_x = 0
        
    def enter(self):
        self.idle_time = 0.0
        # Choose a position to move to
        self.move_target_x = random.uniform(g.SCREENWIDTH * 0.3, g.SCREENWIDTH * 0.7)
    
    def update(self, dt: float, player, bullet_manager):
        self.idle_time += dt
        
        # Move towards target position
        dx = self.move_target_x - self.boss.x
        if abs(dx) > 5:
            move_dir = 1 if dx > 0 else -1
            self.boss.x += move_dir * g.BOSS_MOVE_SPEED * dt
        
        # Transition to attack after idle time
        cooldown = g.BOSS_ATTACK_COOLDOWN_PHASE1 if self.boss.phase == 1 else g.BOSS_ATTACK_COOLDOWN_PHASE2
        if self.idle_time >= cooldown:
            if self.boss.phase == 1:
                # Phase 1 attacks
                attack = random.choice(['spread_shot', 'predictive_shot'])
            else:
                # Phase 2 attacks (more aggressive)
                attack = random.choice(['spread_shot', 'predictive_shot', 'homing_barrage', 'laser_sweep'])
            
            self.boss.change_state(attack)
#endregion IdleState


#region SpreadShotState
class SpreadShotState(BossState):
    """Boss fires a spread of bullets"""
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph_time = 0.0
        self.has_fired = False
        
    def enter(self):
        self.telegraph_time = 0.0
        self.has_fired = False
        self.boss.telegraph_timer = g.BOSS_TELEGRAPH_DURATION
    
    def update(self, dt: float, player, bullet_manager):
        self.telegraph_time += dt
        
        if self.telegraph_time >= g.BOSS_TELEGRAPH_DURATION and not self.has_fired:
            self.has_fired = True
            
            # Fire spread shot
            num_bullets = 7 if self.boss.phase == 1 else 11
            spread_angle = math.pi / 3  # 60 degrees
            
            for i in range(num_bullets):
                angle = -spread_angle/2 + (i / (num_bullets-1)) * spread_angle
                
                # Aim towards player with some spread
                dx = (player.x + player.width/2) - (self.boss.x + self.boss.width/2)
                dy = (player.y + player.height/2) - (self.boss.y + self.boss.height/2)
                base_angle = math.atan2(dy, dx)
                
                final_angle = base_angle + angle
                speed = g.BULLET_SPEEDS['normal']
                
                vx = math.cos(final_angle) * speed
                vy = math.sin(final_angle) * speed
                
                bullet_manager.add_bullet(
                    self.boss.x + self.boss.width/2,
                    self.boss.y + self.boss.height/2,
                    vx, vy, 'normal', 'boss'
                )
            
            # Return to idle
            self.boss.change_state('idle')
#endregion SpreadShotState


#region PredictiveShotState
class PredictiveShotState(BossState):
    """Boss fires at where player will be"""
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph_time = 0.0
        self.has_fired = False
        
    def enter(self):
        self.telegraph_time = 0.0
        self.has_fired = False
        self.boss.telegraph_timer = g.BOSS_TELEGRAPH_DURATION
    
    def update(self, dt: float, player, bullet_manager):
        self.telegraph_time += dt
        
        if self.telegraph_time >= g.BOSS_TELEGRAPH_DURATION and not self.has_fired:
            self.has_fired = True
            
            # Predict player position
            prediction_time = 0.8
            predicted_x = player.x + player.vx * prediction_time
            predicted_y = player.y + player.vy * prediction_time
            
            # Fire multiple shots for phase 2
            num_shots = 1 if self.boss.phase == 1 else 3
            
            for i in range(num_shots):
                # Add some variance in phase 2
                if num_shots > 1:
                    offset_x = (i - 1) * 50  # Spread predictions
                    target_x = predicted_x + offset_x
                    target_y = predicted_y
                else:
                    target_x = predicted_x
                    target_y = predicted_y
                
                dx = target_x - (self.boss.x + self.boss.width/2)
                dy = target_y - (self.boss.y + self.boss.height/2)
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 0:
                    speed = g.BULLET_SPEEDS['normal']
                    vx = (dx / distance) * speed
                    vy = (dy / distance) * speed
                    
                    bullet_manager.add_bullet(
                        self.boss.x + self.boss.width/2,
                        self.boss.y + self.boss.height/2,
                        vx, vy, 'normal', 'boss'
                    )
            
            self.boss.change_state('idle')
#endregion PredictiveShotState


#region HomingBarrageState
class HomingBarrageState(BossState):
    """Boss fires homing missiles (Phase 2 only)"""
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph_time = 0.0
        self.missiles_fired = 0
        self.fire_timer = 0.0
        
    def enter(self):
        self.telegraph_time = 0.0
        self.missiles_fired = 0
        self.fire_timer = 0.0
        self.boss.telegraph_timer = g.BOSS_TELEGRAPH_DURATION
    
    def update(self, dt: float, player, bullet_manager):
        self.telegraph_time += dt
        
        if self.telegraph_time >= g.BOSS_TELEGRAPH_DURATION:
            self.fire_timer += dt
            
            # Fire missiles at intervals
            if self.fire_timer >= 0.3 and self.missiles_fired < 5:
                self.fire_timer = 0.0
                self.missiles_fired += 1
                
                # Fire homing missile
                speed = g.BULLET_SPEEDS['homing']
                # Aim roughly at player
                dx = (player.x + player.width/2) - (self.boss.x + self.boss.width/2)
                dy = (player.y + player.height/2) - (self.boss.y + self.boss.height/2)
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 0:
                    vx = (dx / distance) * speed
                    vy = (dy / distance) * speed
                    
                    bullet_manager.add_bullet(
                        self.boss.x + self.boss.width/2,
                        self.boss.y + self.boss.height/2,
                        vx, vy, 'homing', 'boss'
                    )
            
            # Return to idle after all missiles fired
            if self.missiles_fired >= 5:
                self.boss.change_state('idle')
#endregion HomingBarrageState


#region LaserSweepState
class LaserSweepState(BossState):
    """Boss fires sweeping laser (Phase 2 only)"""
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph_time = 0.0
        self.sweep_time = 0.0
        self.sweep_angle = 0.0
        
    def enter(self):
        self.telegraph_time = 0.0
        self.sweep_time = 0.0
        self.sweep_angle = -math.pi/4  # Start angle
        self.boss.telegraph_timer = g.BOSS_TELEGRAPH_DURATION
    
    def update(self, dt: float, player, bullet_manager):
        self.telegraph_time += dt
        
        if self.telegraph_time >= g.BOSS_TELEGRAPH_DURATION:
            self.sweep_time += dt
            
            # Sweep laser across screen
            if self.sweep_time <= 2.0:  # 2 second sweep
                # Fire laser bullets in current direction
                if int(self.sweep_time * 20) % 2 == 0:  # Fire every other frame
                    speed = g.BULLET_SPEEDS['laser']
                    vx = math.cos(self.sweep_angle) * speed
                    vy = math.sin(self.sweep_angle) * speed
                    
                    bullet_manager.add_bullet(
                        self.boss.x + self.boss.width/2,
                        self.boss.y + self.boss.height/2,
                        vx, vy, 'laser', 'boss'
                    )
                
                # Update sweep angle
                self.sweep_angle += (math.pi/2) * dt / 2.0  # 90 degrees over 2 seconds
            else:
                self.boss.change_state('idle')
#endregion LaserSweepState


#region Perfectionist Boss
class Perfectionist:
    """
    Terraria Twins-inspired boss with phase-based behavior
    """
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = 48
        self.height = 48
        
        # Health and phases
        self.max_health = g.BOSS_MAX_HEALTH
        self.health = self.max_health
        self.phase = 1
        
        # State machine
        self.states = {
            'idle': IdleState(self),
            'spread_shot': SpreadShotState(self),
            'predictive_shot': PredictiveShotState(self),
            'homing_barrage': HomingBarrageState(self),
            'laser_sweep': LaserSweepState(self)
        }
        self.current_state = self.states['idle']
        self.current_state.enter()
        
        # Visual effects
        self.telegraph_timer = 0.0
    
    def change_state(self, state_name: str):
        """Change boss state"""
        if state_name in self.states:
            self.current_state.exit()
            self.current_state = self.states[state_name]
            self.current_state.enter()
    
    def update(self, dt: float, player, bullet_manager):
        """Update boss logic"""
        # Update telegraph timer
        self.telegraph_timer = max(0, self.telegraph_timer - dt)
        
        # Check for phase transition
        if self.phase == 1 and self.health <= self.max_health * 0.5:
            self.phase = 2
            self.change_state('idle')  # Reset to idle for phase transition
        
        # Update current state
        self.current_state.update(dt, player, bullet_manager)
        
        # Keep boss in reasonable bounds
        self.x = max(50, min(g.SCREENWIDTH - self.width - 50, self.x))
        self.y = max(50, min(200, self.y))  # Keep boss in upper area
    
    def take_damage(self, damage: float):
        """Boss takes damage"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
    
    def draw(self, screen: pygame.Surface):
        """Draw the boss"""
        # Choose color based on state
        if self.telegraph_timer > 0:
            # Flashing telegraph effect
            if int(self.telegraph_timer * 8) % 2:
                color = g.COLORS['boss_telegraph']
            else:
                color = g.COLORS['boss']
        else:
            color = g.COLORS['boss']
        
        # Phase 2 visual indicator
        if self.phase == 2:
            # Darker, more menacing color
            color = tuple(max(0, c - 50) for c in color)
        
        pygame.draw.rect(screen, color, (int(self.x), int(self.y), self.width, self.height))
        
        # Draw collision box in debug mode
        if g.SHOW_COLLISION_BOXES:
            pygame.draw.rect(screen, (255, 0, 0), 
                           (int(self.x), int(self.y), self.width, self.height), 2)
        
        # Draw phase indicator
        font = pygame.font.Font(None, 24)
        phase_text = font.render(f"Phase {self.phase}", True, g.COLORS['ui_text'])
        screen.blit(phase_text, (self.x, self.y - 30))
#endregion Perfectionist Boss