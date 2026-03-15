import pygame, random, sys, math
from enum import Enum

pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Infinite Racing - Pro")
clock = pygame.time.Clock()
FPS = 60
# COLORS
WHITE, BLACK, RED, YELLOW, ORANGE, BLUE, GRAY, ROAD, GRASS = \
    (255,255,255),(0,0,0),(220,60,60),(255,220,0),(255,170,60),(80,160,255),(50,50,50),(60,60,65),(40,120,40)
ROAD_WIDTH, ROAD_X, LANES, LANE_W = 600, (WIDTH-600)//2, 5, 600//5
# GAME STATES - إضافة حالة الفوز
class State(Enum): MENU, PLAY, PAUSE, GAME_OVER, WIN = range(5)
# CAMERA
class Camera:
    def __init__(self): self.shake = 0
    def apply(self, y): return y + random.uniform(-self.shake, self.shake)
    def hit(self): self.shake = 10
    def update(self): self.shake *= 0.85
# ROAD
class Road:
    def __init__(self): self.parts = [i*120 for i in range(20)]
    def update(self, speed):
        for i in range(len(self.parts)): self.parts[i] += speed
        if self.parts[0] > HEIGHT:
            self.parts.pop(0)
            self.parts.append(self.parts[-1]-120)
    def draw(self, s, c):
        pygame.draw.rect(s, GRASS, (0,0,ROAD_X,HEIGHT))
        pygame.draw.rect(s, GRASS, (ROAD_X+ROAD_WIDTH,0,WIDTH,HEIGHT))
        for y in self.parts:
            yy = c.apply(y)
            pygame.draw.rect(s, ROAD, (ROAD_X, yy, ROAD_WIDTH, 120))
            for i in range(1, LANES):
                x = ROAD_X + i*LANE_W
                pygame.draw.rect(s, YELLOW, (x-2, yy+40, 4, 40))
# PLAYER
class Player:
    def __init__(self):
        self.x,self.y,self.speed,self.max_speed,self.acc = WIDTH//2, HEIGHT-140, 0, 28, 0.5
        self.turn, self.score, self.coins, self.lives, self.level = 6, 0, 0, 3, 1
        self.invincible, self.speed_boost, self.magnet, self.combo, self.combo_timer = 0, 0, 0, 0, 0
    def update(self, keys):
        self.speed = min(self.speed+self.acc, self.max_speed + (10 if self.speed_boost>0 else 0)) if keys[pygame.K_UP] else self.speed*0.97
        if keys[pygame.K_LEFT]: self.x -= self.turn
        if keys[pygame.K_RIGHT]: self.x += self.turn
        self.x = max(ROAD_X+30, min(self.x, ROAD_X+ROAD_WIDTH-30))
        self.score += 1*(1+(self.level-1)*0.2)
        if self.invincible>0: self.invincible -= 1
        if self.speed_boost>0: self.speed_boost -= 1
        if self.magnet>0: self.magnet -= 1
        if self.combo_timer>0: self.combo_timer -= 1
        else: self.combo=0
    def draw(self,s):
        # رسم سيارة اللاعب بشكل مفصل
        car_width, car_height = 50, 100
        
        # جسم السيارة الرئيسي
        pygame.draw.rect(s, RED, (self.x-car_width//2, self.y-car_height//2, car_width, car_height), border_radius=10)
        
        # السقف
        roof_width, roof_height = car_width-10, car_height//2
        pygame.draw.rect(s, RED, (self.x-roof_width//2, self.y-car_height//2+10, roof_width, roof_height), border_radius=8)
        
        # النوافذ
        window_color = (150, 200, 255)  # لون أزرق فاتح للنوافذ
        pygame.draw.rect(s, window_color, (self.x-roof_width//2+5, self.y-car_height//2+15, roof_width-10, 15), border_radius=3)
        pygame.draw.rect(s, window_color, (self.x-roof_width//2+5, self.y-car_height//2+35, roof_width-10, 15), border_radius=3)
        
        # الأضواء الأمامية
        pygame.draw.circle(s, WHITE, (self.x-car_width//4, self.y+car_height//2-5), 5)
        pygame.draw.circle(s, WHITE, (self.x+car_width//4, self.y+car_height//2-5), 5)
        
        # الأضواء الخلفية
        pygame.draw.circle(s, (255, 100, 100), (self.x-car_width//4, self.y-car_height//2+5), 5)
        pygame.draw.circle(s, (255, 100, 100), (self.x+car_width//4, self.y-car_height//2+5), 5)
        
        # العجلات
        wheel_color = BLACK
        wheel_width, wheel_height = 8, 15
        pygame.draw.rect(s, wheel_color, (self.x-car_width//2-5, self.y-car_height//3, wheel_width, wheel_height), border_radius=3)
        pygame.draw.rect(s, wheel_color, (self.x+car_width//2-3, self.y-car_height//3, wheel_width, wheel_height), border_radius=3)
        pygame.draw.rect(s, wheel_color, (self.x-car_width//2-5, self.y+car_height//3-wheel_height, wheel_width, wheel_height), border_radius=3)
        pygame.draw.rect(s, wheel_color, (self.x+car_width//2-3, self.y+car_height//3-wheel_height, wheel_width, wheel_height), border_radius=3)
        
    def rect(self): return pygame.Rect(self.x-25,self.y-50,50,100)
# AI CARS
class AICar:
    def __init__(self, level=1):
        self.lane = random.randint(0, LANES-1)
        self.x = ROAD_X + self.lane*LANE_W + LANE_W//2
        self.y = -120
        self.type = random.choice(['normal','fast','zigzag','truck'])
        if self.type == 'normal':
            self.speed = random.randint(5,9) + level*0.3; self.width,self.height = 50,90; self.color=BLUE
        elif self.type == 'fast':
            self.speed = random.randint(10,15) + level*0.7; self.width,self.height = 40,80; self.color=ORANGE
        elif self.type == 'zigzag':
            self.speed = random.randint(5,8) + level*0.3; self.width,self.height=45,85; self.color=YELLOW
            self.timer = 0; self.dir = random.choice([-1,1])
        elif self.type == 'truck':
            self.speed = random.randint(3,6) + level*0.2; self.width,self.height = 60,120; self.color=GRAY
    def update(self, road_speed):
        self.y += road_speed - self.speed
        if self.type == 'zigzag':
            self.timer += 1
            if self.timer > 30:
                self.timer = 0
                self.dir *= -1
            self.x += self.dir*2
            lane_center = ROAD_X + self.lane*LANE_W + LANE_W//2
            if abs(self.x - lane_center) > LANE_W//3: self.dir *= -1
    def draw(self,s,c):
        yy = c.apply(self.y)
        
        # رسم سيارة الذكاء الاصطناعي بشكل مفصل
        car_width, car_height = self.width, self.height
        
        # جسم السيارة الرئيسي
        pygame.draw.rect(s, self.color, (self.x-car_width//2, yy-car_height//2, car_width, car_height), border_radius=8)
        
        # السقف
        roof_width, roof_height = car_width-10, car_height//2
        pygame.draw.rect(s, self.color, (self.x-roof_width//2, yy-car_height//2+10, roof_width, roof_height), border_radius=6)
        
        # النوافذ
        window_color = (150, 200, 255)  # لون أزرق فاتح للنوافذ
        pygame.draw.rect(s, window_color, (self.x-roof_width//2+5, yy-car_height//2+15, roof_width-10, 15), border_radius=3)
        pygame.draw.rect(s, window_color, (self.x-roof_width//2+5, yy-car_height//2+35, roof_width-10, 15), border_radius=3)
        
        # الأضواء الأمامية
        pygame.draw.circle(s, WHITE, (self.x-car_width//4, yy+car_height//2-5), 4)
        pygame.draw.circle(s, WHITE, (self.x+car_width//4, yy+car_height//2-5), 4)
        
        # الأضواء الخلفية
        pygame.draw.circle(s, (255, 100, 100), (self.x-car_width//4, yy-car_height//2+5), 4)
        pygame.draw.circle(s, (255, 100, 100), (self.x+car_width//4, yy-car_height//2+5), 4)
        
        # العجلات
        wheel_color = BLACK
        wheel_width, wheel_height = 6, 12
        pygame.draw.rect(s, wheel_color, (self.x-car_width//2-5, yy-car_height//3, wheel_width, wheel_height), border_radius=3)
        pygame.draw.rect(s, wheel_color, (self.x+car_width//2-1, yy-car_height//3, wheel_width, wheel_height), border_radius=3)
        pygame.draw.rect(s, wheel_color, (self.x-car_width//2-5, yy+car_height//3-wheel_height, wheel_width, wheel_height), border_radius=3)
        pygame.draw.rect(s, wheel_color, (self.x+car_width//2-1, yy+car_height//3-wheel_height, wheel_width, wheel_height), border_radius=3)
        
    def rect(self,c): return pygame.Rect(self.x - self.width//2, c.apply(self.y) - self.height//2, self.width, self.height)
# COINS
class Coin:
    def __init__(self,level=1):
        self.lane=random.randint(0,LANES-1)
        self.x=ROAD_X+self.lane*LANE_W+LANE_W//2
        self.y=-60
        self.type=random.choice(['normal','bonus','super'])
        self.value = 10 if self.type=='normal' else 25 if self.type=='bonus' else 50
        self.radius = 15 if self.type=='normal' else 18 if self.type=='bonus' else 20
        self.color = ORANGE if self.type=='normal' else YELLOW if self.type=='bonus' else (255,215,0)
    def update(self,speed): self.y += speed
    def draw(self,s,c): pygame.draw.circle(s,self.color,(self.x,int(c.apply(self.y))),self.radius)
    def rect(self,c): return pygame.Rect(self.x-self.radius, c.apply(self.y)-self.radius, self.radius*2, self.radius*2)
# GAME
class Game:
    def __init__(self):
        self.state = State.MENU
        self.cam = Camera()
        self.road = Road()
        self.p = Player()
        self.cars = []
        self.coins = []
        self.timer = 0
        self.level_target_score = 500
        self.win_coins = 100 # عدد العملات المطلوبة للفوز
    def reset(self): self.__init__(); self.state=State.PLAY
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.state = State.PAUSE if self.state==State.PLAY else State.PLAY
        self.p.update(keys); self.cam.update(); self.road.update(self.p.speed)
        self.timer += 1
        self.p.level = 1 + int(self.p.score // self.level_target_score)
        if self.timer % max(30,90-self.p.level*5) == 0: self.cars.append(AICar(self.p.level))
        if self.timer % max(20,40-self.p.level*2) == 0: self.coins.append(Coin(self.p.level))
        for c in self.cars[:]:
            c.update(self.p.speed)
            if c.rect(self.cam).colliderect(self.p.rect()):
                self.p.lives -= 1
                self.cam.hit()
                self.cars.remove(c)
        for coin in self.coins[:]:
            coin.update(self.p.speed)
            if coin.rect(self.cam).colliderect(self.p.rect()):
                self.p.coins += 1
                self.p.score += coin.value
                self.coins.remove(coin)
        self.cars = [c for c in self.cars if c.y < HEIGHT+100]
        self.coins = [c for c in self.coins if c.y < HEIGHT+100]
        
        # التحقق من شرط الفوز
        if self.p.coins >= self.win_coins:
            self.state = State.WIN
        elif self.p.lives <= 0:
            self.state = State.GAME_OVER
    def draw(self):
        screen.fill(BLACK)
        self.road.draw(screen,self.cam)
        self.p.draw(screen)
        for c in self.cars: c.draw(screen,self.cam)
        for coin in self.coins: coin.draw(screen,self.cam)
        font = pygame.font.Font(None, 32)
        # ===== HUD أثناء اللعب =====
        if self.state == State.PLAY or self.state == State.PAUSE:
            # Lives
            pygame.draw.rect(screen, BLACK, (20, 10, 140, 40), border_radius=5)
            for i in range(self.p.lives):
                pygame.draw.circle(screen, RED, (40 + i*30, 30), 10)
            # Coins
            pygame.draw.rect(screen, BLACK, (180, 10, 140, 40), border_radius=5)
            coin_text = font.render(f"Coins: {self.p.coins}/{self.win_coins}", True, YELLOW)
            screen.blit(coin_text, (190, 18))
            # Score
            pygame.draw.rect(screen, BLACK, (340, 10, 200, 40), border_radius=5)
            score_text = font.render(f"Score: {int(self.p.score)}", True, WHITE)
            screen.blit(score_text, (350, 18))
        # ===== Game Over الشاشة =====
        if self.state == State.GAME_OVER:
            font_big = pygame.font.Font(None, 72)
            screen.blit(font_big.render("GAME OVER", True, RED), (WIDTH//2-180, HEIGHT//2-100))
            font_mid = pygame.font.Font(None, 48)
            # عرض السكور، العملات، والحياة في الوسط
            screen.blit(font_mid.render(f"Score: {int(self.p.score)}", True, WHITE), (WIDTH//2-100, HEIGHT//2))
            screen.blit(font_mid.render(f"Coins: {self.p.coins}", True, YELLOW), (WIDTH//2-100, HEIGHT//2 + 60))
            screen.blit(font_mid.render(f"Lives Left: {self.p.lives}", True, RED), (WIDTH//2-100, HEIGHT//2 + 120))
            font_small = pygame.font.Font(None, 36)
            screen.blit(font_small.render("Press R to Restart", True, WHITE), (WIDTH//2-100, HEIGHT//2 + 200))
        # ===== Win الشاشة =====
        if self.state == State.WIN:
            # إنشاء طبقة شبه شفافة
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            # رسم نجوم زخرفية
            for i in range(20):
                x = random.randint(50, WIDTH-50)
                y = random.randint(50, HEIGHT-50)
                pygame.draw.polygon(screen, YELLOW, [(x, y-10), (x-10, y+10), (x+10, y+10)])
            
            # رسم نص "YOU WIN!" مع الزخارف
            font_big = pygame.font.Font(None, 96)
            text = font_big.render("YOU WIN!", True, YELLOW)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2-50))
            screen.blit(text, text_rect)
            
            # رسم إطار زخرفي حول النص
            pygame.draw.rect(screen, YELLOW, (text_rect.x-20, text_rect.y-20, text_rect.width+40, text_rect.height+40), 3)
            
            # عرض الإحصائيات
            font_mid = pygame.font.Font(None, 48)
            score_text = font_mid.render(f"Final Score: {int(self.p.score)}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2+50))
            screen.blit(score_text, score_rect)
            
            coins_text = font_mid.render(f"Coins Collected: {self.p.coins}", True, YELLOW)
            coins_rect = coins_text.get_rect(center=(WIDTH//2, HEIGHT//2+100))
            screen.blit(coins_text, coins_rect)
            
            # تعليمات إعادة البدء
            font_small = pygame.font.Font(None, 36)
            restart_text = font_small.render("Press R to Play Again", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2+200))
            screen.blit(restart_text, restart_rect)
            
            # رسم الورق الملون
            for i in range(50):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                color = random.choice([RED, YELLOW, BLUE, (0,255,0), ORANGE])
                pygame.draw.rect(screen, color, (x, y, 5, 10))
        # ===== قائمة البداية =====
        if self.state == State.MENU:
            font_big = pygame.font.Font(None, 72)
            screen.blit(font_big.render("Press SPACE to Start", True, WHITE), (WIDTH//2-200, HEIGHT//2))
            # عرض شرط الفوز
            font_mid = pygame.font.Font(None, 48)
            win_text = font_mid.render(f"Collect {self.win_coins} coins to win!", True, YELLOW)
            win_rect = win_text.get_rect(center=(WIDTH//2, HEIGHT//2+60))
            screen.blit(win_text, win_rect)
    def run(self):
        while True:
            clock.tick(FPS)
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if self.state == State.MENU and e.key == pygame.K_SPACE: self.reset()
                    if (self.state == State.GAME_OVER or self.state == State.WIN) and e.key == pygame.K_r: self.reset()
            if self.state == State.PLAY: self.update()
            self.draw(); pygame.display.flip()
if __name__=="__main__":
    Game().run()