import pygame, random, sys, torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque

class DQN(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()#لوراثة الخصائص الخاصة في nn model
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128), nn.ReLU(),
            nn.Linear(128, 128), nn.ReLU(), 
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, out_dim)
        )
    def forward(self, x): return self.net(x)

class FastEnv:
    def __init__(self): self.reset()#لما تعمل كائن جديد اعمل بيئة جديدة 
    def reset(self):
        self.lane = 2
        self.cars, self.coins = [], []
        self.timer, self.lives = 0, 3
        return self.get_state()

    def step(self, action):
        reward = 0.1 # مكافأة ثبات بسيطة
        old_lane = self.lane # تخزين المسار السابق لكشف "النقطة العمياء"
        
        # تنفيذ الحركة
        if action == 1 and self.lane > 0: self.lane -= 1#الحركة الى اليسار 
        elif action == 2 and self.lane < 4: self.lane += 1#الحركة الى اليمين 
        
        self.timer += 1
        if self.timer % 30 == 0: self.cars.append([random.randint(0, 4), -100])#كل 30 خطوة نضيف  عوائق جديدة 
        if self.timer % 50 == 0: self.coins.append([random.randint(0, 4), -60])#كل 30 خطوة نضيف  كوين  جديد
        
        # --- منطق الأعداء، مستوى الخطورة، والنقطة العمياء ---
        for c in self.cars[:]:#مكان العقبات 
            c[1] += 12#الموقع العامودي للسيارة مكافاه للتحرك بعيدا عن الخطر 
            dist = abs(c[1] - (800 - 140)) #  المسافة الطولية بين السيارتين
            
            if c[0] == self.lane:#نقيس المسافة بين العقبة والسيارة الخاصة بنا 
                # 1. حالة التصادم أو النقطة العمياء (التصادم الجانبي)
                if dist < 95:#تمثل المسافة الامنه 
                    # إذا كان التصادم ناتج عن تغيير مسار (دخل في سيارة بجانبه)
                    penalty = 50.0 if self.lane == old_lane else 70.0  
                    reward -= penalty 
                    self.lives -= 1
                    self.cars.remove(c)#remove the obictical car 
                # 2. مستوى الخطورة (Danger Zone) - التواجد خلف سيارة قريبة
                elif dist < 250:#المركبة في منطه خطرة ولكن مستوى الخطورة 
                    reward -= 1.5 # عقوبة تنبيهية للابتعاد عن السيارات المزعجة
            
            elif c[1] > 800: self.cars.remove(c)#تجاوزت السايرة حدود المسار فنزيلها لنحصل على عقبات جديدة 
        
        # --- موازنة الحصول على الكوين ---
        for cn in self.coins[:]:
            cn[1] += 10#لحركه  العملات في البيئة 
            if cn[0] == self.lane and abs(cn[1] - (800 - 140)) < 60:#السيارة والكوين في نفس الطريق 
                reward += 25.0 # زيادة قيمة الكوين لتشجيع المخاطرة المحسوبة
                self.coins.remove(cn)
            elif cn[1] > 800: self.coins.remove(cn)#the coin is out side the moniterd screen so we remove it to make update 

        return self.get_state(), reward, self.lives <= 0#بعد الانتهاء من الحركة ننظر الى الحالة 

    def get_state(self):
        res = [self.lane / 4.0]#تحويل موقع المركبة الى قيمه من 0 الى 1 والفائده هو اننا نسهل على النموذج عملية التعلم لاننا نجعل المدخلات في نطاق موحد 
        c_dists, n_dists = [1.0] * 5, [1.0] * 5
        for c in self.cars:
            d = (800 - 140 - c[1]) / 800#نحول d الى قيمه نسبية 
            if 0 < d < c_dists[c[0]]: c_dists[c[0]] = d#i determine the obistical car 
        for cn in self.coins:
            d = (800 - 140 - cn[1]) / 800
            if 0 < d < n_dists[cn[0]]: n_dists[cn[0]] = d
        return np.array(res + c_dists + n_dists, dtype=np.float32)#نرجع مصفوفة تمثل حالة البيئة 

q_net = DQN(11, 3)
optimizer = optim.Adam(q_net.parameters(), lr=0.00025)#معامل صغير لايجاد تحديثات بسيطه على القيم
memory = deque(maxlen=50000)#هيكل البيانات Q 
eps, eps_decay = 1.0, 0.985#eps for exploration  ,eps desay for expolitation  
rewards_history = []

print("--- STARTING ENHANCED TRAINING ---")
for ep in range(1, 501):
    env = FastEnv()#كائن جديد من البيئة
    state, done = env.reset(), False#اعادة تعيين الحالة للسيارة وال المتغير الثاني يعني ان اللعبة لم تنتهي 
    episode_reward = 0
    while not done:#طول ما السيارة ما خسرت 
        if random.random() < eps: action = random.randint(0, 2)#عملية عشوائية لاستمرار الاستكشاف 
        else:
            with torch.no_grad(): action = torch.argmax(q_net(torch.tensor(state).unsqueeze(0))).item()#just go forward and add another dimention to tensor 
                                                                                                       #to ensure that  all dimention is match         
        n_state, reward, done = env.step(action)#updat to state and reward repet this process and know if the is end or not 
        memory.append((state, action, reward, n_state, done))#save the parameters 
        state = n_state#update the state to new state 
        episode_reward += reward#update the reward of the episod 
        
        if len(memory) > 256:#نتاكد من حجم الذاكرة 
            batch = random.sample(memory, 128)#عينة عشوائية من الذاكرة لضان تنوع التجارب للابتعاد عن ضمان النموذج لانماط معينة 
            s_t, ns_t = torch.tensor(np.array([b[0] for b in batch])), torch.tensor(np.array([b[3] for b in batch]))#تحويل البيانات الى تينسور 
            a_t = torch.tensor([b[1] for b in batch]).unsqueeze(1)  #تحويل الافعال مع اضافة بعد جديد               #b[0]الحالة الحالية b[3]الحالة الجديدة 
            r_t = torch.tensor([b[2] for b in batch], dtype=torch.float32).unsqueeze(1)
            d_t = torch.tensor([b[4] for b in batch], dtype=torch.float32).unsqueeze(1)
            
            target = r_t + 0.99 * (1 - d_t) * q_net(ns_t).detach().max(1)[0].unsqueeze(1)#حساب قيمه الهدف 
                           #0.99 للنظر الى الحوافر المستقبلية 
                           #d_t is state of the game 1 mean the game is complete and 0 mean the game is end 
                           #n_st new state the car will go to it 
                           #max(1)[0]give me the maximum value and put it in a new tensor his size is 0
            loss = nn.MSELoss()(q_net(s_t).gather(1, a_t), target)#gather نختار القيم من مخرجات الشبكة بناءا على الافعال 
                                                                  #target is the actual aim 
            optimizer.zero_grad(); loss.backward(); optimizer.step()#نحذف الخبرات القدية لالا تاثر على الخبرات الجديدة
            #لعدم التاثر في التحسينات السابقة 
    eps = max(0.01, eps * eps_decay)#لتقليل نسبة الاستكاف مع مرور الوقت والقيمة ما تنزل عن 0.01 لضمان استمرار الاستكشاف ولو بنسبة بسيط 
    rewards_history.append(episode_reward)
    if ep % 50 == 0:
        avg_r = sum(rewards_history[-50:]) / 50
        print(f"Episode {ep} | Avg Reward: {avg_r:.2f} | Eps: {eps:.3f}")

torch.save(q_net.state_dict(), "final_ai_model.pth")#save the parameters on the file using the dectionary iside the fun state_dict 
print("Training Complete. Model Optimized for Risk & Reward.")
