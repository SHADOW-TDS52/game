
import pgzrun
import random
import math

# --- НАСТРОЙКИ ---
WIDTH = 800
HEIGHT = 600
TITLE = "Орбитальный Защитник: Pixel Edition"

# Параметры орбит
PLAYER_ORBIT_RADIUS = 200
PLAYER_SPEED = 0.05
PLAYER_ORBIT_CHANGE = 10

# Механика
BULLET_SPEED = 15
ENEMY_BASE_SPEED = 3
WAVE_BONUS = 0.5

# Состояние
score = 0
wave = 1
game_over = False

# Списки объектов
bullets = []
enemies = []
modules = []

# Игрок
player = Actor('player', center=(WIDTH//2, HEIGHT//2))
player.orbit = PLAYER_ORBIT_RADIUS
player_angle_rad = 0  # игровой угол в радианах

# Стрельба
can_shoot = True
shoot_timer = 0

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_pos_from_orbit(angle, radius):
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    x = center_x + math.cos(angle) * radius
    y = center_y + math.sin(angle) * radius
    return x, y

def create_bullet():
    global can_shoot, shoot_timer
    if not can_shoot:
        return
    
    # Проверка: есть ли картинка лазера, иначе используем простой круг
    if 'laser' in images:
        b = Actor('laser')
    else:
        # запасной вариант: рисуем прямоугольник через временный Actor с простым спрайтом
        b = Actor('alien')
        b.width = 10
        b.height = 20
    
    px, py = get_pos_from_orbit(player_angle_rad, player.orbit)
    b.pos = (px, py)
    
    b.vx = math.cos(player_angle_rad) * BULLET_SPEED
    b.vy = math.sin(player_angle_rad) * BULLET_SPEED
    b.life = 60
    
    bullets.append(b)
    
    can_shoot = False
    shoot_timer = 25

def create_enemy():
    angle = random.uniform(0, 2 * math.pi)
    
    if 'enemy' in images:
        e = Actor('enemy')
    else:
        e = Actor('alien')
        e.width = 30
        e.height = 30
    
    e.angle_rad = angle
    e.orbit = 350
    e.speed = ENEMY_BASE_SPEED + (wave * WAVE_BONUS)
    e.radius = max(e.width, e.height) // 2 + 5  # небольшой запас
    enemies.append(e)

def create_module():
    angle = random.uniform(0, 2 * math.pi)
    m = Actor('module') if 'module' in images else Actor('player')
    m.angle_rad = angle
    m.orbit = random.randint(250, 350)
    m.type = random.choice([0, 1, 2])  # 0: очки, 1: ускорение стрельбы, 2: щит
    m.radius = 12
    modules.append(m)

# --- ОСНОВНАЯ ЛОГИКА ---
def update():
    global score, wave, game_over, can_shoot, shoot_timer, player_angle_rad
    
    if game_over:
        if keyboard.r:
            reset_game()
        return

    # 1. Управление игроком
    if keyboard.left or keyboard.a:
        player_angle_rad -= PLAYER_SPEED
    if keyboard.right or keyboard.d:
        player_angle_rad += PLAYER_SPEED
    
    if keyboard.up or keyboard.w:
        player.orbit = max(100, min(300, player.orbit - PLAYER_ORBIT_CHANGE))
    if keyboard.down or keyboard.s:
        player.orbit = max(100, min(300, player.orbit + PLAYER_ORBIT_CHANGE))

    # Обновляем реальную позицию игрока
    px, py = get_pos_from_orbit(player_angle_rad, player.orbit)
    player.pos = (px, py)
    # Поворот спрайта: +90, чтобы нос смотрел наружу
    player.angle = math.degrees(player_angle_rad) + 90 

    # 2. Стрельба
    if shoot_timer > 0:
        shoot_timer -= 1
    if shoot_timer == 0:
        can_shoot = True
        
    if (keyboard.space or keyboard.z) and can_shoot:
        create_bullet()

    # 3. Обновление снарядов
    bullets_to_remove = []
    for b in bullets:
        b.x += b.vx
        b.y += b.vy
        b.life -= 1
        if b.life <= 0 or not screen.rect.contains(b):
            bullets_to_remove.append(b)
    for b in bullets_to_remove:
        bullets.remove(b)

    # 4. Спавн
    # Делаем спавн реже: шанс 1 раз в ~10 кадров при 60 FPS, плюс лимит по волне
    spawn_chance = 5 + wave * 2
    if len(enemies) < 4 + wave and random.randint(1, 100) < spawn_chance:
        create_enemy()
    if random.randint(1, 400) == 1:
        create_module()

    # 5. Обновление врагов
    enemies_to_remove = []
    for e in enemies:
        e.orbit -= e.speed * 0.1
        e.angle_rad += 0.02
        
        ex, ey = get_pos_from_orbit(e.angle_rad, e.orbit)
        e.pos = (ex, ey)
        e.angle = math.degrees(e.angle_rad)

        if e.orbit < 60:
            game_over = True
            return

        # Столкновение с пулями (сначала собираем на удаление, чтобы не ломать цикл)
        for b in bullets[:]:
            if b.colliderect(e):
                if b not in bullets_to_remove:
                    bullets_to_remove.append(b)
                enemies_to_remove.append(e)
                score += 10
                break
        
        # Столкновение с игроком (круговая коллизия для аккуратности)
        dx = player.pos[0] - e.pos[0]
        dy = player.pos[1] - e.pos[1]
        dist_sq = dx*dx + dy*dy
        min_dist = player.radius + e.radius if hasattr(player, 'radius') else 20 + e.radius
        if dist_sq <= min_dist * min_dist:
            game_over = True
            return

    for e in enemies_to_remove:
        if e in enemies:
            enemies.remove(e)
    for b in bullets_to_remove:
        if b in bullets:
            bullets.remove(b)

    # 6. Модули
    modules_to_remove = []
    for m in modules:
        mx, my = get_pos_from_orbit(m.angle_rad, m.orbit)
        m.pos = (mx, my)
        
        # Круговая коллизия с модулем
        dx = player.pos[0] - m.pos[0]
        dy = player.pos[1] - m.pos[1]
        dist_sq = dx*dx + dy*dy
        min_dist = (player.radius if hasattr(player, 'radius') else 20) + m.radius
        if dist_sq <= min_dist * min_dist:
            score += 50
            modules_to_remove.append(m)
            # Тут можно добавить эффекты: ускорение стрельбы, щит и т.п.
    
    for m in modules_to_remove:
        if m in modules:
            modules.remove(m)

    # Прогресс волн
    if score > wave * 50:
        wave += 1

# --- ОТРИСОВКА ---
def draw():
    # Рисуем фон, если он есть
    if 'background' in images:
        screen.blit('background', (0, 0))
    else:
        screen.fill((10, 10, 20))
    
    # Рисуем ядро (центр)
    screen.draw.filled_circle((WIDTH//2, HEIGHT//2), 40, (50, 50, 50))
    
    # Рисуем объекты
    for b in bullets:
        b.draw()
    for e in enemies:
        e.draw()
    for m in modules:
        m.draw()
        
    player.draw()

    # Интерфейс
    screen.draw.text(f"Счет: {score}", (20, 20), fontsize=30, color=(255, 255, 255))
    screen.draw.text(f"Волна: {wave}", (20, 60), fontsize=30, color=(255, 255, 255))
    
    if game_over:
        screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2 - 20), fontsize=60, color=(255, 0, 0))
        screen.draw.text("Нажми R для рестарта", center=(WIDTH//2, HEIGHT//2 + 30), fontsize=30, color=(255, 255, 255))

def reset_game():
    global score, wave, game_over, bullets, enemies, modules, player, player_angle_rad
    score = 0
    wave = 1
    game_over = False
    bullets = []
    enemies = []
    modules = []
    player.orbit = PLAYER_ORBIT_RADIUS
    player_angle_rad = 0
    px, py = get_pos_from_orbit(player_angle_rad, player.orbit)
    player.pos = (px, py)
    player.angle = 90

pgzrun.go()
    