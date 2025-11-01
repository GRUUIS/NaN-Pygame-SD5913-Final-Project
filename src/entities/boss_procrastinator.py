"""
Procrastinator Boss - themed around procrastination and stress.
Math-driven attacks to evoke mounting pressure and indecision.

Highlights:
- Lissajous drift path to feel unfocused movement
- Poisson-distributed Distraction Field spawning around the player
- Predictive pursuit barrage (lead computation via quadratic interception)
- Logarithmic spiral burst (angle-monotone with exponential speed ramp)

Only existing bullet types are used: 'normal', 'homing', 'laser'.
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
    """Lissajous drift and state selection based on stress and deadline.

    Path: x = cx + Ax sin(ω t), y = cy + Ay sin(2 ω t + φ)
    This gives a lazy, unfocused meander.
    """
    def __init__(self, boss):
        super().__init__(boss)
        self.timer = 0.0
        self.t = 0.0
        # parameters (will be modulated slightly every enter)
        self.omega = 1.1
        self.phi = 0.9
        self.Ax = 160
        self.Ay = 60
        # center near top
        self.cx = boss.x
        self.cy = 140
        # soften entry to avoid visible teleport
        self.blend_time = getattr(g, 'BOSS2_DRIFT_BLEND_TIME', 0.25)
        self.blend_elapsed = 0.0
        self.start_x = boss.x
        self.start_y = boss.y

    def enter(self):
        self.timer = 0.0
        # keep phase continuity loosely; small random to avoid repetitive loops
        self.t = random.uniform(0.0, 0.6)
        # slight variation to avoid repetitiveness
        self.omega = 1.0 + random.uniform(-0.15, 0.2)
        self.phi = random.uniform(0.6, 1.4)
        self.Ax = 140 + random.uniform(-30, 40)
        self.Ay = 50 + random.uniform(-10, 15)
        # start from current boss location to avoid snap
        self.cx = self.boss.x
        self.cy = self.boss.y
        self.blend_time = getattr(g, 'BOSS2_DRIFT_BLEND_TIME', 0.25)
        self.blend_elapsed = 0.0
        self.start_x = self.boss.x
        self.start_y = self.boss.y

    def update(self, dt, player, bullet_manager):
        self.timer += dt
        self.t += dt

        # Approach factor based on phase, stress, and deadline (closer as fight progresses)
        s = self.boss.stress / max(1.0, self.boss.max_stress)
        r = self.boss.deadline_ratio()
        phase_norm = (self.boss.phase - 1) / 2.0  # 0..1
        a_min = getattr(g, 'BOSS2_APPROACH_MIN', 0.05)
        a_max = getattr(g, 'BOSS2_APPROACH_MAX', 0.92)
        a_base = getattr(g, 'BOSS2_APPROACH_BASE', 0.22)
        a_phase = getattr(g, 'BOSS2_APPROACH_PHASE', 0.38)
        a_dead = getattr(g, 'BOSS2_APPROACH_DEADLINE', 0.38)
        a_stress = getattr(g, 'BOSS2_APPROACH_STRESS', 0.18)
        approach = max(a_min, min(a_max, a_base + a_phase * phase_norm + a_dead * (1.0 - r) + a_stress * s))

        # Desired drift center moves toward the player as approach increases
        pcx = player.x + player.width / 2
        pcy = player.y + player.height / 2
        base_cx = g.SCREENWIDTH * 0.5
        base_cy = getattr(g, 'BOSS2_BASE_CY', 120.0)
        desired_cx = base_cx * (1.0 - approach) + pcx * approach
        # Keep boss generally above player, but allow descent as approach increases
        desired_cy = base_cy * (1.0 - approach) + (pcy - 80) * approach
        # Smoothly chase desired center
        chase_rate = getattr(g, 'BOSS2_CHASE_RATE', 3.0)
        self.cx += (desired_cx - self.cx) * min(1.0, chase_rate * dt)
        self.cy += (desired_cy - self.cy) * min(1.0, chase_rate * dt)

        # Reduce drift amplitude as approach grows (less meander, more“贴脸”)
        shrink = getattr(g, 'BOSS2_AMPLITUDE_SHRINK', 0.52)
        Ax_eff = self.Ax * (1.0 - shrink * approach)
        Ay_eff = self.Ay * (1.0 - shrink * approach)

        # Lissajous drift around the moving center
        x_lis = self.cx + Ax_eff * math.sin(self.omega * self.t)
        y_lis = self.cy + Ay_eff * math.sin(2 * self.omega * self.t + self.phi)

        # blend-in to avoid jump when entering this state
        if self.blend_elapsed < self.blend_time:
            self.blend_elapsed += dt
            a = min(1.0, self.blend_elapsed / self.blend_time)
            x_try = self.start_x * (1 - a) + x_lis * a
            y_try = self.start_y * (1 - a) + y_lis * a
        else:
            x_try = x_lis
            y_try = y_lis

        # checkpoint downward impulse (calendar shock)
        if getattr(self.boss, 'drop_impulse', 0.0) > 0.0:
            y_try += self.boss.drop_impulse * 0.5 * dt
            decay = getattr(g, 'BOSS2_DROP_DECAY', 220.0)
            self.boss.drop_impulse = max(0.0, self.boss.drop_impulse - decay * dt)

        # progressive safe radius shrink around player: enforce min separation
        pcx = player.x + player.width / 2
        pcy = player.y + player.height / 2
        dx = x_try - pcx
        dy = y_try - pcy
        dist = math.hypot(dx, dy)
        # min separation shrinks with progress
        min_sep = (
            getattr(g, 'BOSS2_MIN_SEP_BASE', 260.0)
            - getattr(g, 'BOSS2_MIN_SEP_PHASE', 160.0) * phase_norm
            - getattr(g, 'BOSS2_MIN_SEP_DEADLINE', 140.0) * (1.0 - r)
            - getattr(g, 'BOSS2_MIN_SEP_STRESS', 80.0) * s
        )
        min_sep = max(getattr(g, 'BOSS2_MIN_SEP_MIN', 80.0), min(getattr(g, 'BOSS2_MIN_SEP_MAX', 260.0), min_sep))
        if dist < min_sep and dist > 1e-3:
            scale = min_sep / dist
            x_try = pcx + dx * scale
            y_try = pcy + dy * scale

        # keep boss inside reasonable bounds; allow deeper descent as deadline nears
        y_max_dyn = (
            getattr(g, 'BOSS2_Y_MAX_BASE', 220.0)
            + getattr(g, 'BOSS2_Y_MAX_DEADLINE_ADD', 160.0) * (1.0 - r)
            + getattr(g, 'BOSS2_Y_MAX_PHASE_ADD', 60.0) * phase_norm
        )
        y_max_dyn = min(y_max_dyn, g.SCREENHEIGHT - getattr(g, 'BOSS2_Y_MAX_MARGIN', 100.0))
        self.boss.x = max(40, min(g.SCREENWIDTH - self.boss.width - 40, x_try))
        self.boss.y = max(40, min(y_max_dyn, y_try))

        cooldown = self.boss.get_current_cooldown()
        if self.timer >= cooldown:
            s = self.boss.stress / max(1.0, self.boss.max_stress)
            r = self.boss.deadline_ratio()
            # weights favor distractions at low stress, spiral/squeeze near deadline
            weights = [
                ("distraction_field", getattr(g, 'BOSS2_WEIGHT_DISTRACTION_BASE', 0.9) + getattr(g, 'BOSS2_WEIGHT_DISTRACTION_STRESS', 0.6) * s),
                ("predictive_barrage", getattr(g, 'BOSS2_WEIGHT_PREDICTIVE_BASE', 0.6) + getattr(g, 'BOSS2_WEIGHT_PREDICTIVE_STRESS', 0.9) * s),
                ("log_spiral_burst", (getattr(g, 'BOSS2_WEIGHT_SPIRAL_BASE', 0.4) + getattr(g, 'BOSS2_WEIGHT_SPIRAL_DEADLINE', 1.4) * (1.0 - r)) * (1.0 + getattr(g, 'BOSS2_WEIGHT_SPIRAL_PHASE_BONUS', 0.4) * ((self.boss.phase - 1) / 2.0))),
            ]
            # In phase 3, introduce rain barrage with high weight
            if self.boss.phase >= 3:
                weights.append(("rain_barrage", getattr(g, 'BOSS2_WEIGHT_RAIN_BASE', 1.6) + getattr(g, 'BOSS2_WEIGHT_RAIN_DEADLINE', 1.2) * (1.0 - r) + getattr(g, 'BOSS2_WEIGHT_RAIN_STRESS', 0.8) * s))
            # normalize and sample
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
    """Poisson-distributed distractions around the player.

    At rate λ(s, r) = λ0 * (1 + s) * (1 + 0.8*(1 - r)), we spawn slow bullets
    on a ring around the player with small outward velocity, creating a
    creeping pressure field that needs navigation.
    """
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph = 0.0
        self.duration = getattr(g, 'BOSS2_DISTRACTION_DURATION', 1.3)
        self.elapsed = 0.0
        self.lambda0 = getattr(g, 'BOSS2_DISTRACTION_LAMBDA0', 10.0)  # base events per second
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
        # rate as function of stress s in [0,1] and deadline ratio r in [0,1]
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
    """Predictive homing barrage: compute interception lead using linear algebra.

    Solve (v·v - s^2) t^2 + 2 (r·v) t + (r·r) = 0 for t >= 0
    where r = p - b and v = v_player, s = homing speed. Initial shot is led,
    then homing refines during flight via BulletManager's homing.
    """
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
        # base 2, + up to 3 with stress
        self.to_fire = 2 + min(3, int(self.boss.stress // 20))
        self.fire_timer = 0.0
        self.boss.telegraph_timer = self.telegraph
        # Small chance to fake at low stress: procrastinate the commitment
        s = self.boss.stress / max(1.0, self.boss.max_stress)
        self.maybe_fake = (
            s < getattr(g, 'BOSS2_PRED_FAKE_STRESS_T', 0.3)
            and random.random() < getattr(g, 'BOSS2_PRED_FAKE_PROB', 0.25)
        )

    def update(self, dt, player, bullet_manager):
        if self.telegraph > 0:
            self.telegraph -= dt
            # If we planned to fake and telegraph ended, bail out without firing
            if self.telegraph <= 0 and self.maybe_fake and self.shots_done == 0:
                # procrastinate: skip firing, increase stress and streak
                self.boss.add_stress(+3)
                self.boss.fake_streak = getattr(self.boss, 'fake_streak', 0) + 1
                # possible future backlash boost will be granted when we do fire next time
                self.boss.change_state('drift')
                return
            if self.telegraph > 0:
                return
        self.fire_timer += dt
        # backlog boost adds extra salvos and shortens interval slightly
        boost = getattr(self.boss, 'get_backlog_boost', lambda: 1.0)()
        interval = getattr(g, 'BOSS2_PRED_INTERVAL_BOOST', 0.32) if boost > 1.0 else getattr(g, 'BOSS2_PRED_INTERVAL_BASE', 0.35)
        extra = getattr(g, 'BOSS2_PRED_EXTRA_SALVO', 1) if boost > 1.0 else 0
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
            # coefficients for quadratic: A t^2 + B t + C = 0
            A = (vxp * vxp + vyp * vyp) - (speed * speed)
            B = 2 * (rx * vxp + ry * vyp)
            C = (rx * rx + ry * ry)
            t = None
            if abs(A) < 1e-5:
                # linear fall-back
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
                # direct aim
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
            # if we had procrastinated recently, cash in backlash boost
            if getattr(self.boss, 'fake_streak', 0) >= 2 and getattr(self.boss, 'backlog_boost_timer', 0.0) <= 0.0:
                self.boss.backlog_boost_timer = getattr(g, 'BOSS2_BACKLOG_DURATION', 4.0)
                self.boss.fake_streak = 0
            # In phase 2+, follow with spiral sweep; phase 3 will itself chain into rain
            if self.boss.phase >= 2:
                self.boss.change_state('log_spiral_burst')
            else:
                self.boss.change_state('drift')
#endregion PredictiveBarrageState


#region LogSpiralBurstState
class LogSpiralBurstState(BossState):
    """Logarithmic spiral burst using angle ramp and exponential speed.

    θ(t) = θ0 + ω t,  s(θ) = s_min * exp(k θ)
    Bullets are independent straight movers; the envelope forms a log spiral.
    """
    def __init__(self, boss):
        super().__init__(boss)
        self.telegraph = 0.0
        self.time = 0.0
        self.theta = 0.0
        self.spawn_timer = 0.0

    def enter(self):
        self.telegraph = max(0.25, self.boss.telegraph_time() * 0.8)
        self.time = 0.0
        # start angle aimed near player
        bx = self.boss.x + self.boss.width / 2
        by = self.boss.y + self.boss.height / 2
        # approximate initial aim
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
        # parameters
        r = self.boss.deadline_ratio()
        s_norm = self.boss.stress / max(1.0, self.boss.max_stress)
        boost = getattr(self.boss, 'get_backlog_boost', lambda: 1.0)()
        omega = (
            getattr(g, 'BOSS2_SPIRAL_OMEGA_BASE', 2.6)
            + getattr(g, 'BOSS2_SPIRAL_OMEGA_DEADLINE', 1.6) * (1.0 - r)
        ) * (1.0 + getattr(g, 'BOSS2_SPIRAL_OMEGA_BOOST', 0.12) * (boost - 1.0))
        k = (
            getattr(g, 'BOSS2_SPIRAL_K_BASE', 0.14)
            + getattr(g, 'BOSS2_SPIRAL_K_STRESS', 0.10) * s_norm
        ) * (1.0 + getattr(g, 'BOSS2_SPIRAL_K_BOOST', 0.18) * (boost - 1.0))
        base = g.BULLET_SPEEDS['normal'] * getattr(g, 'BOSS2_SPIRAL_BASE_SPEED_MULT', 0.55)
        # spawn every configured interval
        spawn_dt = getattr(g, 'BOSS2_SPIRAL_SPAWN_INTERVAL', 0.05)
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
        if self.time >= getattr(g, 'BOSS2_SPIRAL_DURATION', 1.8):
            # In phase 3, follow up with rain barrage to choke movement
            if self.boss.phase >= 3:
                self.boss.change_state('rain_barrage')
            else:
                self.boss.change_state('drift')
#endregion LogSpiralBurstState


#region RainBarrageState
class RainBarrageState(BossState):
    """Dense vertical rain to restrict player movement (phase 3 emphasis).

    Spawns falling bullets from top with slight lateral variance.
    Intensity scales with (1 - deadline_ratio) and stress; backlog boost applies.
    """
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

        # intensity controls
        s = self.boss.stress / max(1.0, self.boss.max_stress)
        r = self.boss.deadline_ratio()
        boost = getattr(self.boss, 'get_backlog_boost', lambda: 1.0)()
        lam = getattr(g, 'BOSS2_RAIN_LAMBDA0', 22.0) * (
            1.0 + getattr(g, 'BOSS2_RAIN_LAMBDA_DEADLINE', 0.8) * (1.0 - r)
        ) * (
            1.0 + getattr(g, 'BOSS2_RAIN_LAMBDA_STRESS', 0.6) * s
        ) * (1.0 + getattr(g, 'BOSS2_RAIN_LAMBDA_BOOST', 0.4) * (boost - 1.0))
        expected = lam * dt + self.spawn_carry
        k = int(expected)
        self.spawn_carry = expected - k
        # spawn k bullets across the width with bias near player
        px = player.x + player.width / 2
        for _ in range(k):
            # mixture: bias near player vs uniform
            if random.random() < getattr(g, 'BOSS2_RAIN_BIAS_PLAYER_MIX', 0.6):
                x = max(20, min(g.SCREENWIDTH - 20, random.gauss(px, getattr(g, 'BOSS2_RAIN_BIAS_PLAYER_SIGMA', 120.0))))
            else:
                x = random.uniform(20, g.SCREENWIDTH - 20)
            y = -10
            vy = g.BULLET_SPEEDS['laser'] * (
                getattr(g, 'BOSS2_RAIN_VY_BASE_MULT', 0.8) + getattr(g, 'BOSS2_RAIN_VY_DEADLINE', 0.4) * (1.0 - r)
            )
            vx = random.uniform(-getattr(g, 'BOSS2_RAIN_VX_JITTER', 40.0), getattr(g, 'BOSS2_RAIN_VX_JITTER', 40.0))
            bullet_manager.add_bullet(x, y, vx, vy, 'laser', 'boss')

        # duration scales slightly with phase/stress
        duration = getattr(g, 'BOSS2_RAIN_DURATION_BASE', 1.6) + getattr(g, 'BOSS2_RAIN_DURATION_STRESS', 0.3) * s
        if self.time >= duration:
            self.boss.change_state('drift')
#endregion RainBarrageState


#region Procrastinator Boss
class Procrastinator:
    width = 48
    height = 48

    def __init__(self, x, y):
        self.x = x
        self.y = y
        # config
        self.max_health = getattr(g, 'BOSS2_MAX_HEALTH', 520)
        self.health = self.max_health
        self.phase = 1
        self.move_speed = getattr(g, 'BOSS2_MOVE_SPEED', 110)
        # stress and deadline
        self.max_stress = 100
        self.stress = 10
        self.deadline_total = getattr(g, 'DEADLINE_SECONDS', 120)
        self.deadline_left = float(self.deadline_total)
        # FSM
        self.states = {
            'drift': DriftState(self),
            'distraction_field': DistractionFieldState(self),
            'predictive_barrage': PredictiveBarrageState(self),
            'log_spiral_burst': LogSpiralBurstState(self),
            'rain_barrage': RainBarrageState(self),
        }
        self.current_state = self.states['drift']
        self.current_state.enter()
        # visuals
        self.telegraph_timer = 0.0
        # procrastination/backlog dynamics
        self.fake_streak = 0
        self.backlog_boost_timer = 0.0
        self.checkpoint_stage = 0  # how many thresholds crossed (0..3)
        self.drop_impulse = 0.0

    def get_backlog_boost(self) -> float:
        """Temporary boost multiplier after procrastination streak cashes in."""
        return (getattr(g, 'BOSS2_BACKLOG_BOOST_MULT', 1.5) if self.backlog_boost_timer > 0.0 else 1.0)

    #region Helpers
    def add_stress(self, delta):
        self.stress = max(0, min(self.max_stress, self.stress + delta))

    def deadline_ratio(self):
        return max(0.0, min(1.0, self.deadline_left / self.deadline_total)) if self.deadline_total > 0 else 0.0

    def is_in_deadline_rush(self):
        # trigger occasional rushes at thresholds
        r = self.deadline_ratio()
        return r < 0.25 and random.random() < 0.15

    def telegraph_time(self):
        base = getattr(g, 'BOSS2_TELEGRAPH_BASE', 1.1)
        # higher stress -> shorter telegraph
        return max(0.4, base * (1.0 - 0.003 * self.stress))
    #endregion Helpers

    #region Tunables Accessors
    def get_current_cooldown(self):
        if self.phase == 1:
            base = getattr(g, 'BOSS2_COOLDOWN_P1', 1.8)
        elif self.phase == 2:
            base = getattr(g, 'BOSS2_COOLDOWN_P2', 1.2)
        else:
            base = getattr(g, 'BOSS2_COOLDOWN_P3', 0.9)
        return max(0.5, base * (1.0 - 0.0025 * self.stress))

    def homing_speed(self):
        base = getattr(g, 'BOSS2_HOMING_BASE_SPEED', 200)
        return base * (1.0 + 0.004 * self.stress)

    def laser_speed(self):
        base = getattr(g, 'BOSS2_LASER_BASE_SPEED', 360)
        # speed slightly increases with urgency
        return base * (1.0 + 0.3 * (1.0 - self.deadline_ratio()))
    #endregion Tunables Accessors

    #region FSM
    def change_state(self, name):
        if name in self.states:
            self.current_state.exit()
            self.current_state = self.states[name]
            self.current_state.enter()
    #endregion FSM

    #region Core Update
    def update(self, dt, player, bullet_manager: BulletManager):
        # update phase by health
        if self.phase == 1 and self.health <= self.max_health * 0.7:
            self.phase = 2
        if self.phase == 2 and self.health <= self.max_health * 0.35:
            self.phase = 3
        # stress and deadline progression
        self.deadline_left = max(0.0, self.deadline_left - dt)
        # backlog boost decay
        if self.backlog_boost_timer > 0.0:
            self.backlog_boost_timer = max(0.0, self.backlog_boost_timer - dt)
        # calendar checkpoints: 0.6, 0.4, 0.2
        r = self.deadline_ratio()
        stage = 0
        if r <= 0.6:
            stage = 1
        if r <= 0.4:
            stage = 2
        if r <= 0.2:
            stage = 3
        if stage > self.checkpoint_stage:
            # trigger a downward impulse; more severe at later checkpoints
            self.drop_impulse = max(self.drop_impulse, 160.0 + 60.0 * stage)
            self.checkpoint_stage = stage
        # natural stress grow if player not hitting boss
        self.add_stress(+dt * 2.0)
        # clamp position bounds (allow deeper descent as deadline nears / phase increases)
        self.x = max(50, min(g.SCREENWIDTH - self.width - 50, self.x))
        y_max_dyn = 220 + 160 * (1.0 - self.deadline_ratio()) + 60 * ((self.phase - 1) / 2.0)
        y_max_dyn = min(y_max_dyn, g.SCREENHEIGHT - 100)
        self.y = max(50, min(y_max_dyn, self.y))
        # cache last seen player center for aiming hints
        self.last_player_x = player.x + player.width / 2
        self.last_player_y = player.y + player.height / 2
        # update state logic
        self.telegraph_timer = max(0.0, self.telegraph_timer - dt)
        self.current_state.update(dt, player, bullet_manager)
    #endregion Core Update

    #region Combat
    def take_damage(self, dmg):
        self.health = max(0, self.health - dmg)
        # reduce stress on hit
        self.add_stress(-min(6, dmg * 0.6))
    #endregion Combat

    #region Rendering
    def draw(self, screen: pygame.Surface):
        # base color, shift with stress
        base_color = (90, 120, 200)  # calm blue
        stress_tint = min(1.0, self.stress / 100.0)
        color = (
            int(base_color[0] + stress_tint * 100),
            int(base_color[1] * (1.0 - 0.3 * stress_tint)),
            int(base_color[2] * (1.0 - 0.6 * stress_tint)),
        )
        pygame.draw.rect(screen, color, (int(self.x), int(self.y), self.width, self.height))
        # telegraph flash overlay
        if self.telegraph_timer > 0 and int(self.telegraph_timer * 10) % 2:
            pygame.draw.rect(screen, (255, 120, 120), (int(self.x), int(self.y), self.width, self.height), 2)
        # phase label
        font = pygame.font.Font(None, 22)
        label = font.render(f"Phase {self.phase}", True, g.COLORS['ui_text'])
        screen.blit(label, (self.x, self.y - 24))
    #endregion Rendering
#endregion Procrastinator Boss

