import pygame, random, sys, torch, torch.nn as nn, numpy as np

# نفس بنية الشبكة العصبية المستخدمة في التدريب
class DQN(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128), nn.ReLU(),
            nn.Linear(128, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, out_dim)
        )
    def forward(self, x): return self.net(x)

pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Pro Racing - Showing Trained Model")
clock = pygame.time.Clock()

WHITE, BLACK, RED, YELLOW, ORANGE, BLUE, GRAY, ROAD_COLOR, GRASS = \
    (255,255,255),(0,0,0),(220,60,60),(255,220,0),(255,170,60),(80,160,255),(50,50,50),(60,60,65),(40,120,40)

ROAD_WIDTH, LANES = 600, 5
ROAD_X = (WIDTH - ROAD_WIDTH) // 2
LANE_W = ROAD_WIDTH // LANES

def draw_pro_car(s, x, y, color):
    w, h = 50, 100
    pygame.draw.rect(s, color, (int(x-w//2), int(y-h//2), w, h), border_radius=10)
    roof_w, roof_h = w-10, h//2
    pygame.draw.rect(s, color, (int(x-roof_w//2), int(y-h//4), roof_w, roof_h), border_radius=8)
    win_c = (150, 200, 255)
    pygame.draw.rect(s, win_c, (int(x-roof_w//2+5), int(y-35), roof_w-10, 15), border_radius=3)
    pygame.draw.rect(s, win_c, (int(x-roof_w//2+5), int(y-15), roof_w-10, 15), border_radius=3)
    pygame.draw.circle(s, WHITE, (int(x-w//4), int(y-h//2+5)), 5)
    pygame.draw.circle(s, WHITE, (int(x+w//4), int(y-h//2+5)), 5)
    for wx in [-w//2-5, w//2-3]:
        for wy in [-h//3, h//3-15]:
            pygame.draw.rect(s, BLACK, (int(x+wx), int(y+wy), 8, 15), border_radius=3)

# تحميل "العقل" الذي تم تدريبه
model = DQN(11, 3)
try:
    model.load_state_dict(torch.load("final_ai_model.pth"))
    model.eval()
    print("AI Model loaded successfully!")
except:
    print("No model file found! Run training first.")
    sys.exit()

def get_current_state(player_lane, enemies, coins):
    res = [player_lane / 4.0]
    c_dists, n_dists = [1.0] * 5, [1.0] * 5
    for e in enemies:
        d = (HEIGHT - 140 - e[1]) / HEIGHT
        if 0 < d < c_dists[e[0]]: c_dists[e[0]] = d
    for cn in coins:
        d = (HEIGHT - 140 - cn[1]) / HEIGHT
        if 0 < d < n_dists[cn[0]]: n_dists[cn[0]] = d
    return np.array(res + c_dists + n_dists, dtype=np.float32)

player_lane = 2
current_x = ROAD_X + player_lane * LANE_W + LANE_W // 2
enemies, coins, timer, score = [], [], 0, 0

while True:
    screen.fill(GRASS)
    pygame.draw.rect(screen, ROAD_COLOR, (ROAD_X, 0, ROAD_WIDTH, HEIGHT))
    
    # رسم خطوط الطريق المتحركة
    for i in range(1, LANES):
        for y_line in range(-120, HEIGHT + 120, 120):
            pygame.draw.rect(screen, YELLOW, (ROAD_X + i*LANE_W - 2, y_line + (timer % 120), 4, 40))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()

    # استشارة الذكاء الاصطناعي
    state = get_current_state(player_lane, enemies, coins)
    with torch.no_grad():
        action = torch.argmax(model(torch.tensor(state).unsqueeze(0).float())).item()

    if action == 1 and player_lane > 0: player_lane -= 1
    elif action == 2 and player_lane < 4: player_lane += 1

    target_x = ROAD_X + player_lane * LANE_W + LANE_W // 2
    current_x += (target_x - current_x) * 0.20

    timer += 1
    if timer % 45 == 0: enemies.append([random.randint(0, 4), -120, random.choice([BLUE, ORANGE, GRAY])])
    if timer % 60 == 0: coins.append([random.randint(0, 4), -60])

    for e in enemies[:]:
        e[1] += 9
        draw_pro_car(screen, ROAD_X + e[0]*LANE_W + LANE_W//2, e[1], e[2])
        if e[0] == player_lane and abs(e[1] - (HEIGHT - 140)) < 85:
            enemies, coins, score = [], [], 0
        elif e[1] > HEIGHT + 120: enemies.remove(e)

    for cn in coins[:]:
        cn[1] += 9
        pygame.draw.circle(screen, YELLOW, (ROAD_X + cn[0]*LANE_W + LANE_W//2, int(cn[1])), 15)
        if cn[0] == player_lane and abs(cn[1] - (HEIGHT - 140)) < 65:
            score += 10; coins.remove(cn)
        elif cn[1] > HEIGHT + 120: coins.remove(cn)

    draw_pro_car(screen, current_x, HEIGHT - 140, RED)
    screen.blit(pygame.font.SysFont("Arial", 32, True).render(f"TRAINED AI SCORE: {score}", True, WHITE), (30, 30))
    pygame.display.flip()
    clock.tick(60)