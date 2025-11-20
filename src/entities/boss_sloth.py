"""Boss #2 - The Sloth

Ground‑crawling zoning boss that creates persistent slime hazards to force
the player to keep moving. Core mechanics:
    - Crawl State: slow horizontal patrol, leaves damaging slowing trail.
    - SlimeAttack State: lobs arcing slime globs that become pools.
    - Trail segments punish idling (higher DPS if player barely moves).
    - Phase 2: faster cooldowns, more globs per attack.
    - Fading State: defeat fade (future: particles / ripples).

Dialog integration: uses TextPopup for now (can be swapped to DialogBox later)."""

from __future__ import annotations
import math, random, os
import pygame
import globals as g
from .bullets import BulletManager
from ..systems.ui import TextPopup


class SlothState:
    def __init__(self, boss: 'TheSloth'): self.boss = boss
    def enter(self): pass
    def exit(self): pass
    def update(self, dt: float, player, bullet_manager: BulletManager): pass


class IntroState(SlothState):
    def enter(self):
        self.timer = 0.0
        self.duration = 2.2
        self.boss.say_once(self.boss.entry_line)
    def update(self, dt, player, bullet_manager):
        self.timer += dt
        if self.timer >= self.duration:
            self.boss.change_state('crawl')


class CrawlState(SlothState):
    """Grounded slow crawl. Leaves slime trail while moving.
    Player is pressured because trail damages & slows, punishing staying still."""
    def enter(self):
        self.pick_target()
        self.attack_cd = self._cooldown()
        self.say_timer = 0.0
        self.retarget_timer = 0.0  # how often we re-aim at player's x
        # Advanced pattern timers
        self.dash_cd = getattr(g, 'BOSS2_DASH_COOLDOWN', 6.5)
        self.spore_cd = getattr(g, 'BOSS2_SPORE_COOLDOWN', 7.5)
        self.eruption_t = getattr(g, 'BOSS2_ERUPTION_INTERVAL', 9.0)
    def _cooldown(self):
        return g.BOSS2_SLIME_COOLDOWN if self.boss.phase == 1 else g.BOSS2_SLIME_COOLDOWN_P2
    def pick_target(self):
        w = g.SCREENWIDTH
        # choose horizontally biased points; more frequent short moves in P2
        points = [w*0.15, w*0.33, w*0.5, w*0.67, w*0.85]
        self.target_x = random.choice(points)
    def update(self, dt, player, bullet_manager):
        # Phase transition
        if self.boss.phase == 1 and self.boss.health <= self.boss.max_health * g.BOSS2_PHASE2_HP_RATIO:
            self.boss.phase = 2
        # Enrage check
        if not getattr(self.boss, 'enraged', False) and self.boss.health <= self.boss.max_health * getattr(g, 'BOSS2_ENRAGE_HP_RATIO', 0.35):
            self.boss.enraged = True
            # shorten timers immediately
            self.dash_cd *= 0.5
            self.spore_cd *= 0.6
            self.attack_cd *= 0.6
        # Horizontal ground movement
        speed = g.BOSS2_MOVE_SPEED * (1.2 if self.boss.phase==2 else 1.0)
        if getattr(self.boss, 'enraged', False):
            speed *= 1.25
        center_x = self.boss.x + self.boss.width/2
        # Periodically retarget towards player's current x (seeking behavior)
        self.retarget_timer -= dt
        if self.retarget_timer <= 0:
            px = player.x + player.width/2
            # Apply a small lead when player is moving
            px += (player.vx * 0.25)
            # Keep inside screen padding
            px = max(60, min(g.SCREENWIDTH-60, px))
            self.target_x = px
            self.retarget_timer = 0.5 if self.boss.phase==1 else 0.35
        dx = self.target_x - center_x
        if abs(dx) < 10:
            self.pick_target()
        else:
            step = max(-1, min(1, dx)) * speed * dt
            self.boss.x += step
            self.boss._maybe_drop_trail(center_x, dt)
        # Attack timer
        self.attack_cd -= dt
        if self.attack_cd <= 0:
            self.boss.change_state('slime_attack')
            return
        # Advanced timers (skip if about to fade)
        if self.boss.health > 0:
            self.dash_cd -= dt
            self.spore_cd -= dt
            self.eruption_t -= dt
            # Priority order: dash -> spore -> eruption
            if self.dash_cd <= 0:
                # reset cooldown (phase/enrage scaling)
                base = getattr(g, 'BOSS2_DASH_COOLDOWN_P2', 5.5) if self.boss.phase==2 else getattr(g, 'BOSS2_DASH_COOLDOWN', 6.5)
                if getattr(self.boss, 'enraged', False): base *= 0.6
                self.dash_cd = base
                self.boss.change_state('dash')
                return
            if self.spore_cd <= 0:
                base = getattr(g, 'BOSS2_SPORE_COOLDOWN', 7.5)
                if self.boss.phase==2: base *= 0.85
                if getattr(self.boss, 'enraged', False): base *= 0.6
                self.spore_cd = base
                self.boss.change_state('spore_attack')
                return
            if self.eruption_t <= 0:
                base = getattr(g, 'BOSS2_ERUPTION_INTERVAL', 9.0)
                if self.boss.phase==2: base *= 0.85
                if getattr(self.boss, 'enraged', False): base *= 0.7
                self.eruption_t = base
                self.boss.change_state('eruption')
                return
        # Dialog timer
        self.say_timer += dt
        interval = 6.0 if self.boss.phase==1 else 4.5
        if self.say_timer >= interval:
            self.say_timer = 0
            self.boss.say_random_mid()


class SlimeAttackState(SlothState):
    """Telegraphs briefly then emits a fan of slime globs.
    Phase 2 throws more globs with slightly wider spread."""
    def enter(self):
        self.telegraph = 0.9
        self.fired = False
    def update(self, dt, player, bullet_manager):
        self.telegraph -= dt
        if self.telegraph <= 0 and not self.fired:
            self.fired = True
            self._fire(player, bullet_manager)
            self.boss.change_state('crawl')
    def _fire(self, player, bullet_manager):
        origin_x = self.boss.x + self.boss.width/2
        origin_y = self.boss.y + self.boss.height*0.25
        # Use tuned volley counts; enraged increases further
        if getattr(self.boss, 'enraged', False):
            n = getattr(g, 'BOSS2_SLIME_VOLLEY_ENRAGE', 12)
        else:
            n = getattr(g, 'BOSS2_SLIME_VOLLEY_P2', 9) if self.boss.phase==2 else getattr(g, 'BOSS2_SLIME_VOLLEY_P1', 6)
        spread = getattr(g, 'BOSS2_SLIME_SPREAD_P2', 1.05) if self.boss.phase==2 else getattr(g, 'BOSS2_SLIME_SPREAD_P1', 0.85)
        for i in range(n):
            ratio = (i/(n-1)) if n>1 else 0.5
            offset = -spread/2 + spread * ratio
            base_speed = getattr(g, 'BOSS2_SLIME_BASE_SPEED_P1', 190) if self.boss.phase==1 else getattr(g, 'BOSS2_SLIME_BASE_SPEED_P2', 210)
            if getattr(self.boss, 'enraged', False):
                base_speed *= getattr(g, 'BOSS2_SLIME_ENRAGE_SPEED_MULT', 1.08)
            jitter_low = getattr(g, 'BOSS2_SLIME_SPEED_JITTER_LOW', -24)
            jitter_high = getattr(g, 'BOSS2_SLIME_SPEED_JITTER_HIGH', 36)
            speed = base_speed + random.uniform(jitter_low, jitter_high)
            ang = getattr(g, 'BOSS2_SLIME_BASE_ANGLE', -1.05) + offset
            vx = math.cos(ang)*speed
            vy = math.sin(ang)*speed
            bullet_manager.add_bullet(origin_x, origin_y, vx, vy, 'slime', 'boss')


class DashState(SlothState):
    def enter(self):
        self.timer = 0.0
        self.duration = getattr(g, 'BOSS2_DASH_DURATION', 0.9)
        # Determine direction toward player at enter
        self.dash_speed = getattr(g, 'BOSS2_DASH_SPEED', 250)
        self.hit = False
    def update(self, dt, player, bullet_manager):
        self.timer += dt
        # Move horizontally toward player center
        center_x = self.boss.x + self.boss.width/2
        target_x = player.x + player.width/2
        dir = 1 if target_x > center_x else -1
        dash_speed = self.dash_speed * (getattr(g, 'BOSS2_DASH_ENRAGE_SPEED_MULT', 1.25) if getattr(self.boss, 'enraged', False) else 1.0)
        self.boss.x += dir * dash_speed * dt
        # Drop trail faster due to rapid movement
        self.boss._maybe_drop_trail(self.boss.x + self.boss.width/2, dt)
        # Contact damage once
        if not self.hit:
            brect = pygame.Rect(self.boss.x, self.boss.y, self.boss.width, self.boss.height)
            prect = pygame.Rect(player.x, player.y, player.width, player.height)
            if brect.colliderect(prect):
                dmg = getattr(g, 'BOSS2_ERUPTION_BURST_DAMAGE', 22) * 0.5
                player.take_damage(dmg)
                self.hit = True
        if self.timer >= self.duration:
            self.boss.change_state('crawl')


class SporeAttackState(SlothState):
    def enter(self):
        self.telegraph = 0.7
        self.fired = False
    def update(self, dt, player, bullet_manager):
        self.telegraph -= dt
        if self.telegraph <= 0 and not self.fired:
            self.fired = True
            self._fire(player, bullet_manager)
            self.boss.change_state('crawl')
    def _fire(self, player, bullet_manager):
        origin_x = self.boss.x + self.boss.width/2
        origin_y = self.boss.y + self.boss.height*0.25
        # count varies by phase & enrage
        if getattr(self.boss, 'enraged', False):
            n = getattr(g, 'BOSS2_SPORE_COUNT_ENRAGE', 7)
        else:
            n = getattr(g, 'BOSS2_SPORE_COUNT_P2', 5) if self.boss.phase==2 else getattr(g, 'BOSS2_SPORE_COUNT_P1', 3)
        spread = getattr(g, 'BOSS2_SPORE_SPREAD_ENRAGE', 80) if getattr(self.boss, 'enraged', False) else getattr(g, 'BOSS2_SPORE_SPREAD_P1', 60)
        vy_min = getattr(g, 'BOSS2_SPORE_VY_MIN', -55)
        vy_max = getattr(g, 'BOSS2_SPORE_VY_MAX', -35)
        for i in range(n):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(vy_min, vy_max)
            bullet_manager.add_bullet(origin_x, origin_y, vx, vy, 'slime_spore', 'boss')


class EruptionState(SlothState):
    def enter(self):
        # Immediate effect then return; collect segments for burst damage
        self.done = False
    def update(self, dt, player, bullet_manager):
        if self.done:
            self.boss.change_state('crawl')
            return
        prect = pygame.Rect(player.x, player.y, player.width, player.height)
        # Choose recent segments (last 6) for burst
        segs = self.boss.trail_segments[-6:]
        burst_dmg = getattr(g, 'BOSS2_ERUPTION_BURST_DAMAGE', 28)
        for seg in segs:
            # visual flash handled in draw via age manipulation (optional: reduce age to keep alive)
            if prect.colliderect(seg['rect']):
                player.take_damage(burst_dmg)
            # accelerate aging so they vanish sooner post-eruption
            seg['age'] += getattr(g, 'BOSS2_ERUPTION_TRAIL_AGE_ADD', 0.6)
        self.done = True


class FadingState(SlothState):
    def enter(self):
        self.timer = 0.0
        self.duration = 2.5
        self.boss.say_once(self.boss.defeat_line)
    def update(self, dt, player, bullet_manager):
        self.timer += dt
        if self.timer >= self.duration:
            self.boss.fully_defeated = True


class TheSloth:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = g.BOSS2_BODY_W
        self.height = g.BOSS2_BODY_H
        self.max_health = g.BOSS2_MAX_HEALTH
        self.health = self.max_health
        self.phase = 1
        # Dialogue lines
        self.entry_line = "You stole your own time. You stopped moving forward."
        self.mid_lines = [
            "Rest... a little longer.",
            "Motion is pointless.",
            "Stay. Let the trail swallow you.",
            "Time slows. You fade."
        ]
        self.defeat_line = "Walk first, then think."  # victory popup for player
        self.dialog_cooldown = 0.0
        self.fully_defeated = False
        # Animation
        self.anim_timer = 0.0
        self.anim_frame = 0
        self.state_name = 'intro'
        self.states = {
            'intro': IntroState(self),
            'crawl': CrawlState(self),
            'slime_attack': SlimeAttackState(self),
            'dash': DashState(self),
            'spore_attack': SporeAttackState(self),
            'eruption': EruptionState(self),
            'fading': FadingState(self)
        }
        self.current_state = self.states['intro']
        self.current_state.enter()
        # Load sprites (placeholder safe) — lazy slice
        self.walk_frames = self._load_sheet(g.BOSS2_SPRITE_WALK_PATH, g.BOSS2_WALK_FRAME_COUNT)
        self.attack_frames = self._load_sheet(g.BOSS2_SPRITE_ATTACK_PATH, g.BOSS2_ATTACK_FRAME_COUNT)
        self.fade_frames = self._load_sheet(g.BOSS2_SPRITE_FADE_PATH, g.BOSS2_FADE_FRAME_COUNT)
        # Ground movement context
        self.ground_y = None  # set by scene (top of ground platform) or computed fallback
        # Slime trail system
        self.trail_segments = []  # list of dict {rect, age}
        self._trail_last_x = self.x
        self.enraged = False

    # Dialogue helpers
    def say_once(self, text: str):
        if not text: return
        def anchor(): return (self.x + self.width/2, self.y)
        from ..systems.ui import UIManager  # local to avoid cycles
        if hasattr(self, 'ui') and self.ui:
            self.ui.add(TextPopup(text, anchor, duration=3.0, bg=(15,15,15)))

    def say_random_mid(self):
        if not self.mid_lines: return
        line = random.choice(self.mid_lines)
        def anchor(): return (self.x + self.width/2, self.y)
        if hasattr(self, 'ui') and self.ui:
            self.ui.add(TextPopup(line, anchor, duration=3.0, bg=(15,15,15)))

    # FSM
    def change_state(self, name: str):
        if name in self.states:
            self.current_state.exit()
            self.state_name = name
            self.current_state = self.states[name]
            self.current_state.enter()

    # Loading & Animation
    def _load_sheet(self, path: str, count: int):
        frames = []
        if not path or not os.path.exists(path):
            return frames
        try:
            sheet = pygame.image.load(path).convert_alpha()
            fw = g.BOSS2_FRAME_W
            fh = g.BOSS2_FRAME_H
            for i in range(count):
                sub = pygame.Surface((fw, fh), pygame.SRCALPHA)
                sub.blit(sheet, (0,0), area=pygame.Rect(i*fw,0,fw,fh))
                frames.append(sub)
        except Exception:
            return []
        return frames

    def update(self, dt: float, player, bullet_manager: BulletManager):
        if self.health <= 0 and self.state_name != 'fading':
            self.change_state('fading')
        self.current_state.update(dt, player, bullet_manager)
        # basic anim step
        self.anim_timer += dt
        fps = g.BOSS2_WALK_ANIM_FPS
        if self.state_name == 'slime_attack':
            fps = g.BOSS2_ATTACK_ANIM_FPS
        elif self.state_name == 'fading':
            fps = g.BOSS2_FADE_ANIM_FPS
        if fps>0 and self.anim_timer >= 1.0/fps:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % max(1, self._frame_count())
        # Ensure y locked to ground when not fading (fading keeps position)
        if self.state_name != 'fading':
            self._enforce_ground()
        # Trail hazard update & player interaction
        self._update_trail(dt, player)

    def _frame_count(self):
        if self.state_name == 'slime_attack' and self.attack_frames: return len(self.attack_frames)
        if self.state_name == 'fading' and self.fade_frames: return len(self.fade_frames)
        return len(self.walk_frames)

    def take_damage(self, dmg: float):
        if self.health <=0: return
        self.health -= dmg
        if self.health < 0: self.health = 0

    def draw(self, screen: pygame.Surface):
        # pick frame set
        frames = self.walk_frames
        if self.state_name == 'slime_attack' and self.attack_frames:
            frames = self.attack_frames
        elif self.state_name == 'fading' and self.fade_frames:
            frames = self.fade_frames
        frame = None
        if frames:
            frame = frames[self.anim_frame % len(frames)]
        if frame is None:
            # fallback rectangle
            color = (150,150,150) if self.state_name!='fading' else (200,200,200)
            pygame.draw.rect(screen, color, (int(self.x), int(self.y), self.width, self.height), border_radius=12)
        else:
            screen.blit(frame, (int(self.x), int(self.y)))
        # simple fade overlay during fading
        if self.state_name == 'fading':
            prog = min(1.0, getattr(self.states['fading'], 'timer', 0.0)/ max(0.01, getattr(self.states['fading'], 'duration',1)))
            if frame:
                overlay = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                overlay.fill((255,255,255,int(120*prog)))
                screen.blit(overlay,(int(self.x), int(self.y)))
        # Draw slime trail segments (beneath boss, after to avoid covering player)
        for seg in self.trail_segments:
            r = seg['rect']
            age = seg['age']
            fade = 1.0 - (age / g.BOSS2_SLIME_TRAIL_LIFETIME)
            alpha = int(170 * max(0.05, fade))
            surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            col = (70, 150, 90, alpha)
            pygame.draw.rect(surf, col, (0,0,r.width,r.height), border_radius=6)
            inner = pygame.Rect(4,4,r.width-8,r.height-8)
            pygame.draw.rect(surf, (90,180,110,int(alpha*0.6)), inner, border_radius=4)
            screen.blit(surf, (r.x, r.y))

    # --- Ground & Trail helpers ---
    def set_ground(self, ground_top: float):
        self.ground_y = ground_top - self.height
        # snap immediately
        self.y = self.ground_y

    def _enforce_ground(self):
        if self.ground_y is None:
            # fallback guess: screen bottom - 70 (same as BossBattleScene ground)
            self.ground_y = g.SCREENHEIGHT - 70 - self.height
        self.y = self.ground_y

    def _maybe_drop_trail(self, center_x: float, dt: float):
        if abs(center_x - self._trail_last_x) >= g.BOSS2_SLIME_TRAIL_DROP_DIST:
            self._trail_last_x = center_x
            seg_w = g.BOSS2_SLIME_TRAIL_SEG_W
            seg_h = g.BOSS2_SLIME_TRAIL_SEG_H
            rx = int(center_x - seg_w/2)
            ry = int(self.y + self.height - seg_h + 6)  # slightly embedded
            rect = pygame.Rect(rx, ry, seg_w, seg_h)
            self.trail_segments.append({'rect': rect, 'age': 0.0})

    def _update_trail(self, dt: float, player):
        if not self.trail_segments:
            return
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        new_list = []
        for seg in self.trail_segments:
            seg['age'] += dt
            if seg['age'] <= g.BOSS2_SLIME_TRAIL_LIFETIME:
                # collision check
                if player_rect.colliderect(seg['rect']) and self.state_name != 'fading':
                    moving = abs(player.vx) > 25
                    dps = g.BOSS2_SLIME_TRAIL_DPS * (1.0 if moving else g.BOSS2_SLIME_TRAIL_IDLE_MULT)
                    if getattr(self, 'enraged', False):
                        dps *= getattr(g, 'BOSS2_TRAIL_ENRAGE_DPS_MULT', 1.3)
                    player.take_damage(dps * dt)
                    # apply slow only while inside
                    player.vx *= g.BOSS2_SLIME_TRAIL_SLOW
                new_list.append(seg)
        self.trail_segments = new_list
