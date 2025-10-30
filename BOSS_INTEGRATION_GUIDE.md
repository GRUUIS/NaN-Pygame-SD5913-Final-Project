# Boss Battle Integration - Usage Guide

## Overview
已成功重构entities文件夹，并将boss测试功能集成到main.py中。所有配置现在有效使用globals.py进行管理。

## 文件结构重构结果

### 清理后的 `src/entities/` 结构：
```
src/entities/
├── __init__.py          # 导出所有主要组件
├── boss_battle_scene.py # 完整的boss战斗场景
├── player.py           # 2D平台玩家类
├── boss.py             # Perfectionist boss与FSM状态机
├── bullets.py          # 子弹系统和管理器
└── platform.py         # 平台碰撞系统
```

### 增强的 `globals.py`：
- 屏幕配置 (分辨率、FPS)
- 物理常量 (重力、跳跃强度、移动速度)
- 玩家配置 (生命值、攻击冷却)
- Boss配置 (生命值、阶段攻击冷却、移动速度)
- 子弹配置 (速度、伤害)
- 颜色定义 (所有游戏元素的颜色)
- 游戏状态枚举
- 调试选项

## 游戏模式

### 1. 正常游戏模式
```bash
python main.py
```
启动标准游戏管理器

### 2. Boss战斗测试模式  
```bash
python main.py boss
# 或
python main.py test
```
直接进入boss战斗测试，包含：
- 完整的2D平台物理系统
- "泰拉瑞亚双子魔眼"风格的boss AI
- 多种子弹类型（普通、追踪、激光）
- 两阶段boss战斗机制

### 3. 帮助信息
```bash
python main.py help
```

## Boss战斗控制

### 玩家控制：
- **WASD**: 移动
- **空格**: 跳跃
- **鼠标**: 瞄准和射击
- **R**: 重置战斗
- **ESC**: 退出

### Boss AI特性：
- **阶段1**: 扇形射击、预测射击
- **阶段2** (50%生命值时): 追踪导弹、激光扫射
- FSM状态机控制行为切换
- 可视化攻击预告（闪烁效果）

## 技术特点

### 有效使用globals.py：
✅ 所有游戏常量集中管理  
✅ 颜色配置统一  
✅ 物理参数可调节  
✅ 调试选项控制  

### 模块化设计：
✅ 组件分离（player.py, boss.py, bullets.py, platform.py）  
✅ 清晰的导入结构  
✅ 避免循环导入  
