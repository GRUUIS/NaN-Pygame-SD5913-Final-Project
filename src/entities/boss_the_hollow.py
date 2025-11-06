"""
The Hollow - Boss #3 (Nihilism)

A black humanoid silhouette that embodies emptiness. Keeps the core math-driven
behaviors of the Procrastinator boss but re-themed. It can summon "Void Shards"
(black small squares) that fall from above and damage the player on touch.

Entry line: "You think words can scare me away?"
Defeat line (displayed for the player): "This is not a threat-it's my process"
"""
#region Imports
import math
import random
import pygame
import globals as g

from .bullets import BulletManager
#endregion Imports


#region State Base
class BossState:
    def __init__(self, boss):
        self.boss = boss

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self, dt, player, bullet_manager):
        pass
#endregion State Base


#region DriftState
class DriftState(BossState):
    """Lissajous drift and state selection based on stress and deadline."""
    def __init__(self, boss):
        super().__init__(boss)
        self.timer = 0.0
        self.t = 0.0
        self.omega = 1.1
        self.phi = 0.9
        self.Ax = 160
        self.Ay = 60
        self.cx = boss.x
        self.cy = 140
        self.blend_time = getattr(g, 'BOSS3_DRIFT_BLEND_TIME', 0.25)
        self.blend_elapsed = 0.0
        self.start_x = boss.x
        self.start_y = boss.y

    def enter(self):
        self.timer = 0.0
        self.t = random.uniform(0.0, 0.6)
        self.omega = 1.0 + random.uniform(-0.15, 0.2)
        self.phi = random.uniform(0.6, 1.4)
        self.Ax = 140 + random.uniform(-30, 40)
        self.Ay = 50 + random.uniform(-10, 15)
        self.cx = self.boss.x
        self.cy = self.boss.y
        self.blend_time = getattr(g, 'BOSS3_DRIFT_BLEND_TIME', 0.25)
        self.blend_elapsed = 0.0
        self.start_x = self.boss.x
        self.start_y = self.boss.y

    def update(self, dt, player, bullet_manager):
        self.timer += dt
        self.t += dt

        s = self.boss.stress / max(1.0, self.boss.max_stress)
        r = self.boss.deadline_ratio()
        phase_norm = (self.boss.phase - 1) / 2.0
        a_min = getattr(g, 'BOSS3_APPROACH_MIN', 0.05)
        a_max = getattr(g, 'BOSS3_APPROACH_MAX', 0.92)
        a_base = getattr(g, 'BOSS3_APPROACH_BASE', 0.22)
        a_phase = getattr(g, 'BOSS3_APPROACH_PHASE', 0.38)
        a_dead = getattr(g, 'BOSS3_APPROACH_DEADLINE', 0.38)
        a_stress = getattr(g, 'BOSS3_APPROACH_STRESS', 0.18)
        approach = max(a_min, min(a_max, a_base + a_phase * phase_norm + a_dead * (1.0 - r) + a_stress * s))

        pcx = player.x + player.width / 2
        pcy = player.y + player.height / 2
        base_cx = g.SCREENWIDTH * 0.5
        base_cy = getattr(g, 'BOSS3_BASE_CY', 120.0)
        desired_cx = base_cx * (1.0 - approach) + pcx * approach
        desired_cy = base_cy * (1.0 - approach) + (pcy - 80) * approach
        chase_rate = getattr(g, 'BOSS3_CHASE_RATE', 3.0)
        self.cx += (desired_cx - self.cx) * min(1.0, chase_rate * dt)
        self.cy += (desired_cy - self.cy) * min(1.0, chase_rate * dt)

        shrink = getattr(g, 'BOSS3_AMPLITUDE_SHRINK', 0.52)
        Ax_eff = self.Ax * (1.0 - shrink * approach)
        Ay_eff = self.Ay * (1.0 - shrink * approach)

        x_lis = self.cx + Ax_eff * math.sin(self.omega * self.t)
        y_lis = self.cy + Ay_eff * math.sin(2 * self.omega * self.t + self.phi)

        if self.blend_elapsed < self.blend_time:
            self.blend_elapsed += dt
            a = min(1.0, self.blend_elapsed / self.blend_time)
            x_try = self.start_x * (1 - a) + x_lis * a
            y_try = self.start_y * (1 - a) + y_lis * a
        else:
            x_try = x_lis
            y_try = y_lis

        if getattr(self.boss, 'drop_impulse', 0.0) > 0.0:
            y_try += self.boss.drop_impulse * 0.5 * dt
            decay = getattr(g, 'BOSS3_DROP_DECAY', 220.0)
            self.boss.drop_impulse = max(0.0, self.boss.drop_impulse - decay * dt)

        pcx = player.x + player.width / 2
        pcy = player.y + player.height / 2
        dx = x_try - pcx
        dy = y_try - pcy
        dist = math.hypot(dx, dy)
        min_sep = (
            getattr(g, 'BOSS3_MIN_SEP_BASE', 260.0)
            - getattr(g, 'BOSS3_MIN_SEP_PHASE', 160.0) * phase_norm
            - getattr(g, 'BOSS3_MIN_SEP_DEADLINE', 140.0) * (1.0 - r)
            - getattr(g, 'BOSS3_MIN_SEP_STRESS', 80.0) * s
        )
        min_sep = max(getattr(g, 'BOSS3_MIN_SEP_MIN', 80.0), min(getattr(g, 'BOSS3_MIN_SEP_MAX', 260.0), min_sep))
        if dist < min_sep and dist > 1e-3:
            scale = min_sep / dist
            x_try = pcx + dx * scale
            y_try = pcy + dy * scale

        y_max_dyn = (
            getattr(g, 'BOSS3_Y_MAX_BASE', 220.0)
            + getattr(g, 'BOSS3_Y_MAX_DEADLINE_ADD', 160.0) * (1.0 - r)
            + getattr(g, 'BOSS3_Y_MAX_PHASE_ADD', 60.0) * phase_norm
        )
        y_max_dyn = min(y_max_dyn, g.SCREENHEIGHT - getattr(g, 'BOSS3_Y_MAX_MARGIN', 100.0))
        self.boss.x = max(40, min(g.SCREENWIDTH - self.boss.width - 40, x_try))
        self.boss.y = max(40, min(y_max_dyn, y_try))

        cooldown = self.boss.get_current_cooldown()
        if self.timer >= cooldown:
            s = self.boss.stress / max(1.0, self.boss.max_stress)
            r = self.boss.deadline_ratio()
            weights = [
                ("distraction_field", getattr(g, 'BOSS3_WEIGHT_DISTRACTION_BASE', 0.9) + getattr(g, 'BOSS3_WEIGHT_DISTRACTION_STRESS', 0.6) * s),
                ("predictive_barrage", getattr(g, 'BOSS3_WEIGHT_PREDICTIVE_BASE', 0.6) + getattr(g, 'BOSS3_WEIGHT_PREDICTIVE_STRESS', 0.9) * s),
                ("log_spiral_burst", (getattr(g, 'BOSS3_WEIGHT_SPIRAL_BASE', 0.4) + getattr(g, 'BOSS3_WEIGHT_SPIRAL_DEADLINE', 1.4) * (1.0 - r)) * (1.0 + getattr(g, 'BOSS3_WEIGHT_SPIRAL_PHASE_BONUS', 0.4) * ((self.boss.phase - 1) / 2.0))),
            ]
            if self.boss.phase >= 3:
                weights.append(("void_shard_rain", getattr(g, 'BOSS3_WEIGHT_RAIN_BASE', 1.6) + getattr(g, 'BOSS3_WEIGHT_RAIN_DEADLINE', 1.2) * (1.0 - r) + getattr(g, 'BOSS3_WEIGHT_RAIN_STRESS', 0.8) * s))
            total = sum(w for _, w in weights)
            pick = random.uniform(0, total)
            acc = 0.0
            for name, w in weights:
                acc += w
                if pick <= acc:
                    self.boss.change_state(name)
                    break
#endregion DriftState


#region DistractionFieldState
class DistractionFieldState(BossState):
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph = 0.0
        self.duration = getattr(g, 'BOSS3_DISTRACTION_DURATION', 1.3)
        self.elapsed = 0.0
        self.lambda0 = getattr(g, 'BOSS3_DISTRACTION_LAMBDA0', 10.0)
        self.spawn_carry = 0.0

    def enter(self):
        self.telegraph = min(0.9, self.boss.telegraph_time())
        self.boss.telegraph_timer = self.telegraph
        self.elapsed = 0.0
        self.spawn_carry = 0.0

    def update(self, dt, player, bullet_manager):
        if self.telegraph > 0:
            self.telegraph -= dt
            return

        self.elapsed += dt
        s = self.boss.stress / max(1.0, self.boss.max_stress)
        r = self.boss.deadline_ratio()
        boost = getattr(self.boss, 'get_backlog_boost', lambda: 1.0)()
        lam = self.lambda0 * (1.0 + s) * (1.0 + 0.8 * (1.0 - r)) * (1.0 + 0.5 * (boost - 1.0))
        expected = lam * dt + self.spawn_carry
        k = int(expected)
        self.spawn_carry = expected - k
        if k > 0:
            pcx = player.x + player.width / 2
            pcy = player.y + player.height / 2
            for _ in range(k):
                ang = random.uniform(0, 2 * math.pi)
                rad = random.uniform(28, 64)
                spawn_x = pcx + rad * math.cos(ang)
                spawn_y = pcy + rad * math.sin(ang)
                speed = g.BULLET_SPEEDS['normal'] * random.uniform(0.25, 0.45)
                vx = math.cos(ang) * speed
                vy = math.sin(ang) * speed
                bullet_manager.add_bullet(spawn_x, spawn_y, vx, vy, 'normal', 'boss')

        if self.elapsed >= self.duration:
            self.boss.add_stress(-4)
            self.boss.change_state('drift')
#endregion DistractionFieldState


#region PredictiveBarrageState
class PredictiveBarrageState(BossState):
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph = 0.0
        self.shots_done = 0
        self.to_fire = 0
        self.fire_timer = 0
        self.maybe_fake = False

    def enter(self):
        self.telegraph = self.boss.telegraph_time()
        self.shots_done = 0
        self.to_fire = 2 + min(3, int(self.boss.stress // 20))
        self.fire_timer = 0.0
        self.boss.telegraph_timer = self.telegraph
        s = self.boss.stress / max(1.0, self.boss.max_stress)
        self.maybe_fake = (
            s < getattr(g, 'BOSS3_PRED_FAKE_STRESS_T', 0.3)
            and random.random() < getattr(g, 'BOSS3_PRED_FAKE_PROB', 0.25)
        )

    def update(self, dt, player, bullet_manager):
        if self.telegraph > 0:
            self.telegraph -= dt
            if self.telegraph <= 0 and self.maybe_fake and self.shots_done == 0:
                self.boss.add_stress(+3)
                self.boss.fake_streak = getattr(self.boss, 'fake_streak', 0) + 1
                self.boss.change_state('drift')
                return
            if self.telegraph > 0:
                return
        self.fire_timer += dt
        boost = getattr(self.boss, 'get_backlog_boost', lambda: 1.0)()
        interval = getattr(g, 'BOSS3_PRED_INTERVAL_BOOST', 0.32) if boost > 1.0 else getattr(g, 'BOSS3_PRED_INTERVAL_BASE', 0.35)
        extra = getattr(g, 'BOSS3_PRED_EXTRA_SALVO', 1) if boost > 1.0 else 0
        base_to_fire = 2 + min(3, int(self.boss.stress // 20))
        self.to_fire = base_to_fire + extra
        if self.fire_timer >= interval and self.shots_done < self.to_fire:
            self.fire_timer = 0.0
            self.shots_done += 1
            speed = self.boss.homing_speed()
            bx = self.boss.x + self.boss.width / 2
            by = self.boss.y + self.boss.height / 2
            px = player.x + player.width / 2
            py = player.y + player.height / 2
            rx = px - bx
            ry = py - by
            vxp = player.vx
            vyp = player.vy
            A = (vxp * vxp + vyp * vyp) - (speed * speed)
            B = 2 * (rx * vxp + ry * vyp)
            C = (rx * rx + ry * ry)
            t = None
            if abs(A) < 1e-5:
                if abs(B) > 1e-5:
                    t = max(0.0, -C / B)
            else:
                disc = B * B - 4 * A * C
                if disc >= 0:
                    sqrt_disc = math.sqrt(disc)
                    t1 = (-B + sqrt_disc) / (2 * A)
                    t2 = (-B - sqrt_disc) / (2 * A)
                    t_candidates = [tt for tt in (t1, t2) if tt >= 0]
                    if t_candidates:
                        t = min(t_candidates)
            if t is None:
                d = math.hypot(rx, ry)
                ux, uy = (rx / d, ry / d) if d > 0 else (1.0, 0.0)
            else:
                lead_x = rx + vxp * t
                lead_y = ry + vyp * t
                d = math.hypot(lead_x, lead_y)
                ux, uy = (lead_x / d, lead_y / d) if d > 0 else (1.0, 0.0)
            bullet_manager.add_bullet(bx, by, ux * speed, uy * speed, 'homing', 'boss')
        if self.shots_done >= self.to_fire:
            self.boss.add_stress(-4)
            if getattr(self.boss, 'fake_streak', 0) >= 2 and getattr(self.boss, 'backlog_boost_timer', 0.0) <= 0.0:
                self.boss.backlog_boost_timer = getattr(g, 'BOSS3_BACKLOG_DURATION', 4.0)
                self.boss.fake_streak = 0
            if self.boss.phase >= 2:
                self.boss.change_state('log_spiral_burst')
            else:
                self.boss.change_state('drift')
#endregion PredictiveBarrageState


#region LogSpiralBurstState
class LogSpiralBurstState(BossState):
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph = 0.0
        self.time = 0.0
        self.theta = 0.0
        self.spawn_timer = 0.0

    def enter(self):
        self.telegraph = max(0.25, self.boss.telegraph_time() * 0.8)
        self.time = 0.0
        bx = self.boss.x + self.boss.width / 2
        by = self.boss.y + self.boss.height / 2
        dx = (self.boss.last_player_x if hasattr(self.boss, 'last_player_x') else bx) - bx
        dy = (self.boss.last_player_y if hasattr(self.boss, 'last_player_y') else by) - by
        self.theta = math.atan2(dy, dx) if (dx or dy) else -math.pi/4
        self.spawn_timer = 0.0
        self.boss.telegraph_timer = self.telegraph

    def update(self, dt, player, bullet_manager):
        if self.telegraph > 0:
            self.telegraph -= dt
            return
        self.time += dt
        self.spawn_timer += dt
        r = self.boss.deadline_ratio()
        s_norm = self.boss.stress / max(1.0, self.boss.max_stress)
        boost = getattr(self.boss, 'get_backlog_boost', lambda: 1.0)()
        omega = (
            getattr(g, 'BOSS3_SPIRAL_OMEGA_BASE', 2.6)
            + getattr(g, 'BOSS3_SPIRAL_OMEGA_DEADLINE', 1.6) * (1.0 - r)
        ) * (1.0 + getattr(g, 'BOSS3_SPIRAL_OMEGA_BOOST', 0.12) * (boost - 1.0))
        k = (
            getattr(g, 'BOSS3_SPIRAL_K_BASE', 0.14)
            + getattr(g, 'BOSS3_SPIRAL_K_STRESS', 0.10) * s_norm
        ) * (1.0 + getattr(g, 'BOSS3_SPIRAL_K_BOOST', 0.18) * (boost - 1.0))
        base = g.BULLET_SPEEDS['normal'] * getattr(g, 'BOSS3_SPIRAL_BASE_SPEED_MULT', 0.55)
        spawn_dt = getattr(g, 'BOSS3_SPIRAL_SPAWN_INTERVAL', 0.05)
        while self.spawn_timer >= spawn_dt:
            self.spawn_timer -= spawn_dt
            speed = base * math.exp(k * (self.theta % (2 * math.pi)))
            vx = math.cos(self.theta) * speed
            vy = math.sin(self.theta) * speed
            bullet_manager.add_bullet(
                self.boss.x + self.boss.width/2,
                self.boss.y + self.boss.height/2,
                vx, vy, 'laser', 'boss'
            )
            self.theta += omega * spawn_dt
        if self.time >= getattr(g, 'BOSS3_SPIRAL_DURATION', 1.8):
            if self.boss.phase >= 3:
                self.boss.change_state('void_shard_rain')
            else:
                self.boss.change_state('drift')
#endregion LogSpiralBurstState


#region VoidShardRainState
class VoidShardRainState(BossState):
    """Falling void shards (black squares) from the top of the screen."""
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph = 0.0
        self.time = 0.0
        self.spawn_carry = 0.0

    def enter(self):
        self.telegraph = max(0.2, self.boss.telegraph_time() * 0.7)
        self.boss.telegraph_timer = self.telegraph
        self.time = 0.0
        self.spawn_carry = 0.0

    def update(self, dt, player, bullet_manager):
        if self.telegraph > 0:
            self.telegraph -= dt
            return
        self.time += dt

        s = self.boss.stress / max(1.0, self.boss.max_stress)
        r = self.boss.deadline_ratio()
        boost = getattr(self.boss, 'get_backlog_boost', lambda: 1.0)()
        lam = getattr(g, 'BOSS3_RAIN_LAMBDA0', 22.0) * (
            1.0 + getattr(g, 'BOSS3_RAIN_LAMBDA_DEADLINE', 0.8) * (1.0 - r)
        ) * (
            1.0 + getattr(g, 'BOSS3_RAIN_LAMBDA_STRESS', 0.6) * s
        ) * (1.0 + getattr(g, 'BOSS3_RAIN_LAMBDA_BOOST', 0.4) * (boost - 1.0))
        expected = lam * dt + self.spawn_carry
        k = int(expected)
        self.spawn_carry = expected - k
        px = player.x + player.width / 2
        for _ in range(k):
            if random.random() < getattr(g, 'BOSS3_RAIN_BIAS_PLAYER_MIX', 0.6):
                x = max(20, min(g.SCREENWIDTH - 20, random.gauss(px, getattr(g, 'BOSS3_RAIN_BIAS_PLAYER_SIGMA', 120.0))))
            else:
                x = random.uniform(20, g.SCREENWIDTH - 20)
            y = -10
            vy = g.BULLET_SPEEDS.get('void_shard', 300) * (
                getattr(g, 'BOSS3_RAIN_VY_BASE_MULT', 0.8) + getattr(g, 'BOSS3_RAIN_VY_DEADLINE', 0.4) * (1.0 - r)
            ) / max(0.01, g.BULLET_SPEEDS.get('void_shard', 300) / 300)
            vx = random.uniform(-getattr(g, 'BOSS3_RAIN_VX_JITTER', 40.0), getattr(g, 'BOSS3_RAIN_VX_JITTER', 40.0))
            bullet_manager.add_bullet(x, y, vx, vy, 'void_shard', 'boss')

        duration = getattr(g, 'BOSS3_RAIN_DURATION_BASE', 1.6) + getattr(g, 'BOSS3_RAIN_DURATION_STRESS', 0.3) * s
        if self.time >= duration:
            self.boss.change_state('drift')
#endregion VoidShardRainState


#region The Hollow Boss
class TheHollow:
    width = 48
    height = 64

    entry_line = "You think words can scare me away?"
    defeat_line = "This is not a threat-it's my process"

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.max_health = getattr(g, 'BOSS3_MAX_HEALTH', 520)
        self.health = self.max_health
        self.phase = 1
        self.move_speed = getattr(g, 'BOSS3_MOVE_SPEED', 110)
        self.max_stress = 100
        self.stress = 10
        self.deadline_total = getattr(g, 'DEADLINE_SECONDS', 120)
        self.deadline_left = float(self.deadline_total)
        self.states = {
            'drift': DriftState(self),
            'distraction_field': DistractionFieldState(self),
            'predictive_barrage': PredictiveBarrageState(self),
            'log_spiral_burst': LogSpiralBurstState(self),
            'void_shard_rain': VoidShardRainState(self),
        }
        self.current_state = self.states['drift']
        self.current_state.enter()
        self.telegraph_timer = 0.0
        self.fake_streak = 0
        self.backlog_boost_timer = 0.0
        self.checkpoint_stage = 0
        self.drop_impulse = 0.0

    def get_backlog_boost(self) -> float:
        return (getattr(g, 'BOSS3_BACKLOG_BOOST_MULT', 1.5) if self.backlog_boost_timer > 0.0 else 1.0)

    # Helpers
    def add_stress(self, delta):
        self.stress = max(0, min(self.max_stress, self.stress + delta))

    def deadline_ratio(self):
        return max(0.0, min(1.0, self.deadline_left / self.deadline_total)) if self.deadline_total > 0 else 0.0

    def telegraph_time(self):
        base = getattr(g, 'BOSS3_TELEGRAPH_BASE', 1.1)
        return max(0.4, base * (1.0 - 0.003 * self.stress))

    # Tunables
    def get_current_cooldown(self):
        if self.phase == 1:
            base = getattr(g, 'BOSS3_COOLDOWN_P1', 1.8)
        elif self.phase == 2:
            base = getattr(g, 'BOSS3_COOLDOWN_P2', 1.2)
        else:
            base = getattr(g, 'BOSS3_COOLDOWN_P3', 0.9)
        return max(0.5, base * (1.0 - 0.0025 * self.stress))

    def homing_speed(self):
        base = getattr(g, 'BOSS3_HOMING_BASE_SPEED', 200)
        return base * (1.0 + 0.004 * self.stress)

    # FSM
    def change_state(self, name):
        if name in self.states:
            self.current_state.exit()
            self.current_state = self.states[name]
            self.current_state.enter()

    # Update
    def update(self, dt, player, bullet_manager: BulletManager):
        # Phase transitions by HP ratio (configurable in globals.py)
        p2_ratio = getattr(g, 'HOLLOW_PHASE2_HP_RATIO', 0.7)
        p3_ratio = getattr(g, 'HOLLOW_PHASE3_HP_RATIO', 0.35)
        if self.phase == 1 and self.health <= self.max_health * p2_ratio:
            self.phase = 2
        if self.phase == 2 and self.health <= self.max_health * p3_ratio:
            self.phase = 3
        self.deadline_left = max(0.0, self.deadline_left - dt)
        if self.backlog_boost_timer > 0.0:
            self.backlog_boost_timer = max(0.0, self.backlog_boost_timer - dt)
        r = self.deadline_ratio()
        stage = 0
        if r <= 0.6:
            stage = 1
        if r <= 0.4:
            stage = 2
        if r <= 0.2:
            stage = 3
        if stage > self.checkpoint_stage:
            self.drop_impulse = max(self.drop_impulse, 160.0 + 60.0 * stage)
            self.checkpoint_stage = stage
        self.add_stress(+dt * 2.0)
        self.x = max(50, min(g.SCREENWIDTH - self.width - 50, self.x))
        y_max_dyn = 220 + 160 * (1.0 - self.deadline_ratio()) + 60 * ((self.phase - 1) / 2.0)
        y_max_dyn = min(y_max_dyn, g.SCREENHEIGHT - 100)
        self.y = max(50, min(y_max_dyn, self.y))
        self.last_player_x = player.x + player.width / 2
        self.last_player_y = player.y + player.height / 2
        self.telegraph_timer = max(0.0, self.telegraph_timer - dt)
        self.current_state.update(dt, player, bullet_manager)

    # Combat
    def take_damage(self, dmg):
        self.health = max(0, self.health - dmg)
        self.add_stress(-min(6, dmg * 0.6))

    # Render
    def draw(self, screen: pygame.Surface):
        # Black silhouette body
        body_color = (10, 10, 10)
        pygame.draw.rect(screen, body_color, (int(self.x), int(self.y), self.width, self.height))
        # subtle outline when telegraphing
        if self.telegraph_timer > 0 and int(self.telegraph_timer * 10) % 2:
            pygame.draw.rect(screen, (200, 200, 200), (int(self.x), int(self.y), self.width, self.height), 2)
        # phase label (gray)
        font = pygame.font.Font(None, 22)
        label = font.render(f"The Hollow - P{self.phase}", True, (220, 220, 220))
        screen.blit(label, (self.x, self.y - 24))
#endregion The Hollow Boss
