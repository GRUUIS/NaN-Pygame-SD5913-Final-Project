from PIL import Image, ImageDraw, ImageFont
import os

# Mapping of files to create: path -> (w,h,color, label)
files = {
    # UI / opening
    'assets/sprites/ui/title_screen.png': (1280,720,(50,50,120),'title_screen'),
    'assets/sprites/ui/title_logo.png': (800,200,(80,40,120),'title_logo'),
    'assets/sprites/ui/start_button.png': (300,100,(30,120,60),'start'),
    'assets/sprites/ui/exit_button.png': (300,100,(120,30,30),'exit'),
    'assets/sprites/ui/menu_cursor.png': (64,64,(200,200,50),'cursor'),
    'assets/sprites/ui/dialogue_box.png': (1000,200,(40,40,40),'dialogue'),
    'assets/sprites/ui/speech_bubble.png': (300,150,(220,220,220),'bubble'),
    'assets/sprites/ui/save_icon.png': (64,64,(200,120,40),'save'),
    'assets/sfx/save_point_light.png': (256,256,(255,200,100),'savefx'),

    # Room / interactables
    'assets/sprites/props/room_state.png': (1280,720,(30,30,50),'room'),
    'assets/sprites/props/room_state_symmetry1.png': (1280,720,(40,40,80),'sym1'),
    'assets/sprites/props/room_state_symmetry2.png': (1280,720,(10,10,20),'sym2'),
    'assets/sprites/ui/closeup_box.png': (1000,500,(60,60,60),'closeup'),
    'assets/sprites/props/bed.png': (256,128,(120,60,60),'bed'),
    'assets/sprites/props/desk.png': (256,128,(90,60,30),'desk'),
    'assets/sprites/props/desk_zoomin.png': (512,256,(110,80,40),'desk_zoom'),
    'assets/sprites/items/flashlight.png': (64,24,(200,200,80),'flash'),
    'assets/sprites/props/oldphone.png': (64,64,(80,80,100),'phone'),
    'assets/sprites/props/bookshelf.png': (256,256,(100,70,40),'bookshelf'),
    'assets/sprites/props/bookshelf_zoomin.png': (512,512,(120,90,50),'bookshelf_z'),
    'assets/sprites/props/mirror_stand.png': (256,256,(180,180,200),'mirror'),
    'assets/sprites/props/curtain.png': (256,512,(150,80,80),'curtain'),
    'assets/sprites/props/clock.png': (128,256,(80,80,120),'clock'),
    'assets/sprites/props/clock_zoomin.png': (256,256,(100,100,140),'clock_z'),
    'assets/sprites/props/painting_broken.png': (256,256,(140,60,60),'painting'),
    'assets/sprites/props/rug.png': (512,256,(120,30,60),'rug'),
    'assets/sprites/props/door_wood.png': (128,256,(90,50,30),'door'),
    'assets/sprites/props/bedside_table.png': (128,64,(100,60,40),'bedside'),

    # Items / battle
    'assets/sprites/items/item_brush.png': (64,64,(200,100,160),'brush'),
    'assets/sprites/items/item_clock.png': (64,64,(200,200,120),'clock_it'),
    'assets/sprites/items/item_flame.png': (64,64,(160,80,200),'flame'),
    'assets/sprites/ui/item_zoom_brush.png': (512,512,(220,160,200),'zoom_brush'),
    'assets/sprites/ui/item_zoom_clock.png': (512,512,(220,220,160),'zoom_clock'),
    'assets/sprites/ui/item_zoom_flame.png': (512,512,(200,160,220),'zoom_flame'),
    'assets/sprites/ui/item_overlay.png': (1280,720,(0,0,0,180),'overlay'),
    'assets/sprites/props/battle_arena1.png': (1280,720,(30,10,40),'arena1'),
    'assets/sprites/props/battle_arena2.png': (1280,720,(40,20,30),'arena2'),
    'assets/sprites/props/battle_arena3.png': (1280,720,(10,10,10),'arena3'),

    # Player and bosses
    'assets/sprites/player/player_idle.png': (64,64,(100,150,255),'p_idle'),
    'assets/sprites/player/player_walk.png': (64,64,(100,200,255),'p_walk'),
    'assets/sprites/player/player_attack_brush.png': (64,64,(180,120,200),'p_ab'),
    'assets/sprites/player/player_attack_clock.png': (64,64,(200,180,120),'p_ac'),
    'assets/sprites/player/player_attack_flame.png': (64,64,(200,120,180),'p_af'),
    'assets/sprites/boss/boss_whisperer_walk.png': (128,128,(220,220,220),'bw_walk'),
    'assets/sprites/boss/boss_whisperer_attack.png': (128,128,(240,200,200),'bw_atk'),
    'assets/sprites/boss/boss_sloth_walk.png': (128,128,(160,160,160),'bs_walk'),
    'assets/sprites/boss/boss_sloth_attack.png': (128,128,(170,170,200),'bs_atk'),
    'assets/sprites/boss/boss_hollow_walk.png': (128,128,(20,20,20),'bh_walk'),
    'assets/sprites/boss/boss_hollow_attack.png': (128,128,(40,40,40),'bh_atk'),

    # bullets & fx
    'assets/sprites/particles/bullet_error.png': (32,32,(200,60,60),'b_err'),
    'assets/sprites/particles/bullet_gear.png': (32,32,(200,180,60),'b_gear'),
    'assets/sprites/particles/bullet_void.png': (32,32,(30,30,60),'b_void'),
    'assets/sprites/particles/brush_attack_fx.png': (64,64,(100,180,240),'fx_brush'),
    'assets/sprites/particles/clock_attack_fx.png': (64,64,(200,200,120),'fx_clock'),
    'assets/sprites/particles/flame_attack_fx.png': (64,64,(240,120,60),'fx_flame'),

    # ending
    'assets/sprites/ui/ending_happy.png': (1280,720,(255,220,180),'happy'),
    'assets/sprites/ui/ending_bad.png': (1280,720,(120,140,160),'bad'),
    'assets/sprites/ui/restart_button.png': (300,100,(60,160,80),'restart'),
    'assets/sprites/ui/quit_button.png': (300,100,(160,60,60),'quit'),

    # sfx placeholders (we'll create tiny .wav placeholders as text files indicating placeholder)
    'assets/sfx/click.wav': (1,1,(0,0,0),'sfx_click'),
    'assets/sfx/door_open.wav': (1,1,(0,0,0),'sfx_door'),
    'assets/sfx/puzzle_solve.wav': (1,1,(0,0,0),'sfx_puzzle'),
    'assets/sfx/item_get.wav': (1,1,(0,0,0),'sfx_item'),
    'assets/sfx/attack.wav': (1,1,(0,0,0),'sfx_attack'),
    'assets/sfx/hit.wav': (1,1,(0,0,0),'sfx_hit'),
    'assets/sfx/death.wav': (1,1,(0,0,0),'sfx_death'),
    'assets/sfx/ambient_loop.ogg': (1,1,(0,0,0),'sfx_ambient'),
    'assets/sfx/boss_theme_1.ogg': (1,1,(0,0,0),'sfx_boss'),
    'assets/sfx/ending_theme.ogg': (1,1,(0,0,0),'sfx_end'),
}

os.makedirs('assets', exist_ok=True)
for p,(w,h,color,label) in files.items():
    dirp = os.path.dirname(p)
    if dirp and not os.path.exists(dirp):
        os.makedirs(dirp, exist_ok=True)
    # For small sfx placeholders, write a text file indicating placeholder
    if p.endswith('.wav') or p.endswith('.ogg'):
        # create a tiny text placeholder so devs know to replace
        with open(p + '.placeholder.txt','w',encoding='utf-8') as f:
            f.write('Placeholder for sound file: {}\nGenerate a real audio file and replace this placeholder.'.format(os.path.basename(p)))
        continue
    mode = 'RGBA' if len(color) == 4 else 'RGB'
    img = Image.new(mode, (w,h), color + (() if len(color)==3 else ()))
    draw = ImageDraw.Draw(img)
    # Draw label centered
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    text = label
    if font:
        try:
            # Pillow >=8
            bbox = draw.textbbox((0,0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except Exception:
            try:
                tw, th = font.getsize(text)
            except Exception:
                tw, th = (0,0)
        draw.text(((w-tw)/2,(h-th)/2), text, fill=(255,255,255), font=font)
    img.save(p)

print('Placeholders generated:')
for p in files.keys():
    print(' -',p)
print('\nNote: small audio placeholders are written as .placeholder.txt files. Replace with real audio files later.')
