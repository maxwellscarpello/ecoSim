#### IMPORTS ####
import random
import pygame
import math

#### CONFIG ####
WIDTH = 1000
HEIGHT = 700
FPS = 60
WORLD_W, WORLD_H = 1000, 700
FOOD_COUNT = 50
FOOD_RADIUS = 3

#### HELPERS ####
def dist(x1, y1, x2, y2): 
    ## [HELPER] Euclidean distance ##
    return math.hypot(x2 - x1, y2 - y1)

def gen_clamp(x, y, margin=0):
        ## [HELPER] Clamp arbitrary point to world bounds ##
        left = margin
        right = WORLD_W - margin
        top = margin
        bottom = WORLD_H - margin

        if x < left:
            x = left
        if x > right:
            x = right
        if y < top:
            y = top
        if y > bottom:
            y = bottom
        return x, y

### CLASSES #### 
class Creature:
    ## [STATE] Per-creature stats and behavior state ##
    def __init__(self, x, y):
        self.x = x # x-position
        self.y = y # y-position
        self.speed = random.uniform(20, 100) # units per second; scaled by dt
        self.wander_speed = self.speed * 0.75 # wander speed
        self.max_energy = random.randint(80, 200) # max energy
        self.energy = self.max_energy # current energy
        self.vision = random.randint(80, 200) # vision radius
        self.r = random.randint(5, 15) # creature size
        self.target = None # current target
        self.wander_target = None # current wander destination
        self.eating = False # whether or not creature is eating
        self.eat_timer = 0 
        self.metabolism = random.randint(1, 10) # energy drain per second
        self.hunger_percent = random.uniform(0.3, 0.7)
        self.hunger_threshold = self.max_energy * self.hunger_percent # energy value that creature searches for food at
        self.alive = True
        self.heading = random.uniform(0, 2 * math.pi) # creatures starts facing a random direction
        self.cone_half_angle = math.radians(45) # half angle of the vision cone
    
    def clamp(self):
        ## [BOUNDS] Clamp creature center to world ##
        min_x = self.r # left
        max_x = WORLD_W - self.r # right
        min_y = self.r # top
        max_y = WORLD_H - self.r # bottom

        if self.x < min_x:
            self.x = min_x
        if self.x > max_x:
            self.x = max_x
        if self.y < min_y:
            self.y = min_y
        if self.y > max_y:
            self.y = max_y

    def find_food(self, foods):
        ## [TARGET] Choose closest visible food ##
        closest_food = None
        closest_dist = float("inf")
        for fx, fy in foods:
            d = dist(self.x, self.y, fx, fy)
            if d <= self.vision and d < closest_dist:
                closest_dist = d
                closest_food = fx, fy
        self.target = closest_food

    def move_toward_target(self, target, dt, speed):
        ## [MOVE] Normalized movement toward target ##
        tx, ty = target
        dx = tx - self.x # direction from
        dy = ty - self.y # creature to target
        d = dist(self.x, self.y, tx, ty)
        if d == 0: # divide by zero guard
            return
        nx = dx / d # normalized x-dir ###direction vectors toward
        ny = dy / d # normalized y-dir ###the target
        self.x += nx * speed * dt # move by speed
        self.y += ny * speed * dt # and time
        self.heading = math.atan2(ny, nx) # where creature is facing

    def wander(self, dt):
        ## [WANDER] Pick a local point, then move until reached ##
        r = random.uniform(0, self.vision)
        angle = random.uniform(0, 2 * math.pi)
        dx = r * math.cos(angle) # x-dir
        dy = r * math.sin(angle) # y-dir
        if self.wander_target is None:
            tx = self.x + dx
            ty = self.y + dy
            tx, ty = gen_clamp(tx, ty, margin=self.r)
            self.wander_target = tx, ty
        self.move_toward_target(self.wander_target, dt, self.wander_speed)
        tx, ty = self.wander_target
        d = dist(self.x, self.y, tx, ty)
        if d == 0: # divide by zero guard
            return
        if d <= 10:
            self.wander_target =  None

    def death(self):
        if self.alive is False:
            self.target = None
            self.wander_target = None
    
    def update(self, dt, foods):
        ## [UPDATE] Main per-frame behavior/state machine ##
        self.energy -= self.metabolism * dt # energy drain per second
        if self.alive is not True:
            return
        
        ## [EATING] Pause movement until eat timer completes ##
        if self.eating is True:
            self.eat_timer -= dt
            if self.eat_timer <= 0:
                if self.target in foods:
                    foods.remove(self.target)
                self.energy += 10
                self.target = None
                self.eating = False
            return

        ## [TARGET VALIDATION] Drop stale/removed targets ##
        if self.target not in foods:
            self.target = None   

        ## [DECISION] Acquire food target if none ##
        if self.target is None and self.energy <= self.hunger_threshold:
            self.find_food(foods)

        ## [CHASE] Move and transition into eating ##
        if self.target is not None and self.energy <= self.hunger_threshold:
            self.move_toward_target(self.target, dt, self.speed)
            tx, ty = self.target
            d = dist(self.x, self.y, tx, ty)
            if d > self.vision:
                self.target = None
            eat_radius = self.r + FOOD_RADIUS
            if d <= eat_radius: # start eating
                self.eating = True
                self.eat_timer = 2
                return
        ## [IDLE] No food target -> wander ##
        else:
            self.wander(dt)

        ## [DEATH] ##
        if self.energy <= 0:
            self.alive = False
            self.death()

        ## [POST] Final position safety clamp ##
        self.clamp()
            
    def draw (self, screen):
        ## [DRAW] Vision overlay + creature body ##
        surf_vision = pygame.Surface((self.vision * 2, self.vision * 2), pygame.SRCALPHA)
        surf_dead = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        if self.alive is True:
            ## VISION CIRCLE ##
            pygame.draw.circle(surf_vision, (255, 100, 100, 50), (self.vision, self.vision), self.vision)
            screen.blit(surf_vision, (self.x - self.vision, self.y - self.vision))

            ## VISION CONE ##
        
            ## CREATURE ##
            # alive
            pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), self.r)
        else:
            # dead
            pygame.draw.circle(surf_dead, (200, 0, 0, 180), (self.r, self.r), self.r)
            screen.blit (surf_dead, (self.x - self.r, self.y - self.r))

#### MAIN LOOP ####
def main(): 
    ## [BOOT] Init pygame/window ##
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ecosystem Simulator")
    clock = pygame.time.Clock()
    running = True
    
    ## FOOD
    foods = []

    ## CREATURES
    creatures = []
    for i in range(1): # number of creatures
        x = random.randint(0, WORLD_W)
        y = random.randint(0, WORLD_H)
        x, y = gen_clamp(x, y)
        creatures.append(Creature(x, y))

    ## [LOOP] Events -> spawn -> update -> draw ##
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        dt = clock.tick(FPS) / 1000 ## convert milliseconds to seconds ##
        
        if len(foods) < FOOD_COUNT and random.random() < 0.02: # 2% chance every tick to spawn food
            x = random.randint(0, WORLD_W - 1)
            y = random.randint(0, WORLD_H - 1)
            foods.append((x, y))    
        for c in creatures:
            c.update(dt, foods)
        
        screen.fill((0, 200, 0)) # draws the screen
        for fx, fy in foods: # draws the food
            pygame.draw.circle(screen, (255, 50, 50), (fx, fy), FOOD_RADIUS)
        for c in creatures:
            c.draw(screen) # draws the creature
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()