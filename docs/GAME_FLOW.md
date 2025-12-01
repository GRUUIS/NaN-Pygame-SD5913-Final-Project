# Mind's Maze - 游戏场景流程图

## 🎮 完整游戏流程

### 运行方式
```bash
# 完整游戏流程
python testing/game_flow_manager.py
# 或
python main.py
```

---

## 📋 场景列表及串联

### 1️⃣ **主菜单** (Main Menu)
**文件**: `combine/meun.py`  
**功能**: 游戏启动界面，提供开始/设置/退出选项  
**控制**: 方向键选择，Enter确认  
**转场**: 选择"Start Game" → 进入解谜场景

---

### 2️⃣ **解谜场景** (Third Puzzle Scene)
**文件**: `testing/new_third_puzzle.py`  
**功能**: 俯视角房间解谜，探索互动物品  
**地图**: `assets/tilemaps/test puzzle scene.tmj`  
**目标**: 探索房间，找到特定物品/触发机关  
**触发条件**: 
- 走到门前（坐标21,12或21,13）
- 右键点击门
**转场**: 完成解谜 → 进入梦境解谜

---

### 3️⃣ **梦境解谜** (First Dream Puzzle - Yume Nikki风格)
**文件**: `testing/first_dream_puzzle.py`  
**功能**: 梦日记风格的超现实梦境，包含4个子谜题  
**子谜题**:
1. **SequencePuzzle**: 颜色序列记忆谜题
2. **MemoryPuzzle**: 镜像反射移动谜题
3. **LightsPuzzle**: 声音节奏跟随谜题
4. **CodePuzzle**: 符号匹配限时谜题

**特色**:
- 8方向角色动画
- 梦境氛围（暗紫色调）
- 收集效果球（Effect Orbs）
- 超现实视觉效果

**控制**: WASD/方向键移动，Space/Enter互动  
**转场**: 收集所有效果球 → 进入梦境过渡

---

### 4️⃣ **梦境过渡** (Dream Transition)
**文件**: `testing/dream_transition_scene.py`  
**功能**: 主角从梦境人物转换为小女巫的过渡动画  
**视觉效果**:
- 梦境破碎/醒来效果
- 角色形态转换
- 平滑过渡动画

**转场**: 过渡完成 → 进入The Hollow战斗

---

### 5️⃣ **Boss1: The First Attack** (初遇虚无 - 剧情战)
**文件**: `src/scenes/boss1_scripted_scene.py`  
**类型**: 剧情式boss战（必败）  
**Boss**: The Hollow (虚无主义化身 - 初遇版本)  
**特色**:
- **漆黑背景**: 完全黑暗的战斗环境
- **压倒性攻击**: 无法躲避的弹幕
- **必然失败**: 玩家血量只有1点，一击即死
- **死亡过渡**: 渐变黑暗混沌效果（非僵硬卡帧）

**攻击模式**:
- **Crossfire Lasers**: 从左右两侧高速射来的激光（每0.18秒）
- **Aimed Lasers**: 从上方瞄准玩家的追踪激光（每0.6秒）

**全局变量修改**: 
- 将 `g.PLAYER_MOVE_SPEED` 降低到10%-18%（营造无力感）
- **重要**: 场景结束时必须调用 `exit()` 恢复原始速度

**转场**: 被击败后按Space → 进入Map01探索

---

### 6️⃣ **Map01 探索场景** (Map01 Exploration)
**文件**: `testing/map01_final.py`  
**功能**: 横版探索场景，玩家可以探索房间、收集物品  
**地图**: `assets/map01/Room1.tmj`  
**特色**:
- 横版平台跳跃
- 物品收集系统
- 门传送机制
- 齿轮拼图谜题

**控制**: 
- WASD/方向键移动
- W/Space跳跃（双段跳）
- Space拾取物品
- Z键跳过关卡

**转场**: 完成探索/到达出口 → 进入镜子房间

---

### 7️⃣ **镜子房间谜题** (Mirror Room Puzzle)
- **Voidfire**: 从屏幕边缘射向玩家的虚空火焰（每0.9秒）

**音效系统**:
- `hollow_rain.wav` - 初始攻击（宏大氛围音）
- `hollow_shoot.wav` - 每颗子弹发射时播放
- `hit.wav` - 被击中瞬间（音量0.7）
- `player_defeat.wav` - 失败音效（延迟200ms，音量0.8）

**死亡视觉效果**（持续约3秒）:
1. **红色闪光**: 被击中瞬间，红屏闪烁0.3秒（180 alpha淡出）
2. **混沌粒子**: 暗红色粒子随机生成并漂浮，制造混乱感
3. **玩家淡出**: 透明度从100%降至30%（0.7倍衰减速度）
4. **子弹消散**: 子弹逐渐变暗消失
5. **黑暗覆盖**: 脉动的黑暗层逐渐吞噬画面（红色色调脉冲）
6. **UI渐隐**: 血条等UI在fade 50%后消失
7. **提示文字**: 屏幕下方小字显示"Press SPACE to continue"（fade 60%后淡入）

**控制**: 
- WASD移动（被减速至10%-18%正常速度）
- 无法射击（射击功能被禁用）
- 死亡后按SPACE继续

**设计意图**: 
- 展现The Hollow的压倒性力量
- 建立后续真正战斗的动机
- 通过"必败体验"强化虚无主义主题

**转场**: 被击败后按Space → 进入Map01探索

---

### 6️⃣ **Map01 探索场景** (Map01 Exploration)
**文件**: `testing/map01_final.py`  
**功能**: 横版探索场景，玩家可以探索房间、收集物品  
**地图**: `assets/map01/Room1.tmj`  
**特色**:
- 横版平台跳跃
- 物品收集系统
- 门传送机制
- 齿轮拼图谜题

**控制**: 
- WASD/方向键移动
- W/Space跳跃（双段跳）
- Space拾取物品
- Z键跳过关卡

**转场**: 完成探索/到达出口 → 进入镜子房间

---

### 7️⃣ **镜子房间谜题** (Mirror Room Puzzle)
**文件**: `testing/mirror_room_puzzle.py`  
**功能**: 基于镜像反射的解谜房间  
**机制**: 
- 镜面对称谜题
- 光线反射机制
- 空间认知挑战

**转场**: 完成谜题 → 进入Boss2战斗

---

### 8️⃣ **Boss2: The Sloth战斗** (Procrastination Boss)
**文件**: `src/entities/sloth_battle_scene.py`  
**类型**: 战斗boss战  
**Boss**: The Sloth (拖延症化身)  
**难度**: 720 HP，3个阶段

**攻击模式**:
- **粘液轨迹** (Slime Trail): 持续地面伤害
- **冲刺攻击** (Dash): 高速横向冲击
- **粘液投射** (Slime Spit): 抛物线弹幕
- **孢子攻击** (Spore): 浮空后降落的毒池
- **碾压攻击** (Crush): 上方坠落AOE伤害

**阶段系统**:
- Phase 1 (100%-65%): 基础攻击
- Phase 2 (65%-50%): 加速攻击频率
- Enrage (<50%): 狂暴状态，所有攻击强化

**音效**:
- `sloth_charge.wav` - 冲刺准备
- `sloth_dash.wav` - 冲刺音效
- `sloth_slime.wav` - 粘液发射
- `sloth_impact.wav` - 碰撞音效

**胜利过渡**: 7阶段蒲公英飘散动画（11.5秒）  
**转场**: 胜利后走到场景边缘 → 进入画作房

---

### 9️⃣ **画作房谜题** (Painting Room Puzzle)
**文件**: `testing/painting_room_puzzle.py`  
**功能**: 画作相关的艺术谜题  
**机制**: 
- 观察画作细节
- 交互式艺术解谜
- 美学与逻辑结合

**转场**: 完成谜题 → 进入Boss3最终战

---

### 🔟 **Boss3: The Hollow最终战** (Final Boss - Nihilism)
**文件**: `src/entities/boss_battle_scene.py`  
**类型**: 最终boss战（真正可战胜版本）  
**Boss**: The Hollow (虚无主义化身 - 完整版)  
**难度**: 更高血量，完整攻击模式

**攻击模式**:
- **雨滴攻击** (Rain Attack): 从天而降的能量雨
- **瞄准激光** (Aimed Lasers): 追踪玩家的激光束
- **交叉火力** (Crossfire): 多方向同时攻击
- **终极技能**: 全屏压制性攻击

**阶段系统**: 多阶段战斗，每阶段解锁新攻击

**音效**:
- `hollow_rain.wav` - 雨滴攻击
- `hollow_shoot.wav` - 激光发射
- `hit.wav` - 击中音效
- BGM动态淡出

**胜利过渡**: 7阶段梦境醒来动画（11.5秒）
- 漆黑逐渐消散
- 虚空破碎效果
- 回归现实的视觉转换

---

## 🎯 完整流程图（ASCII）

```
菜单 → 解谜场景 → 梦境解谜 → 梦境过渡 → Boss1(必败) → Map01探索 
  ↓
镜子房间 → Boss2(The Sloth) → 画作房 → Boss3(The Hollow) → 通关
```

---

## 🎮 玩家能力

### 移动系统
- **WASD/方向键**: 左右移动
- **W键**: 跳跃（支持二段跳）
- **物理**: 重力800, 跳跃力500, 移动速度100

### 战斗系统
- **鼠标瞄准**: 自由360°瞄准
- **左键射击**: 发射子弹（冷却0.5秒）
- **子弹伤害**: 12点
- **玩家血量**: 200 HP
- **无敌帧**: 受击后1秒无敌

### Boss战特殊机制
- **Sloth战**: 普通子弹，需躲避粘液
- **Hollow战**: 虚空火焰子弹，需管理压力值

---

## 🎨 UI系统

### HUD显示 (`src/systems/ui.py`)
- **玩家血条**: 左上角，颜色随血量变化
- **Boss血条**: 顶部中央，显示名称和阶段
- **压力计**: Boss3战显示，boss死亡后隐藏
- **控制提示**: 底部显示当前可用操作
- **战斗时间**: 右下角显示经过时间

### 游戏结束屏幕
- **胜利**: "VICTORY! Press SPACE to continue"（绿色）
- **失败**: "DEFEAT Press R to restart"（红色）

---

## 🔑 快捷键

### 通用
- **ESC**: 退出当前场景/返回菜单
- **Z键**: 跳过当前关卡（开发者模式）

### Boss战斗
- **R键**: 失败后重新开始
- **SPACE**: 胜利后继续（部分场景）

### 测试模式
```bash
python main.py boss1    # 直接测试Boss1（剧情战）
python main.py boss2    # 直接测试Boss2 (Sloth)
python main.py boss3    # 直接测试Boss3 (Hollow)
```

---

## 📊 场景流程图（详细版）

```
┌─────────────┐
│  主菜单     │ (combine/meun.py)
└──────┬──────┘
       │ Start Game
       ▼
┌─────────────┐
│  解谜场景   │ (new_third_puzzle.py)
└──────┬──────┘
       │ 完成解谜/走到门前右键
       ▼
┌─────────────┐
│  梦境解谜   │ (first_dream_puzzle.py)
│ 4个子谜题   │ Sequence/Memory/Lights/Code
└──────┬──────┘
       │ 收集所有效果球
       ▼
┌─────────────┐
│  梦境过渡   │ (dream_transition_scene.py)
│ 角色转换    │ 梦境人物 → 小女巫
└──────┬──────┘
       │ 过渡完成
       ▼
┌─────────────┐
│ Boss1战斗   │ (boss1_scripted_scene.py)
│ The Hollow  │ 剧情式必败，压倒性弹幕攻击
└──────┬──────┘
       │ 被击败后按Space
       ▼
┌─────────────┐
│ Map01探索   │ (map01_final.py)
│ 横版平台    │ 收集物品，探索房间
└──────┬──────┘
       │ 到达出口/完成探索
       ▼
┌─────────────┐
│ 镜子房间    │ (mirror_room_puzzle.py)
└──────┬──────┘
       │ 完成谜题
       ▼
┌─────────────┐
│ Boss2战斗   │ (sloth_battle_scene.py)
│ The Sloth   │ 720HP, 3阶段
└──────┬──────┘
       │ 胜利后走到边缘
       ▼
┌─────────────┐
│ 画作房间    │ (painting_room_puzzle.py)
└──────┬──────┘
       │ 完成谜题
       ▼
┌─────────────┐
│ Boss3战斗   │ (boss_battle_scene.py)
│ The Hollow  │ 完整版最终BOSS
└──────┬──────┘
       │ 胜利后
       ▼
┌─────────────┐
│ 游戏结束    │ 恭喜通关！
└─────────────┘
```

---

## 🗂️ 核心文件映射

| 场景序号 | 场景名称 | 主文件 | 依赖文件 |
|---------|---------|--------|----------|
| 1 | 主菜单 | `combine/meun.py` | - |
| 2 | 解谜场景 | `testing/new_third_puzzle.py` | `src/tiled_loader.py` |
| 3 | 梦境解谜 | `testing/first_dream_puzzle.py` | 无 |
| 4 | 梦境过渡 | `testing/dream_transition_scene.py` | 无 |
| 5 | Boss1战斗 | `src/scenes/boss1_scripted_scene.py` | `src/entities/player.py`, `src/entities/bullets.py` |
| 6 | Map01探索 | `testing/map01_final.py` | `src/tiled_loader.py`, `src/entities/player_map.py` |
| 7 | 镜子房间 | `testing/mirror_room_puzzle.py` | 无 |
| 8 | Boss2战斗 | `src/entities/sloth_battle_scene.py` | `src/entities/boss_sloth.py`, `src/systems/ui.py` |
| 9 | 画作房间 | `testing/painting_room_puzzle.py` | 无 |
| 10 | Boss3战斗 | `src/entities/boss_battle_scene.py` | `src/entities/boss_the_hollow.py`, `src/systems/ui.py` |

---

## 🎯 当前开发状态

✅ **已完成**:
- 主菜单
- 解谜场景
- 梦境解谜（4个子谜题）
- 梦境过渡
- Boss1剧情战（含死亡过渡效果）
- Map01探索场景（横版平台）
- Boss2完整战斗（含蒲公英胜利过渡）
- Boss3完整战斗（含梦醒胜利过渡）
- 集中化UI系统
- 8-bit音效系统
- 二段跳机制
- 完整10场景游戏流程

🔄 **待完善**:
- 镜子房间谜题内容
- 画作房间谜题内容
- Map01与镜子房间的过渡衔接

📝 **待优化**:
- 跨平台兼容性（sprite加载、音频播放）
- 关卡间过渡动画更流畅
- 存档系统

---

## 💡 设计理念

游戏通过**谜题 → 探索 → boss战**的循环设计，将心理主题具象化：

1. **解谜场景** = 探索内心困惑
2. **梦境场景** = 潜意识探索
3. **Map01探索** = 现实世界的行动
4. **Boss战斗** = 对抗心理障碍
   - Boss1 (The Hollow Intro) = 初遇虚无，无力反抗
   - Boss2 (The Sloth) = 对抗拖延症
   - Boss3 (The Hollow Final) = 战胜虚无主义

每个boss都有独特的**视觉主题、攻击模式、胜利过渡**，确保体验多样性。

---

## 🚀 快速启动指南

### 完整游戏流程
```bash
python testing/game_flow_manager.py
```

### 单独测试场景
```bash
# Boss战斗
python main.py boss1
python main.py boss2
python main.py boss3

# 探索场景
python testing/map01_final.py

# 谜题场景
python testing/new_third_puzzle.py
python testing/first_dream_puzzle.py
python testing/mirror_room_puzzle.py
python testing/painting_room_puzzle.py
```
