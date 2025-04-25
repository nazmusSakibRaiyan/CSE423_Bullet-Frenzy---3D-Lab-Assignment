from OpenGL.GL import *
from OpenGL.GLUT import *  
from OpenGL.GLUT.fonts import GLUT_BITMAP_HELVETICA_18  
from OpenGL.GLU import *
import math
import random
import time

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
GRID_LENGTH = 600  
WALL_HEIGHT = 50
PLAYER_RADIUS = 20 
ENEMY_RADIUS = 20  
BULLET_SIZE = 8
GUN_LENGTH = 60    

PLAYER_SPEED = 6.0     
ROTATION_SPEED = 4.0   
BULLET_SPEED = 18.0
ENEMY_SPEED = 0.25      
MAX_LIFE = 5
MAX_MISSED_BULLETS = 10

FOV_Y = 75            
Z_NEAR = 1.0
Z_FAR = 2000.0

KEY_FORWARD = b'w'
KEY_BACKWARD = b's'
KEY_LEFT = b'a'
KEY_RIGHT = b'd'
KEY_CHEAT_TOGGLE = b'c'
KEY_CHEAT_VISION = b'v'
KEY_RESET = b'r'

player_pos = [0.0, 0.0, PLAYER_RADIUS] 
player_angle = 0.0       
player_life = MAX_LIFE
game_score = 0
bullets_missed = 0
game_over = False
player_died = False 

camera_orbit_angle_y = 0.0 
camera_height = 500     
first_person_view = False  

cheat_mode = False
auto_vision = False      

bullets = []             
enemies = []             

keys_pressed = set()     

quadric = None         
def initialize_gl():
    global quadric
    quadric = gluNewQuadric() 
    glClearColor(0.1, 0.1, 0.2, 1.0) 
    glEnable(GL_DEPTH_TEST)          
    glEnable(GL_COLOR_MATERIAL)     
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE) 
 
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glShadeModel(GL_SMOOTH)

    light_ambient = [0.3, 0.3, 0.3, 1.0]
    light_diffuse = [0.9, 0.9, 0.9, 1.0]
    light_specular = [1.0, 1.0, 1.0, 1.0]
    light_position = [0.0, GRID_LENGTH * 1.5, 1000.0, 1.0] 

    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.8, 0.8, 0.8, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 30.0)

def spawn_enemy():
    while True:
        spawn_radius = random.uniform(150, GRID_LENGTH - ENEMY_RADIUS * 2)
        angle = random.uniform(0, 2 * math.pi)
        x = spawn_radius * math.cos(angle)
        y = spawn_radius * math.sin(angle)
        if math.sqrt(x**2 + y**2) > 100: 
            break

    scale = random.uniform(0.8, 1.2)
    scale_direction = random.choice([-1, 1])

    enemies.append({
        'pos': [x, y, ENEMY_RADIUS], 
        'scale': scale,
        'scale_direction': scale_direction
    })

def initialize_enemies():
    enemies.clear()
    for _ in range(5):
        spawn_enemy()

def reset_game():
    global player_pos, player_angle, player_life, game_score, bullets_missed
    global game_over, player_died, cheat_mode, auto_vision
    global bullets, enemies, keys_pressed, first_person_view
    global camera_orbit_angle_y, camera_height
    player_pos = [0.0, 0.0, PLAYER_RADIUS]
    player_angle = 0.0
    player_life = MAX_LIFE
    game_score = 0
    bullets_missed = 0
    game_over = False
    player_died = False
    cheat_mode = False
    auto_vision = False
    first_person_view = False 
    bullets.clear()
    keys_pressed.clear()
    camera_orbit_angle_y = 0.0
    camera_height = 500
    initialize_enemies()
    print("Game Reset!")

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()           
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()           
    glMatrixMode(GL_MODELVIEW) 

def draw_player():
    global quadric
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2]) 
    glRotatef(player_angle, 0, 0, 1)

    if player_died: 
        glTranslatef(0, 0, -PLAYER_RADIUS + 5) 
        glRotatef(90, 1, 0, 0) 

    glColor3f(0.1, 0.9, 0.1) 
    gluSphere(quadric, PLAYER_RADIUS, 20, 20)

    glColor3f(0.3, 0.3, 0.3) 
    glPushMatrix()
    glTranslatef(0, PLAYER_RADIUS, 0) 
    glRotatef(90, 1, 0, 0) 
    gluCylinder(quadric, 5, 5, GUN_LENGTH, 15, 5) 
    glPopMatrix()

    glColor3f(0.4, 0.4, 0.9) 
    glPushMatrix()
    glTranslatef(0, -PLAYER_RADIUS * 0.3, -5) 
    glRotatef(90, 1, 0, 0) 
    gluCylinder(quadric, 4, 4, 18, 10, 5) 
    glPopMatrix()

    glColor3f(0.9, 0.1, 0.1) 
    glPushMatrix()
    glTranslatef(0, -PLAYER_RADIUS * 0.7, 0) 
    glScalef(15, PLAYER_RADIUS * 1.5, 15) 
    glutSolidCube(1.0) 
    glPopMatrix()

    glPopMatrix() 

def draw_enemies():
    global quadric
    for enemy in enemies:
        glPushMatrix()
        glTranslatef(enemy['pos'][0], enemy['pos'][1], enemy['pos'][2])
        scale = enemy['scale']
        glScalef(scale, scale, scale)
        glColor3f(0.9, 0.2, 0.2) # Red
        gluSphere(quadric, ENEMY_RADIUS, 16, 16)

        glColor3f(0.6, 0.1, 0.1) 
        glPushMatrix()
        glTranslatef(0, ENEMY_RADIUS * 0.6, ENEMY_RADIUS * 0.4) 
        gluSphere(quadric, ENEMY_RADIUS * 0.4, 10, 10)
        glPopMatrix()

        glPopMatrix() 

def draw_bullets():
    glColor3f(0.0, 0.0, 0.0) 
    for bullet in bullets:
        if not bullet['hit']:
            glPushMatrix()
            glTranslatef(bullet['pos'][0], bullet['pos'][1], bullet['pos'][2])
            glutSolidCube(BULLET_SIZE) 
            glPopMatrix()

def draw_grid():
    glBegin(GL_QUADS)
    glColor3f(1.0, 1.0, 1.0)
    glNormal3f(0,0,1) 
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(0, GRID_LENGTH, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(-GRID_LENGTH, 0, 0)

    glColor3f(1.0, 1.0, 1.0)
    glNormal3f(0,0,1)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(0, -GRID_LENGTH, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(GRID_LENGTH, 0, 0)

    glColor3f(0.7, 0.5, 0.95)
    glNormal3f(0,0,1)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, -GRID_LENGTH, 0)

    glColor3f(0.7, 0.5, 0.95)
    glNormal3f(0,0,1)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, GRID_LENGTH, 0)
    glEnd()

    glColor3f(0.4, 0.4, 0.4) #
    line_spacing = 50
    glBegin(GL_LINES)
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, line_spacing):
        glVertex3f(i, -GRID_LENGTH, 0.1) 
        glVertex3f(i, GRID_LENGTH, 0.1)
        glVertex3f(-GRID_LENGTH, i, 0.1)
        glVertex3f(GRID_LENGTH, i, 0.1)
    glEnd()

    #Boundary Walls 

    glBegin(GL_QUADS)
    glColor3f(0.9, 0.0, 0.0)
    glNormal3f(0, 0, 0.9) 
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, WALL_HEIGHT)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, WALL_HEIGHT)

    glColor3f(0.0, 0.9, 0.0)
    glNormal3f(-1, 0, 0) 
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, WALL_HEIGHT)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, WALL_HEIGHT)

    glColor3f(0.0, 0.9, 0.9)
    glNormal3f(0, -1, 0) 
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, WALL_HEIGHT)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, WALL_HEIGHT)

    glColor3f(0.0, 0.0, 0.0)
    glNormal3f(0, 1, 0) 
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, WALL_HEIGHT)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, WALL_HEIGHT)
    glEnd()

def fire_bullet():
    if game_over: 
        return
    angle_rad = math.radians(player_angle)
    dir_x = math.sin(angle_rad)
    dir_y = math.cos(angle_rad)
    start_offset = PLAYER_RADIUS + GUN_LENGTH
    start_x = player_pos[0] + dir_x * start_offset
    start_y = player_pos[1] + dir_y * start_offset
    start_z = player_pos[2] 
    bullets.append({
        'pos': [start_x, start_y, start_z],
        'dir': [dir_x, dir_y], 
        'life': 200,
        'hit': False
    })
    print(f"Fired bullet. Count: {len(bullets)}") 

def update_bullets_and_collisions():
    global game_score, bullets_missed, game_over, player_died
    if game_over: 
        return
    bullets_to_remove = []
    enemies_hit_indices = set()
    for i, bullet in enumerate(bullets):
        if bullet['hit']:
            if i not in bullets_to_remove: bullets_to_remove.append(i)
            continue
        bullet['pos'][0] += bullet['dir'][0] * BULLET_SPEED
        bullet['pos'][1] += bullet['dir'][1] * BULLET_SPEED
        bullet['life'] -= 1
        if (abs(bullet['pos'][0]) > GRID_LENGTH or
            abs(bullet['pos'][1]) > GRID_LENGTH or
            bullet['life'] <= 0):
            bullet['hit'] = True
            bullets_to_remove.append(i)
            if bullet['life'] > 0: 
                bullets_missed += 1
                print(f"Bullet missed boundary. Missed count: {bullets_missed}") 
                if bullets_missed >= MAX_MISSED_BULLETS and not game_over:
                    print("Game Over - Too many missed bullets!")
                    game_over = True
                    player_died = True
            continue

        bullet_radius_sq = (BULLET_SIZE / 2)**2 
        for j, enemy in enumerate(enemies):
            if j in enemies_hit_indices: 
                continue 
            dx = bullet['pos'][0] - enemy['pos'][0]
            dy = bullet['pos'][1] - enemy['pos'][1]
            dz = bullet['pos'][2] - enemy['pos'][2]
            dist_sq = dx*dx + dy*dy + dz*dz

            enemy_current_radius = ENEMY_RADIUS * enemy['scale']
            collision_dist_sq = (enemy_current_radius)**2 + bullet_radius_sq 
            if dist_sq < collision_dist_sq:
                bullet['hit'] = True
                bullets_to_remove.append(i)
                enemies_hit_indices.add(j)
                game_score += 1
                print(f"Enemy hit! Score: {game_score}") 
                break 
    if enemies_hit_indices:
        new_enemy_list = []
        for j, enemy in enumerate(enemies):
            if j not in enemies_hit_indices:
                new_enemy_list.append(enemy)
        enemies[:] = new_enemy_list 
        for i in range(len(enemies_hit_indices)):
            if not game_over: 
                spawn_enemy()
    unique_indices = sorted(list(set(bullets_to_remove)), reverse=True)
    for i in unique_indices:
        if 0 <= i < len(bullets): 
            bullets.pop(i)
        else: 
            print(f"Warning: Tried to remove bullet index {i}, but list length is {len(bullets)}") 

def update_enemies_and_collisions():
    global player_life, game_over, player_died
    if game_over: 
        return
    enemies_to_remove_indices = set() 

    for i, enemy in enumerate(enemies):
        scale_change = 0.008
        enemy['scale'] += enemy['scale_direction'] * scale_change
        if enemy['scale'] >= 1.2:
            enemy['scale'] = 1.2
            enemy['scale_direction'] = -1
        elif enemy['scale'] <= 0.8:
            enemy['scale'] = 0.8
            enemy['scale_direction'] = 1
        dx = player_pos[0] - enemy['pos'][0]
        dy = player_pos[1] - enemy['pos'][1]        
        distance_to_player_xy = math.sqrt(dx*dx + dy*dy)
        if distance_to_player_xy > 1.0: 
            move_x = (dx / distance_to_player_xy) * ENEMY_SPEED
            move_y = (dy / distance_to_player_xy) * ENEMY_SPEED
            enemy['pos'][0] += move_x
            enemy['pos'][1] += move_y
        dz = player_pos[2] - enemy['pos'][2]
        dist_sq = dx*dx + dy*dy + dz*dz
        enemy_current_radius = ENEMY_RADIUS * enemy['scale']
        collision_dist_sq = (PLAYER_RADIUS + enemy_current_radius)**2

        if dist_sq < collision_dist_sq:
            enemies_to_remove_indices.add(i) 
            player_life -= 1
            print(f"Player hit by enemy! Life: {player_life}") 
            if player_life <= 0 and not game_over:
                print("Game Over - Player ran out of life!")
                game_over = True
                player_died = True
    if enemies_to_remove_indices:
        new_enemy_list = []
        for i, enemy in enumerate(enemies):
            if i not in enemies_to_remove_indices:
                new_enemy_list.append(enemy)
        enemies[:] = new_enemy_list 
        for i in range(len(enemies_to_remove_indices)):
             if not game_over:
                 spawn_enemy()


def update_cheat_mode():
    global player_angle
    if not cheat_mode or game_over: 
        return
    auto_rotate_speed = 1.5 
    player_angle = (player_angle + auto_rotate_speed) % 360
    if auto_vision: 
        player_angle = (player_angle + auto_rotate_speed) % 360
    if not auto_vision: 
        player_angle = (player_angle + auto_rotate_speed) % 360
    angle_rad = math.radians(player_angle)
    player_dir_x = math.sin(angle_rad)
    player_dir_y = math.cos(angle_rad)
    fire_chance = 0.03 
    if random.random() < fire_chance and len(bullets) < 20: 
        for enemy in enemies:
            dx = enemy['pos'][0] - player_pos[0]
            dy = enemy['pos'][1] - player_pos[1]
            dist_sq = dx*dx + dy*dy
            if dist_sq > 0:
                dot_product = (dx * player_dir_x) + (dy * player_dir_y)
                mag_enemy_vec = math.sqrt(dist_sq)
                cos_angle = dot_product / mag_enemy_vec if mag_enemy_vec else 0
                angle_threshold_cos = math.cos(math.radians(10)) 
                if cos_angle > angle_threshold_cos:
                    fire_bullet()
                    break 


def handle_movement():
    if game_over: 
        return 
    global player_pos
    move_direction = 0 
    if KEY_FORWARD in keys_pressed:
        move_direction += 1
    if KEY_BACKWARD in keys_pressed:
        move_direction -= 1
    if move_direction != 0:
        angle_rad = math.radians(player_angle)
        delta_x = math.sin(angle_rad) * move_direction * PLAYER_SPEED
        delta_y = math.cos(angle_rad) * move_direction * PLAYER_SPEED
        new_x = player_pos[0] + delta_x
        new_y = player_pos[1] + delta_y
        boundary_limit = GRID_LENGTH - PLAYER_RADIUS
        player_pos[0] = max(-boundary_limit, min(boundary_limit, new_x))
        player_pos[1] = max(-boundary_limit, min(boundary_limit, new_y))

def handle_rotation():
    if game_over or cheat_mode:
        return
    global player_angle
    rotation_direction = 0 
    if KEY_LEFT in keys_pressed:
        rotation_direction -= 1
    if KEY_RIGHT in keys_pressed:
        rotation_direction += 1
    if rotation_direction != 0:
        player_angle = (player_angle + rotation_direction * ROTATION_SPEED) % 360

def keyboardListener(key, x, y):
    global cheat_mode, auto_vision, game_over
    if key in [KEY_FORWARD, KEY_BACKWARD, KEY_LEFT, KEY_RIGHT]:
        keys_pressed.add(key)
    elif key == KEY_CHEAT_TOGGLE:
        if not game_over:
            cheat_mode = not cheat_mode
            print(f"Cheat Mode: {'ON' if cheat_mode else 'OFF'}")
            if not cheat_mode: 
                auto_vision = False 
            keys_pressed.discard(KEY_LEFT) 
            keys_pressed.discard(KEY_RIGHT)
    elif key == KEY_CHEAT_VISION:
        if cheat_mode and not game_over: 
            auto_vision = not auto_vision
            print(f"Cheat Auto Vision: {'ON' if auto_vision else 'OFF'}")
            global first_person_view
            if auto_vision: 
                first_person_view = False
    elif key == KEY_RESET:
        if game_over:
            reset_game()

def keyboardUpListener(key, x, y):
    if key in keys_pressed:
        keys_pressed.remove(key)

def specialKeyListener(key, x, y):
    global camera_height, camera_orbit_angle_y
    if not first_person_view and not (cheat_mode and auto_vision):
        move_speed = 25
        rotate_speed = 5.0 
        if key == GLUT_KEY_UP:
            camera_height += move_speed
            camera_height = min(camera_height, 1200) 
        elif key == GLUT_KEY_DOWN:
            camera_height -= move_speed
            camera_height = max(camera_height, PLAYER_RADIUS + 20) 
        elif key == GLUT_KEY_LEFT:
            camera_orbit_angle_y = (camera_orbit_angle_y - rotate_speed) % 360
        elif key == GLUT_KEY_RIGHT:
            camera_orbit_angle_y = (camera_orbit_angle_y + rotate_speed) % 360

def mouseListener(button, state, x, y):
    global first_person_view
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if not game_over and not cheat_mode: 
             fire_bullet()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
         if not (cheat_mode and auto_vision):
              first_person_view = not first_person_view
              print(f"Camera View Toggled: {'First Person' if first_person_view else 'Third Person'}")
         else:
              print("Cannot toggle view mode while Auto Vision cheat is active.")

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = WINDOW_WIDTH / float(WINDOW_HEIGHT) if WINDOW_HEIGHT > 0 else 1.0
    gluPerspective(FOV_Y, aspect_ratio, Z_NEAR, Z_FAR)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    eyeX, eyeY, eyeZ = 0, 0, 0
    centerX, centerY, centerZ = 0, 0, 0
    upX, upY, upZ = 0, 0, 1 
    if first_person_view:
        angle_rad = math.radians(player_angle)
        dir_x = math.sin(angle_rad)
        dir_y = math.cos(angle_rad)
        eye_forward_offset = PLAYER_RADIUS + GUN_LENGTH + 5.0 
        eye_height_offset = 5.0 
        eyeX = player_pos[0] + dir_x * eye_forward_offset
        eyeY = player_pos[1] + dir_y * eye_forward_offset
        eyeZ = player_pos[2] + eye_height_offset 
        look_distance = 100.0 
        centerX = eyeX + dir_x * look_distance
        centerY = eyeY + dir_y * look_distance
        centerZ = eyeZ 
    elif cheat_mode and auto_vision:
        follow_distance = 200 
        height_offset = 100   
        angle_rad = math.radians(player_angle)
        eyeX = player_pos[0] - math.sin(angle_rad) * follow_distance
        eyeY = player_pos[1] - math.cos(angle_rad) * follow_distance
        eyeZ = player_pos[2] + height_offset
        look_ahead_dist = 50
        centerX = player_pos[0] + math.sin(angle_rad) * look_ahead_dist
        centerY = player_pos[1] + math.cos(angle_rad) * look_ahead_dist
        centerZ = player_pos[2]
    else:        
        orbit_radius = 650 
        orbit_angle_rad = math.radians(camera_orbit_angle_y)
        eyeX = orbit_radius * math.sin(orbit_angle_rad)
        eyeY = -orbit_radius * math.cos(orbit_angle_rad) 
        eyeZ = camera_height
        centerX, centerY, centerZ = 0, 0, 0
    if abs(eyeX - centerX) < 0.01 and abs(eyeY - centerY) < 0.01 and abs(eyeZ - centerZ) < 0.01:
        centerX += 0.01
        centerY += 0.01
        centerZ += 0.01
    gluLookAt(eyeX, eyeY, eyeZ,
              centerX, centerY, centerZ,
              upX, upY, upZ)


def idle():
    handle_movement()
    handle_rotation()
    if not game_over:
        update_bullets_and_collisions()
        update_enemies_and_collisions()
        update_cheat_mode()
    glutPostRedisplay()

    time.sleep(0.005)


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    
    setupCamera()
    glEnable(GL_LIGHTING)
    draw_grid()
    draw_bullets()
    draw_enemies()
    draw_player()
    glDisable(GL_LIGHTING)
    info_y = WINDOW_HEIGHT - 30 
    draw_text(10, info_y, f"Life: {player_life}/{MAX_LIFE}")
    draw_text(10, info_y - 30, f"Score: {game_score}")
    draw_text(10, info_y - 60, f"Bullets Missed: {bullets_missed}/{MAX_MISSED_BULLETS}")
    if cheat_mode:
        draw_text(10, info_y - 90, "CHEAT MODE ACTIVE (C)")
        if auto_vision:
            draw_text(10, info_y - 120, "AUTO VISION ACTIVE (V)")

    if game_over:
        msg1 = "G A M E   O V E R"
        msg2 = "Press 'R' to Restart"
        text_width1 = len(msg1) * 10
        text_width2 = len(msg2) * 10
        draw_text(WINDOW_WIDTH / 2 - text_width1 / 2, WINDOW_HEIGHT / 2 + 15, msg1)
        draw_text(WINDOW_WIDTH / 2 - text_width2 / 2, WINDOW_HEIGHT / 2 - 15, msg2)
    glutSwapBuffers()

def main():
    glutInit() 
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH) 
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(50, 50) 
    wind = glutCreateWindow(b"Bullet Frenzy - 3D Lab Assignment") 
    initialize_gl()     
    reset_game()        
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener) 
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle) 

    print("Bullet Frenzy Controls:")
    print(" W/S: Move Forward/Backward")
    print(" A/D: Rotate Left/Right (Disabled in Cheat Mode)")
    print(" Left Mouse: Fire Bullet (Disabled in Cheat Mode)")
    print(" Right Mouse: Toggle First/Third Person View (Disabled in Auto Vision Cheat)")
    print(" Arrow Keys Up/Down: Adjust Camera Height (Third Person)")
    print(" Arrow Keys Left/Right: Orbit Camera (Third Person)")
    print(" C: Toggle Cheat Mode (Auto-Rotate & Auto-Fire)")
    print(" V: Toggle Auto Vision Camera (Requires Cheat Mode)")
    print(" R: Restart Game (When Game Over)")
    print("--------------------------------")

    glutMainLoop() 

if __name__ == "__main__":
    main()