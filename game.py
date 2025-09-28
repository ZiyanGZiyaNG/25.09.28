import pygame
import random
import math
import os

# Initialize Pygame
pygame.init()

# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Bullet Hell Shooter")

# Load player and enemy images
try:
    player_img = pygame.image.load(os.path.join(os.path.dirname(__file__), "我方飛船.png")).convert_alpha()
    player_img = pygame.transform.scale(player_img, (50, 50))
except:
    print("無法載入玩家飛船圖片，使用藍色方塊")
    player_img = None

try:
    enemy_img = pygame.image.load(os.path.join(os.path.dirname(__file__), "敵方飛船.png")).convert_alpha()
    enemy_img = pygame.transform.scale(enemy_img, (40, 40))
except:
    print("無法載入敵方飛船圖片，使用紅色方塊")
    enemy_img = None

try:
    boss_img = pygame.image.load(os.path.join(os.path.dirname(__file__), "boss.png")).convert_alpha()
    boss_img = pygame.transform.scale(boss_img, (150, 150)) # 調整頭目圖片大小
except:
    print("無法載入頭目圖片，使用紫色方塊")
    boss_img = None

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)
PURPLE = (128, 0, 128) # 新增紫色用於頭目方塊

# Game states
GAME_STATE_PLAYING = 0
GAME_STATE_SKILL_SELECTION = 1
GAME_STATE_BOSS_FIGHT = 2 # 新增頭目戰狀態
GAME_STATE_BOSS_DEFEATED = 3 # 頭目被擊敗
GAME_STATE_PLAYER_DEFEATED = 4 # 玩家生命歸零

# Game settings
INITIAL_ENEMY_COUNT = 8
ENEMY_SPAWN_INTERVAL = 2000  # Initial enemy spawn interval (ms)
MIN_ENEMY_SPAWN_INTERVAL = 500  # Minimum enemy spawn interval (ms)
DIFFICULTY_INCREASE_INTERVAL = 10000  # Difficulty increase interval (ms)
SCORE_FOR_UPGRADE = 100  # Score needed for weapon upgrade
SCORE_FOR_LIFE = 500  # Score needed for extra life
SCORE_FOR_WINGMAN = 1000 # Score needed for an extra wingman
MAX_WINGMEN = 3 # Maximum number of wingmen
SCORE_FOR_SKILL = 3000 # Score needed to trigger skill selection
MAX_PLAYER_BULLETS_PER_SHOT = 5 # Maximum bullets player can fire per shot
MAX_WEAPON_LEVEL = 10 # Overall max weapon level (player + wingmen firepower)
INVINCIBLE_TIME = 5000  # Invincible time after hit (ms)
FLASH_INTERVAL = 100  # Flash interval during invincible time (ms)
SHIELD_DURATION = 10000 # Duration of shield skill (ms)
SPLIT_SHOT_DURATION = 10000 # Duration of split shot skill (ms)
FIREBALL_COOLDOWN = 3000 # Cooldown for fireball spawn (ms)
BOUNCING_BALL_GEN_INTERVAL = 30000 # Interval for generating bouncing balls (ms)
MAX_BOUNCING_BALLS = 5 # Maximum number of bouncing balls
DRONE_COUNT = 3 # Number of drones to spawn
DRONE_RADIUS = 70 # Radius of drone orbit
DRONE_ORBIT_SPEED = 0.05 # Speed of drone orbit (radians per frame)
DRONE_SHOOT_COOLDOWN = 500 # Cooldown for drone shooting (ms)
ELECTROMAGNETIC_RADIUS = 100 # Radius for chain lightning effect
BOSS_FIGHT_SCORE_THRESHOLD = 100000 # Score to trigger boss fight

# Bullet offsets for player and wingmen
PLAYER_BULLET_OFFSETS = {
    1: [0],
    2: [-10, 10],
    3: [-15, 0, 15],
    4: [-20, -7, 7, 20],
    5: [-25, -12, 0, 12, 25]
}

WINGMAN_BULLET_OFFSETS = {
    1: [0],
    2: [-5, 5],
    3: [-10, 0, 10]
}

BOSS_BULLET_OFFSETS = {
    1: [0],
    2: [-20, 20],
    3: [-30, 0, 30],
    4: [-40, -15, 15, 40],
    5: [-50, -25, 0, 25, 50]
}

# Skill definitions
SKILLS = {
    "Fireball": "Fireball (randomly spawns on screen every few seconds)",
    "Split Shot": "Split Shot (player bullets split, lasts 10s)",
    "Bouncing Ball": "Bouncing Ball (max 5, one generated every 30s)",
    "Drone": "Drone (shoots in a circle)",
    "Shield": "Shield (player invincible, lasts 10s)",
    "Electromagnetic Wave": "Electromagnetic Wave (bullets with chain lightning)"
}

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        if player_img:
            self.image = player_img
        else:
            self.image = pygame.Surface((50, 50))
            self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.centerx = WINDOW_WIDTH // 2
        self.rect.bottom = WINDOW_HEIGHT - 10
        self.speed = 5
        self.lives = 3
        self.weapon_level = 1
        self.shoot_delay = 200  # 改為 200 毫秒（每秒 5 次）
        self.last_shot = 0
        self.is_invincible = False
        self.invincible_start_time = 0
        self.is_visible = True
        self.last_flash_time = 0
        self.wingmen = pygame.sprite.Group()
        self.has_split_shot = False
        self.split_shot_end_time = 0
        self.has_electromagnetic_wave = False
        self.drones = pygame.sprite.Group()

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WINDOW_WIDTH:
            self.rect.x += self.speed

        current_time = pygame.time.get_ticks()

        # 自動射擊
        self.shoot(current_time)

        # Handle invincibility and flashing
        if self.is_invincible:
            if current_time - self.invincible_start_time > INVINCIBLE_TIME:
                self.is_invincible = False
                self.is_visible = True
            else:
                # Flash effect
                if current_time - self.last_flash_time > FLASH_INTERVAL:
                    self.is_visible = not self.is_visible
                    self.last_flash_time = current_time
        
        # Handle split shot duration
        if self.has_split_shot and current_time > self.split_shot_end_time:
            self.has_split_shot = False

        # Update wingmen positions
        if len(self.wingmen) == 1:
            wingman = self.wingmen.sprites()[0]
            wingman.rect.centerx = self.rect.centerx - 40  # Position to the left
            wingman.rect.centery = self.rect.centery
        elif len(self.wingmen) == 2:
            wingmen_list = self.wingmen.sprites()
            wingmen_list[0].rect.centerx = self.rect.centerx - 40
            wingmen_list[0].rect.centery = self.rect.centery
            wingmen_list[1].rect.centerx = self.rect.centerx + 40
            wingmen_list[1].rect.centery = self.rect.centery
        elif len(self.wingmen) == 3:
            wingmen_list = self.wingmen.sprites()
            wingmen_list[0].rect.centerx = self.rect.centerx - 60
            wingmen_list[0].rect.centery = self.rect.centery
            wingmen_list[1].rect.centerx = self.rect.centerx
            wingmen_list[1].rect.centery = self.rect.centery - 40 # Behind player
            wingmen_list[2].rect.centerx = self.rect.centerx + 60
            wingmen_list[2].rect.centery = self.rect.centery

    def shoot(self, current_time):
        if current_time - self.last_shot > self.shoot_delay:
            # Player's bullets
            player_bullets_count = min(self.weapon_level, MAX_PLAYER_BULLETS_PER_SHOT)
            offsets = PLAYER_BULLET_OFFSETS.get(player_bullets_count, [0])
            for offset in offsets:
                bullet = Bullet(self.rect.centerx + offset, self.rect.top, is_electromagnetic=self.has_electromagnetic_wave)
                all_sprites.add(bullet)
                bullets.add(bullet)
                if self.has_split_shot: # Apply split shot effect
                    split_bullet1 = Bullet(self.rect.centerx + offset - 5, self.rect.top, speed=-8, angle=-0.2, is_electromagnetic=self.has_electromagnetic_wave)
                    split_bullet2 = Bullet(self.rect.centerx + offset + 5, self.rect.top, speed=-8, angle=0.2, is_electromagnetic=self.has_electromagnetic_wave)
                    all_sprites.add(split_bullet1, split_bullet2)
                    bullets.add(split_bullet1, split_bullet2)

            self.last_shot = current_time

            # Distribute excess firepower to wingmen
            excess_firepower = max(0, self.weapon_level - MAX_PLAYER_BULLETS_PER_SHOT)
            wingmen_list = self.wingmen.sprites()

            if wingmen_list and excess_firepower > 0:
                bullets_per_wingman_base = excess_firepower // len(wingmen_list)
                remaining_bullets = excess_firepower % len(wingmen_list)

                for i, wingman in enumerate(wingmen_list):
                    wingman_bullets_to_fire = bullets_per_wingman_base
                    if i < remaining_bullets:
                        wingman_bullets_to_fire += 1
                    
                    if wingman_bullets_to_fire > 0:
                        wingman.shoot_bullet(wingman_bullets_to_fire)

    def upgrade_weapon(self):
        if self.weapon_level < MAX_WEAPON_LEVEL:  # Max weapon level is now higher
            self.weapon_level += 1
            self.shoot_delay = max(100, self.shoot_delay - 20)  # 每次升級減少 20 毫秒，但最低不低於 100 毫秒

    def take_damage(self):
        if not self.is_invincible:
            self.lives -= 1
            self.is_invincible = True
            self.invincible_start_time = pygame.time.get_ticks()
            return True
        return False

    def add_life(self):
        self.lives += 1

    def add_wingman(self):
        if len(self.wingmen) < MAX_WINGMEN: # Limit wingmen by MAX_WINGMEN
            wingman = Wingman(self.rect.centerx, self.rect.centery, 0) # Pass player_img here
            all_sprites.add(wingman)
            self.wingmen.add(wingman)

    def activate_shield(self):
        self.is_invincible = True
        self.invincible_start_time = pygame.time.get_ticks() - (INVINCIBLE_TIME - SHIELD_DURATION) # Make it last longer

    def activate_split_shot(self):
        self.has_split_shot = True
        self.split_shot_end_time = pygame.time.get_ticks() + SPLIT_SHOT_DURATION

    def activate_drone(self):
        for i in range(DRONE_COUNT):
            drone = Drone(self)
            all_sprites.add(drone)
            self.drones.add(drone)
    
    def activate_electromagnetic_wave(self):
        self.has_electromagnetic_wave = True


# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=-10, angle=0, is_electromagnetic=False):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        if is_electromagnetic:
            self.image.fill(BLUE) # 電磁波子彈為藍色
        else:
            self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = speed
        self.angle = angle
        self.is_electromagnetic = is_electromagnetic

    def update(self):
        self.rect.y += self.speed * math.cos(self.angle)
        self.rect.x += self.speed * math.sin(self.angle)
        if self.rect.bottom < 0 or self.rect.top > WINDOW_HEIGHT or self.rect.left > WINDOW_WIDTH or self.rect.right < 0:
            self.kill()

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        if enemy_img:
            self.image = enemy_img
        else:
            self.image = pygame.Surface((30, 30))
            self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WINDOW_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randrange(1, 4)
        self.speedx = random.randrange(-2, 2)

    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if self.rect.top > WINDOW_HEIGHT or self.rect.left < -25 or self.rect.right > WINDOW_WIDTH + 25:
            self.rect.x = random.randrange(WINDOW_WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 4)

# Boss class
class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        if boss_img:
            self.image = boss_img
        else:
            self.image = pygame.Surface((150, 150))
            self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.rect.centerx = WINDOW_WIDTH // 2
        self.rect.top = 50 # Start near the top of the screen
        self.health = 500000 # 500,000 bullet hits
        self.speed_x = 2
        self.shoot_delay = 500 # Boss shoots every 500 ms
        self.last_shot = 0
        self.bullet_level = 1 # Boss's initial bullet level

    def update(self):
        self.rect.x += self.speed_x
        # Bounce off walls
        if self.rect.left < 0 or self.rect.right > WINDOW_WIDTH:
            self.speed_x *= -1

        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = current_time

    def shoot(self):
        # Boss shoots multiple bullets downwards based on bullet_level
        bullets_to_fire = self.bullet_level # Number of bullets to fire per shot
        offsets = BOSS_BULLET_OFFSETS.get(bullets_to_fire, [0]) # Get offsets based on bullet level
        for offset in offsets:
            bullet = Bullet(self.rect.centerx + offset, self.rect.bottom, speed=7) # Boss bullets move downwards
            all_sprites.add(bullet)
            boss_bullets.add(bullet)

    def take_damage(self, damage):
        self.health -= damage
        
        # Upgrade boss bullet level based on health
        if self.health <= 100000 and self.bullet_level < 5:
            self.bullet_level = 5
        elif self.health <= 200000 and self.bullet_level < 4:
            self.bullet_level = 4
        elif self.health <= 300000 and self.bullet_level < 3:
            self.bullet_level = 3
        elif self.health <= 400000 and self.bullet_level < 2:
            self.bullet_level = 2

        if self.health <= 0:
            self.kill()
            return True
        return False

# Wingman class
class Wingman(pygame.sprite.Sprite):
    def __init__(self, x, y, offset_x):
        super().__init__()
        self.width = 40
        self.height = 40
        self.speed = 5
        self.last_shot = 0
        self.shoot_delay = 200  # 與玩家相同的射擊延遲
        self.offset_x = offset_x
        
        # 載入僚機圖片
        try:
            self.image = pygame.image.load(os.path.join(os.path.dirname(__file__), "僚機.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except:
            print("無法載入僚機圖片，使用白色方塊")
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(WHITE)
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

    def update(self):
        # 僚機的位置由 Player 類別統一管理，因此這裡移除自動定位
        # 自動射擊邏輯由 Player.shoot 統一觸發，這裡移除僚機自身的自動射擊
        pass

    def shoot_bullet(self, bullet_count):
        # bullet_count 現在由 Player.shoot 方法傳遞
        if bullet_count > 0:
            offsets = WINGMAN_BULLET_OFFSETS.get(bullet_count, [0])
            for offset in offsets:
                bullet = Bullet(self.rect.centerx + offset, self.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)

# Fireball class
class Fireball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(ORANGE)
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(0, WINDOW_WIDTH - self.rect.width)
        self.rect.y = 0 # Start from top
        self.speed = random.randrange(3, 7)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()

# Bouncing Ball class
class BouncingBall(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 載入彈球圖片
        try:
            self.image = pygame.image.load(os.path.join(os.path.dirname(__file__), "彈球.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (15, 15))
        except:
            print("無法載入彈球圖片，使用黃色方塊")
            self.image = pygame.Surface((15, 15))
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (random.randrange(50, WINDOW_WIDTH - 50), random.randrange(50, WINDOW_HEIGHT - 50))
        self.speed_x = random.choice([-3, 3])
        self.speed_y = random.choice([-3, 3])

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Bounce off walls
        if self.rect.left < 0 or self.rect.right > WINDOW_WIDTH:
            self.speed_x *= -1
        if self.rect.top < 0 or self.rect.bottom > WINDOW_HEIGHT:
            self.speed_y *= -1

# Drone class
class Drone(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        # 載入無人機圖片
        try:
            self.image = pygame.image.load(os.path.join(os.path.dirname(__file__), "無人機.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (20, 20)) # 調整無人機大小
        except:
            print("無法載入無人機圖片，使用青色方塊")
            self.image = pygame.Surface((10, 10))
            self.image.fill(CYAN) # Cyan color for drone
        self.rect = self.image.get_rect()
        self.player = player
        self.angle = random.uniform(0, 2 * math.pi) # Initial random angle
        self.last_shot = 0

    def update(self):
        self.angle += DRONE_ORBIT_SPEED
        self.rect.centerx = self.player.rect.centerx + DRONE_RADIUS * math.cos(self.angle)
        self.rect.centery = self.player.rect.centery + DRONE_RADIUS * math.sin(self.angle)

        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > DRONE_SHOOT_COOLDOWN:
            bullet = Bullet(self.rect.centerx, self.rect.top, speed=-7) # Drones shoot straight up
            all_sprites.add(bullet)
            bullets.add(bullet)
            self.last_shot = current_time

# Button class for UI
class Button():
    def __init__(self, color, x, y, width, height, text='', text_color=WHITE):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.text_color = text_color
        self.font = pygame.font.Font(None, 30)

    def draw(self, screen, outline=None):
        # Call this method to draw the button on the screen
        if outline:
            pygame.draw.rect(screen, outline, (self.x-2,self.y-2,self.width+4,self.height+4),0)
            
        pygame.draw.rect(screen, self.color, (self.x,self.y,self.width,self.height),0)
        
        if self.text != '':
            text_surface = self.font.render(self.text, 1, self.text_color)
            screen.blit(text_surface, (self.x + (self.width/2 - text_surface.get_width()/2), self.y + (self.height/2 - text_surface.get_height()/2)))

    def is_over(self, pos):
        print(f"Checking if mouse at {pos} is over button at ({self.x}, {self.y}, {self.width}, {self.height})") # Added for debugging
        # Pos is the mouse position or a tuple of (x,y) coordinates
        if pos[0] > self.x and pos[0] < self.x + self.width:
            if pos[1] > self.y and pos[1] < self.y + self.height:
                print("Mouse is over button!") # Added for debugging
                return True
        return False


# Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
fireballs = pygame.sprite.Group() # New group for fireballs
bouncing_balls = pygame.sprite.Group() # New group for bouncing balls
drones = pygame.sprite.Group() # New group for drones
boss_bullets = pygame.sprite.Group() # New group for boss bullets
boss_group = pygame.sprite.Group() # New group for the boss

# Create player
player = Player()
all_sprites.add(player)

# Create initial enemies
for i in range(INITIAL_ENEMY_COUNT):
    enemy = Enemy()
    all_sprites.add(enemy)
    enemies.add(enemy)

# Game variables
score = 0
font = pygame.font.Font(None, 36)
game_time = 0
last_enemy_spawn = 0
enemy_spawn_interval = ENEMY_SPAWN_INTERVAL
last_difficulty_increase = 0
next_upgrade_score = SCORE_FOR_UPGRADE
next_life_score = SCORE_FOR_LIFE
next_wingman_score = SCORE_FOR_WINGMAN
next_skill_score = SCORE_FOR_SKILL
game_state = GAME_STATE_PLAYING
skill_options_display = []
skill_buttons = [] # New list to store skill buttons
last_fireball_spawn = 0
last_bouncing_ball_gen = 0
boss = None # Initialize boss as None


# Game main loop
running = True
clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()

while running:
    # Calculate game time
    current_time = pygame.time.get_ticks()
    game_time = current_time - start_time
    
    # Control game speed (always tick to ensure events are processed)
    clock.tick(60)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_state == GAME_STATE_PLAYING or game_state == GAME_STATE_BOSS_FIGHT: # 允許在頭目戰中移動
                if event.key == pygame.K_LEFT:
                    player.rect.x -= player.speed
                if event.key == pygame.K_RIGHT:
                    player.rect.x += player.speed
                # 自動射擊現在由 Player.update() 處理，不需要 K_SPACE
        elif event.type == pygame.MOUSEBUTTONDOWN: # Handle mouse clicks
            print(f"Mouse clicked at: {event.pos}") # Added for debugging
            if game_state == GAME_STATE_SKILL_SELECTION:
                for i, button in enumerate(skill_buttons):
                    if button.is_over(event.pos):
                        selected_skill = skill_options_display[i]
                        if selected_skill == "Shield":
                            player.activate_shield()
                        elif selected_skill == "Split Shot":
                            player.activate_split_shot()
                        elif selected_skill == "Fireball":
                            pass # Fireball is passive, no direct activation, but we still need to select it
                        elif selected_skill == "Bouncing Ball":
                            pass # Bouncing Ball is passive, no direct activation
                        elif selected_skill == "Drone":
                            player.activate_drone()
                        elif selected_skill == "Electromagnetic Wave":
                            player.activate_electromagnetic_wave()
                        game_state = GAME_STATE_PLAYING
                        skill_buttons = [] # Clear buttons after selection
                        break

    # Game logic update
    if game_state == GAME_STATE_PLAYING:
        # Check for boss fight trigger
        if score >= BOSS_FIGHT_SCORE_THRESHOLD and len(boss_group) == 0:
            game_state = GAME_STATE_BOSS_FIGHT
            # Clear all enemies and bullets
            for enemy in enemies:
                enemy.kill()
            for bullet in bullets:
                bullet.kill()
            for fireball in fireballs:
                fireball.kill()
            for bouncing_ball in bouncing_balls:
                bouncing_ball.kill()
            
            # Spawn the boss
            boss = Boss()
            all_sprites.add(boss)
            boss_group.add(boss)

        # Spawn new enemies based on time
        if current_time - last_enemy_spawn > enemy_spawn_interval:
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)
            last_enemy_spawn = current_time

        # Increase difficulty over time
        if current_time - last_difficulty_increase > DIFFICULTY_INCREASE_INTERVAL:
            enemy_spawn_interval = max(MIN_ENEMY_SPAWN_INTERVAL, 
                                     enemy_spawn_interval - 100)
            last_difficulty_increase = current_time

        # Spawn fireballs (passive skill)
        if "Fireball" in skill_options_display and current_time - last_fireball_spawn > FIREBALL_COOLDOWN:
            fireball = Fireball()
            all_sprites.add(fireball)
            fireballs.add(fireball)
            last_fireball_spawn = current_time

        # Generate bouncing balls (passive skill)
        if "Bouncing Ball" in skill_options_display and current_time - last_bouncing_ball_gen > BOUNCING_BALL_GEN_INTERVAL and len(bouncing_balls) < MAX_BOUNCING_BALLS:
            bouncing_ball = BouncingBall()
            all_sprites.add(bouncing_ball)
            bouncing_balls.add(bouncing_ball)
            last_bouncing_ball_gen = current_time


        # Update game
        all_sprites.update()

        # Debugging: print sprite counts at intervals
        if current_time % 1000 < 50: # 每秒列印一次
            print(f"Score: {score}, Enemies: {len(enemies)}, Bullets: {len(bullets)}, Fireballs: {len(fireballs)}, Bouncing Balls: {len(bouncing_balls)}, Drones: {len(player.drones)}")

        # Check bullet and enemy collisions
        hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
        for hit_enemy, hit_bullets in hits.items():
            score += 10
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)
            
            # Check for electromagnetic wave effect
            for bullet_hit in hit_bullets:
                if bullet_hit.is_electromagnetic:
                    enemies_to_kill = []
                    for other_enemy in enemies:
                        distance = math.hypot(hit_enemy.rect.centerx - other_enemy.rect.centerx,
                                              hit_enemy.rect.centery - other_enemy.rect.centery)
                        if distance < ELECTROMAGNETIC_RADIUS:
                            enemies_to_kill.append(other_enemy)
                    
                    for killed_enemy in enemies_to_kill:
                        killed_enemy.kill()
                        score += 10 # Grant score for chain kill
                        new_enemy = Enemy() # Spawn new enemy
                        all_sprites.add(new_enemy)
                        enemies.add(new_enemy)

            # Check for weapon upgrade
            if score >= next_upgrade_score:
                player.upgrade_weapon()
                next_upgrade_score += SCORE_FOR_UPGRADE

            # Check for extra life
            if score >= next_life_score:
                player.add_life()
                next_life_score += SCORE_FOR_LIFE

            # Check for wingman
            if score >= next_wingman_score:
                player.add_wingman()
                next_wingman_score += SCORE_FOR_WINGMAN

            # Check for skill trigger
            if score >= next_skill_score:
                game_state = GAME_STATE_SKILL_SELECTION
                skill_options_display = random.sample(list(SKILLS.keys()), 3)
                # Create buttons for skill selection
                skill_buttons = []
                button_width = 400
                button_height = 50
                button_start_y = WINDOW_HEIGHT // 2 - 50 # Adjust vertical position
                for i, skill_name in enumerate(skill_options_display):
                    button_y = button_start_y + i * (button_height + 10) # 10 pixels padding
                    button = Button(DARK_GRAY, WINDOW_WIDTH // 2 - button_width // 2, button_y, button_width, button_height, f"{i+1}. {SKILLS[skill_name]}", WHITE)
                    skill_buttons.append(button)
                next_skill_score += SCORE_FOR_SKILL # Prepare for next skill trigger

        # Check fireball and enemy collisions
        hits = pygame.sprite.groupcollide(enemies, fireballs, True, True)
        for hit in hits:
            score += 10
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)
        
        # Check bouncing ball and enemy collisions
        hits = pygame.sprite.groupcollide(enemies, bouncing_balls, True, False) # Bouncing ball does not get killed
        for hit in hits:
            score += 10
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)
        
        # Check drone bullets and enemy collisions
        hits = pygame.sprite.groupcollide(enemies, player.drones, True, False) # Drones hit enemies
        for hit in hits:
            score += 10
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)

        # Check player and enemy collisions
        hits = pygame.sprite.spritecollide(player, enemies, True)
        for hit in hits:
            if player.take_damage():
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
                if player.lives <= 0:
                    game_state = GAME_STATE_PLAYER_DEFEATED # 玩家生命歸零，進入失敗狀態

    elif game_state == GAME_STATE_BOSS_FIGHT: # Boss fight logic
        all_sprites.update() # Update all sprites, including player, boss, bullets

        # Player bullets hit boss
        hits = pygame.sprite.groupcollide(boss_group, bullets, False, True) # Boss doesn't get killed, only takes damage
        for boss_hit, hit_bullets in hits.items():
            for bullet_hit in hit_bullets:
                if boss_hit.take_damage(1): # Each bullet deals 1 damage
                    game_state = GAME_STATE_BOSS_DEFEATED # Boss defeated
                    print("END GAME GG!")
                    # Clear all remaining sprites for smooth end game transition
                    for sprite in all_sprites:
                        sprite.kill()
                    break
            if game_state == GAME_STATE_BOSS_DEFEATED: # If boss was defeated, break outer loop
                break

        # Boss bullets hit player
        hits = pygame.sprite.spritecollide(player, boss_bullets, True) # Boss bullets get killed
        for hit in hits:
            if player.take_damage():
                if player.lives <= 0:
                    game_state = GAME_STATE_PLAYER_DEFEATED # 玩家生命歸零，進入失敗狀態

    # Draw
    screen.fill(BLACK)
    
    if game_state in [GAME_STATE_PLAYING, GAME_STATE_BOSS_FIGHT, GAME_STATE_SKILL_SELECTION]:
        # Draw all sprites except player, wingmen and drones
        for sprite in all_sprites:
            if sprite != player and not isinstance(sprite, Wingman) and not isinstance(sprite, Drone):
                screen.blit(sprite.image, sprite.rect)
        
        # Draw player only if visible
        if player.is_visible:
            screen.blit(player.image, player.rect)

        # Draw wingmen
        for wingman in player.wingmen:
            screen.blit(wingman.image, wingman.rect)

        # Draw drones
        for drone in player.drones:
            screen.blit(drone.image, drone.rect)
        
        # Display score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Display lives
        lives_text = font.render(f"Lives: {player.lives}", True, WHITE)
        screen.blit(lives_text, (10, 50))

        # Display game time
        time_text = font.render(f"Time: {game_time//1000}s", True, WHITE)
        screen.blit(time_text, (10, 90))

        # Display enemy count (or boss health)
        if game_state == GAME_STATE_PLAYING:
            enemy_count_text = font.render(f"Enemies: {len(enemies)}", True, WHITE)
            screen.blit(enemy_count_text, (10, 130))
        elif game_state == GAME_STATE_BOSS_FIGHT and boss:
            boss_health_text = font.render(f"Boss Health: {boss.health}", True, RED)
            screen.blit(boss_health_text, (WINDOW_WIDTH // 2 - boss_health_text.get_width() // 2, 10))

        # Display weapon level
        weapon_text = font.render(f"Weapon Level: {player.weapon_level}", True, YELLOW)
        screen.blit(weapon_text, (10, 170))

        # Display next upgrade score
        upgrade_text = font.render(f"Next Upgrade: {next_upgrade_score}", True, YELLOW)
        screen.blit(upgrade_text, (10, 210))

        # Display next life score
        life_text = font.render(f"Next Life: {next_life_score}", True, YELLOW)
        screen.blit(life_text, (10, 250))

        # Display wingman count
        wingman_count_text = font.render(f"Wingmen: {len(player.wingmen)}", True, YELLOW)
        screen.blit(wingman_count_text, (10, 290))

        # Display drone count
        drone_count_text = font.render(f"Drones: {len(player.drones)}", True, YELLOW)
        screen.blit(drone_count_text, (10, 330))

        # Display skill selection UI
        if game_state == GAME_STATE_SKILL_SELECTION:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            title_text = font.render("Choose a Skill:", True, GREEN)
            title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 150))
            screen.blit(title_text, title_rect)

            for button in skill_buttons:
                button.draw(screen, outline=LIGHT_GRAY)

    elif game_state == GAME_STATE_BOSS_DEFEATED:
        end_game_text = font.render("END GAME GG!", True, GREEN)
        end_game_rect = end_game_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        screen.blit(end_game_text, end_game_rect)

    elif game_state == GAME_STATE_PLAYER_DEFEATED:
        game_over_text = font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        screen.blit(game_over_text, game_over_rect)

    pygame.display.flip()

pygame.quit() 