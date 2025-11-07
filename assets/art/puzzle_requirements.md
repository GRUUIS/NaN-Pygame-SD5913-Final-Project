美术&音效需求文档

以下为从 Excel 复制过来的资源清单，按模块（开场 / 解谜场景 / 战斗场景 / 角色&Boss / 子弹&特效 / 结局 / 音效）整理为 Markdown 表格。

## 基本信息

| 项目 | 值 |
|---|---|
| 游戏分辨率 | 1280×720 |
| 帧率 | 60 FPS |
| 字体 | Silver.ttf（免费资产：https://poppyworks.itch.io/silver） |

---

## 开场（UI）

| 文件名 | 类型 | 规格（预估） | 描述 | 备注 |
|---|---:|---:|---|---|
| title_screen.png | UI | 1280×720 | 游戏封面图 | 主界面背景 |
| title_logo.png | UI | 800×200 | 标题花字图 | 可加渐显或下移动效 |
| start_button.png | UI | 300×100 | “Start”按钮 | |
| exit_button.png | UI | 300×100 | “Exit”按钮 | |
| menu_cursor.png | UI | 64×64 | 光标图标 | |
| dialogue_box.png | UI | 1000×200 | 文本框底图 | |
| speech_bubble.png | UI | 300×150 | 对话气泡样式 | 角色对白用 |
| save_icon.png | UI | 64×64 | 存档图标 | 放入房间内可交互点 |
| save_point_light.png | 特效 | 256×256 | 存档完成视觉反馈 | 或者是颜色更改进行反馈 |

---

## 解谜场景（房间与可交互物）

| 文件名 | 类型 | 规格（预估） | 描述 | 备注 |
|---|---:|---:|---|---|
| room_state.png | 背景 | 1280×720 | 解谜场景基础背景 | 一切不可触发物品画在上面 |
| room_state_symmetry1.png | 背景 | 1280×720 | 第一幕镜像场景（初始） | 随角色右移显现，不可进入 |
| room_state_symmetry2.png | 背景 | 1280×720 | 第一幕镜像打破后变黑 | 可进入，主角需进入获取战斗道具 |
| closeup box.png | UI | 1000×500 | 检查道具的物品特写框 | |
| bed.png | 可交互物件 | 256×128 | 床（可检查） | 也可作为存档点？ |
| desk.png | 可交互物件 | 256×128 | 书桌（放置笔记本、画笔） | 解谜触发点 |
| desk_zoomin.png | 可交互物件_特写 | — | 书桌特写 | 解谜 |
| flashlight.png | 道具/特写 | — | 在书桌上，特写可见 | |
| oldphone.png | 道具 | — | 旧手机 | |
| bookshelf.png | 可交互物件 | 256×256 | 书架（隐藏道具） | 解谜触发点 |
| bookshelf_zoomin.png | 可交互物件_特写 | — | 书架特写 | 解谜 |
| mirror_stand.png | 可交互物件 | 256×256 | 镜面 | 另一边对称显示场景 |
| curtain.png | 可交互物件 | 256×512 | 窗帘（开合影响光线） | 光照变化特效 |
| clock.png | 可交互物件 | 128×256 | 墙上时钟 | 第二幕触发点 |
| clock_zoomin.png | 可交互物件_特写 | — | 时钟特写交互 | 解谜 |
| painting_broken.png | 静态物件 | 256×256 | 挂画 | 可覆盖隐藏道具 |
| rug.png | 静态物件 | 512×256 | 地毯 | 可覆盖隐藏道具 |
| door_wood.png | 交互物件 | 128×256 | 门（进入 boss） | 动画帧 4 帧 |
| bedside table.png | 道具 | — | 床头柜 | |

---

## 战斗场景（道具与战斗用资源）

| 文件名 | 类型 | 规格（预估） | 描述 | 备注 |
|---|---:|---:|---|---|
| item_brush.png | 交互物件 | 64×64 | 破损画笔图标 | 第一幕 |
| item_clock.png | 交互物件 | 64×64 | 时间发条图标 | 第二幕 |
| item_flame.png | 交互物件 | 64×64 | 虚空之火图标 | 第三幕 |
| item_zoom_brush.png | UI | 512×512 | 破损画笔特写 | 解谜成功时出现 |
| item_zoom_clock.png | UI | 512×512 | 时间发条特写 | 解谜成功时出现 |
| item_zoom_flame.png | UI | 512×512 | 虚空之火特写 | 解谜成功时出现 |
| item_overlay.png | UI | 1280×720 | 道具特写遮罩背景 | 半透明黑背景 |
| battle_arena1.png | 背景 | 1280×720 | 第一幕战斗地图 | Boss：Whisperer |
| battle_arena2.png | 背景 | 1280×720 | 第二幕战斗地图 | Boss：Sloth |
| battle_arena3.png | 背景 | 1280×720 | 第三幕战斗地图 | Boss：Hollow |

---

## 角色 & Boss（精灵表）

| 文件名 | 类型 | 规格（预估） | 描述 | 备注 |
|---|---:|---:|---|---|
| player_idle.png | sprite | 64×64 | 主角静止动画 | 四帧循环 |
| player_walk.png | sprite | 64×64 | 主角行走动画 | 八方向帧 |
| player_attack_brush.png | sprite | 64×64 | 第一幕攻击动画 | 破损画笔 |
| player_attack_clock.png | sprite | 64×64 | 第二幕攻击动画 | 时间发条 |
| player_attack_flame.png | sprite | 64×64 | 第三幕攻击动画 | 虚空之火 |
| boss_whisperer_walk.png | sprite | 128×128 | Boss 1 移动 | 由文字碎片组成 |
| boss_whisperer_attack.png | sprite | 128×128 | Boss 1 攻击动画 | 发射“ERROR”弹幕 |
| boss_sloth_walk.png | sprite | 128×128 | Boss 2 移动 | 蜗牛样体型，缓慢滑动 |
| boss_sloth_attack.png | sprite | 128×128 | Boss 2 攻击动画 | 吐出“时钟齿轮”弹幕 |
| boss_hollow_walk.png | sprite | 128×128 | Boss 3 移动 | 黑色人形剪影 |
| boss_hollow_attack.png | sprite | 128×128 | Boss 3 攻击动画 | 召唤虚无碎片 |

---

## 子弹 & 特效

| 文件名 | 类型 | 规格（预估） | 描述 | 备注 |
|---|---:|---:|---|---|
| bullet_error.png | 特效 | 32×32 | Boss1 子弹（ERROR字样） | 红色闪烁 |
| bullet_gear.png | 特效 | 32×32 | Boss2 子弹（旋转齿轮） | 金属质感 |
| bullet_void.png | 特效 | 32×32 | Boss3 子弹（黑色光球） | 残影拖尾 |
| brush_attack_fx.png | 特效 | 64×64 | 第一幕武器挥击特效 | 蓝色光线 |
| clock_attack_fx.png | 特效 | 64×64 | 第二幕武器攻击特效 | 时间波纹 |
| flame_attack_fx.png | 特效 | 64×64 | 第三幕武器攻击特效 | 火焰粒子 |

---

## 结局画面 & 按钮

| 文件名 | 类型 | 规格（预估） | 描述 | 备注 |
|---|---:|---:|---|---|
| ending_happy.png | 背景 | 1280×720 | Happy Ending 封面 | 明亮暖色调 |
| ending_bad.png | 背景 | 1280×720 | Bad Ending 封面 | 冷色低饱和度 |
| restart_button.png | UI | 300×100 | “Restart”按钮 | |
| quit_button.png | UI | 300×100 | “Quit”按钮 | |

---

## 音效清单

| 文件名 | 类型 | 描述 |
|---|---:|---|
| click.wav | 音效 | UI按钮点击 |
| door_open.wav | 音效 | 门打开音效 |
| puzzle_solve.wav | 音效 | 解谜成功音效 |
| item_get.wav | 音效 | 道具拾取音效 |
| attack.wav | 音效 | 玩家攻击音效 |
| hit.wav | 音效 | Boss受击音效 |
| death.wav | 音效 | 玩家死亡音效 |
| ambient_loop.ogg | 音效 | 房间场景BGM |
| boss_theme_1.ogg | 音效 | Boss战斗BGM |
| ending_theme.ogg | 音效 | 通关结局BGM |

---

如果需要我将这些文件以占位图或 metadata.json 示例生成到 `assets/` 下（便于开发先行集成），我可以继续创建占位 PNG 与示例 JSON，并提供一组 Git 提交命令帮助你将更改提交到指定分支。

请告诉我接下来要做哪一步：
- 生成占位资源（PNG + metadata）并写入仓库；或
- 仅保留文档并给出推送命令供你本地执行。
# 美术需求：解谜模块资源清单与说明

此文档面向美术人员，列出“解谜部分”（序幕 + 三幕）的所需美术资源、尺寸规范、动画标注与输出要求。请按下列规范交付 PNG / Aseprite 源文件与音效。

---

## 1. 项目总体风格与色调
- 风格：暗系手绘 / 半写实像素混合（可根据团队风格调整），推荐统一色调：褪色灰紫为主，虚空战斗使用深紫 + 冷蓝高光。
- 情绪：序幕与解谜环境偏抑郁、褪色；战斗/虚空使用高对比色与颗粒特效。

## 2. 分辨率、帧与图块规范
- 目标游戏窗口：1280x720（请按此 UI 比例设计）
- 主角与关键交互物建议帧格：32x48 或 48x48（保持整除）。若团队希望更细致可用 64x64。
- 道具图标：32x32 或 24x24（UI/快捷栏用）
- tiles / 地图切片：建议 tile size 32x32（与 Tiled 推荐一致）
- 动画导出：提供 Aseprite 源文件（*.aseprite）与导出 PNG spritesheet（grid），并导出 JSON 或说明帧序列。

## 3. 文件与文件夹约定（交付结构）
- assets/sprites/items/  -> 小道具、齿轮、发条、虚空之火等
- assets/sprites/props/  -> 房间道具（椅子、书桌、电脑、台灯、窗帘、播放机、书架）
- assets/sprites/ui/  -> 组合界面、槽位、高亮、手型光标、提示框底图
- assets/aseprite_sources/ -> 所有 *.aseprite 源文件
- assets/sfx/ -> 音效（ogg/wav）
- assets/tilemaps/ -> Tiled 导出的地图文件（.tmj）及 tileset 图像

每个导出的 PNG 请尽量使用相对路径且命名清晰，例如：
- `props/chair_left.png`
- `props/monitor_left_sheet.png`（若有动画）
- `items/gear_bronze.png`

## 4. 必要资源清单（按幕列出）

### 序幕（教学/房间）
- 房间背景（静态，分前景与远景）
- 床、窗帘（静态 + 打开动画帧）
- 书桌（静态）、断铅笔（道具）、笔记本（打开与关闭帧）
- 播放机（含音量按钮、开关图标）
- 鼠标悬停手型光标（ui/hand.png）

### 第1幕：完美房间（对称性解谜）
- 左/右 对称道具（成对）：椅子、显示器、铅笔/笔断、书架
- 镜面效果元素：镜中物体消失转化为箱子的过渡帧（建议 4~6 帧淡出并生成箱子）
- 破损画笔（拾取图标，32x32）与获取动画（小泡泡、光效）
- 胜利短音效（轻钢琴）与文字弹出气泡样式（UI）

### 第2幕：惰性拖延（齿轮组装）
- 播放机、台灯、窗帘 三个可激活物体的开/关/激活动画（每个 3~6 帧即可）
- 掉落齿轮：铜/银/金 三种齿轮图（32x32），并提供 4 帧小落下动画
- 组合界面资产：圆盘底图（1024x1024 可缩放），槽位高亮、齿轮插入动画帧（小弹簧动画）

### 第3幕：虚无感（投影合成）
- 手电筒（拆装电池前后两种外观）、台灯（无灯泡/有灯泡）、旧手机（关/开/充电动画）
- 投影滤镜与光束：多张半透明遮罩图（投射画笔、合影、锁链形状）
- 虚空之火特效：3~6 帧发光燃烧循环（颜色：淡紫到粉蓝）

### BOSS 战斗通用特效
- 文本碎片粒子（白色小字碎片纹理，4~8 帧）
- 粒子散开（淡蓝）
- 虚空碎片（黑方块）图案

## 5. 动画命名与 Aseprite 标注建议
- 每个动画用 tag 标注示例：`idle`, `walk`, `open`, `activate`, `drop`, `pickup`, `dissolve`。
- 在导出 PNG 时统一帧大小，并输出 `metadata.json`（简单的动画到帧范围映射），便于代码自动加载。

示例 metadata.json 项：
```
{
  "monitor_left_sheet.png": {"frame_w":64, "frame_h":64, "animations": {"idle":[0,3], "glitch":[4,7]}}
}
```

## 6. 特效与音效（交付规格）
- 音效格式：OGG（主要）或 WAV（备选），短音效 ≤ 2s；BGM 可为 10~30s loopable。
- 粒子贴图：建议导出为小图集（16x16 / 32x32）并附透明通道。

## 7. 可交付清单（交付版本要求）
每次迭代请至少包含：
- 对应幕的所有 PNG（spritesheets/单帧）、.aseprite 源文件、metadata.json
- 至少一段短音效（胜利/激活/失败）
- 资源路径应放在 `assets/` 下对应目录，且在 commit message 中注明

## 8. 备注与补充
- 若某资源暂不可用，请先提供占位图（透明背景的纯色矩形）并在交付说明里标注“占位”。
- 若需颜色样式参考，我可以把一份色板供美术参考（如需要请回复）。

---

如需我直接把这份文档生成到仓库的其它位置（例如 `docs/`），或额外生成 `metadata.json` 示例与 Tiled 小样图，请告诉我你要的路径与名称，我会继续创建文件。
