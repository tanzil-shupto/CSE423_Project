from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
from math import sin, cos, pi

# Window dimensions
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Game variables
catcher_x = WINDOW_WIDTH // 2
catcher_y = 50
catcher_width = 100
catcher_height = 20
balls = []
laser_balls = []
boss_ball_active = False
boss_ball = None
boss_ball_hits = 0

ball_radius = 10
base_ball_speed = 0.1
score = 0
lives = 20
paused = False
game_over = False
level = 1
level_target = 10
background_color = [0.0, 0.0, 0.0]
ball_spawn_timer = 0
spawn_interval = 1.0

# Power-up states
power_up_active = False
power_up_end_time = 0
power_up_type = None

laser_active = False
laser_end_time = 0

# Set initial point size
initial_point_size = 5.0

# Midpoint Circle Algorithm
def midpoint_circle(cx, cy, radius):
    points = []
    for angle in range(0, 360, 5):  # step angle for fewer points
        theta = angle * pi / 180
        x = cx + radius * cos(theta)
        y = cy + radius * sin(theta)
        points.append((x, y))
    return points

# Draw the catcher using GL_POINTS
def draw_catcher():
    glColor3f(0.0, 1.0, 0.0)  # Green color
    glPointSize(initial_point_size)
    glBegin(GL_POINTS)
    for x in range(int(catcher_x - catcher_width // 2), int(catcher_x + catcher_width // 2)):
        for y in range(int(catcher_y), int(catcher_y + catcher_height)):
            glVertex2f(x, y)
    glEnd()

# Draw balls using GL_POINTS
def draw_balls():
    glPointSize(initial_point_size)
    for ball in balls:
        glColor3f(ball["color"][0], ball["color"][1], ball["color"][2])
        glBegin(GL_POINTS)
        for point in midpoint_circle(ball["x"], ball["y"], ball_radius):
            glVertex2f(*point)
        glEnd()

# Draw boss ball using GL_POINTS
def draw_boss_ball():
    if boss_ball_active and boss_ball:
        glColor3f(1.0, 0.5, 0.0)  # Orange color
        glPointSize(initial_point_size + 2.0)  # Slightly larger
        glBegin(GL_POINTS)
        for point in midpoint_circle(boss_ball["x"], boss_ball["y"], ball_radius * 2):
            glVertex2f(*point)
        glEnd()

# Draw laser using GL_POINTS
def draw_laser():
    if laser_active:
        glColor3f(1.0, 0.0, 0.0)  # Bright red laser
        glPointSize(initial_point_size * 2)  # Larger point size for visibility
        glBegin(GL_POINTS)
        for y in range(int(catcher_y + catcher_height), WINDOW_HEIGHT):
            glVertex2f(catcher_x, y)
        glEnd()

# Spawn regular ball
def spawn_ball():
    x = random.randint(ball_radius, WINDOW_WIDTH - ball_radius)
    speed = base_ball_speed + random.uniform(0.5, 2.0)
    color = (random.random(), random.random(), random.random())
    special = random.random() < 0.2  # 20% chance for special ball
    double_score = random.random() < 0.1  # 10% chance for double score ball
    balls.append({"x": x, "y": WINDOW_HEIGHT, "speed": speed, "color": color, "special": special, "double": double_score})

# Spawn boss ball
def spawn_boss_ball():
    global boss_ball_active, boss_ball_hits, boss_ball
    boss_ball_active = True
    boss_ball_hits = 0
    x = random.randint(ball_radius, WINDOW_WIDTH - ball_radius)
    speed = base_ball_speed
    boss_ball = {"x": x, "y": WINDOW_HEIGHT, "speed": speed}

# Spawn laser ball
def spawn_laser_ball():
    x = random.randint(ball_radius, WINDOW_WIDTH - ball_radius)
    speed = base_ball_speed + random.uniform(0.5, 2.0)
    laser_balls.append({"x": x, "y": WINDOW_HEIGHT, "speed": speed})

# Update positions of balls, laser, boss ball
def update_positions():
    global balls, laser_active, laser_end_time, catcher_width, power_up_active, power_up_end_time, power_up_type, boss_ball_active, boss_ball, boss_ball_hits, score, lives, level, background_color, spawn_interval, game_over

    current_time = time.time()

    # Update regular balls
    for ball in balls[:]:
        ball["y"] -= ball["speed"]
        # Check if the ball is caught by the catcher
        if catcher_y < ball["y"] < catcher_y + catcher_height and \
           (catcher_x - catcher_width // 2) < ball["x"] < (catcher_x + catcher_width // 2):
            if ball["double"]:
                score += 2
            else:
                score += 1
            if ball["special"]:
                activate_power_up()
            balls.remove(ball)

            # Check for level-up
            if score >= level * level_target:
                level += 1
                spawn_interval = max(0.5, spawn_interval - 0.1)
                background_color = [random.random(), random.random(), random.random()]

        # Remove ball if missed
        elif ball["y"] < 0:
            lives -= 1
            balls.remove(ball)

    # Update laser balls
    for laser_ball in laser_balls[:]:
        laser_ball["y"] -= laser_ball["speed"]
        # Check if laser ball is caught by catcher
        if catcher_y < laser_ball["y"] < catcher_y + catcher_height and \
           (catcher_x - catcher_width // 2) < laser_ball["x"] < (catcher_x + catcher_width // 2):
            # Activate laser
            laser_active = True
            laser_end_time = current_time + 5  # Laser lasts for 5 seconds
            laser_balls.remove(laser_ball)
        # Remove laser ball if missed
        elif laser_ball["y"] < 0:
            laser_balls.remove(laser_ball)

    # Update laser
    if laser_active:
        # Laser is active, check if duration has ended
        if current_time > laser_end_time:
            laser_active = False
        else:
            # Check for collision with regular balls
            for ball in balls[:]:
                # If ball is within laser path (x coordinate close to catcher_x)
                if abs(ball["x"] - catcher_x) < ball_radius:
                    if ball["special"]:
                        activate_power_up()
                    if ball["double"]:
                        score += 2
                    else:
                        score += 1
                    balls.remove(ball)
            # Similarly, check boss ball
            if boss_ball_active and boss_ball:
                if abs(boss_ball["x"] - catcher_x) < (ball_radius * 2):
                    boss_ball_hits += 1
                    if boss_ball_hits >= 3:
                        score += 5
                        boss_ball_active = False
                        boss_ball = None

    # Update boss ball
    if boss_ball_active and boss_ball:
        boss_ball["y"] -= boss_ball["speed"]
        # Check if boss ball is caught by catcher
        if catcher_y < boss_ball["y"] < catcher_y + catcher_height and \
           (catcher_x - catcher_width // 2) < boss_ball["x"] < (catcher_x + catcher_width // 2):
            boss_ball_hits += 1
            if boss_ball_hits >= 3:
                score += 5
                boss_ball_active = False
                boss_ball = None
        # Remove boss ball if missed
        elif boss_ball["y"] < 0:
            boss_ball_active = False
            boss_ball = None

    # Power-up expiration
    if power_up_active and current_time > power_up_end_time:
        deactivate_power_up()

    # Check for game over
    if lives <= 0:
        game_over = True

# Activate power-up
def activate_power_up():
    global power_up_active, power_up_end_time, power_up_type, catcher_width
    if not power_up_active:
        power_up_active = True
        power_up_end_time = time.time() + 5  # 5 seconds duration
        power_up_type = "wide"  # Currently only "wide" power-up
        catcher_width *= 1.5  # Expand catcher width

# Deactivate power-up
def deactivate_power_up():
    global power_up_active, power_up_type, catcher_width
    if power_up_active:
        power_up_active = False
        if power_up_type == "wide":
            catcher_width /= 1.5  # Reset catcher width
        power_up_type = None

# Display text on screen
def display_text(text, x, y):
    glColor3f(1.0, 1.0, 1.0)  # White color
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

# Keyboard input handler
def keyboard(key, x, y):
    global catcher_x, paused, game_over
    if key == b'a':
        catcher_x = max(catcher_x - 20, catcher_width // 2)
    elif key == b'd':
        catcher_x = min(catcher_x + 20, WINDOW_WIDTH - catcher_width // 2)
    elif key == b'p':
        paused = not paused
    elif key == b'r' and game_over:
        restart_game()

# Restart game
def restart_game():
    global balls, laser_balls, boss_ball_active, boss_ball, catcher_x, score, lives, game_over, level, spawn_interval, background_color, power_up_active, catcher_width
    balls = []
    laser_balls = []
    boss_ball_active = False
    boss_ball = None
    catcher_x = WINDOW_WIDTH // 2
    score = 0
    lives = 20  # Reset to initial value
    game_over = False
    level = 1
    spawn_interval = 1.0
    background_color = [0.0, 0.0, 0.0]
    power_up_active = False
    catcher_width = 100  # Reset catcher width

# Main game loop
def game_loop():
    global game_over, ball_spawn_timer

    if game_over:
        glClear(GL_COLOR_BUFFER_BIT)
        display_text("Game Over! Press R to Restart", 300, 300)
        glutSwapBuffers()
        return

    if not paused:
        current_time = time.time()
        if current_time - ball_spawn_timer > spawn_interval:
            spawn_ball()
            # 50% chance to spawn boss ball if not active
            if not boss_ball_active and random.random() < 0.5:
                spawn_boss_ball()
            # 50% chance to spawn laser ball
            if random.random() < 0.5:
                spawn_laser_ball()
            ball_spawn_timer = current_time

        update_positions()

    glClearColor(*background_color, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_catcher()
    draw_balls()
    draw_laser()
    if boss_ball_active:
        draw_boss_ball()
    display_text(f"Score: {score}", 10, WINDOW_HEIGHT - 20)
    display_text(f"Lives: {lives}", 10, WINDOW_HEIGHT - 40)
    display_text(f"Level: {level}", 10, WINDOW_HEIGHT - 60)

    glutSwapBuffers()
    glutPostRedisplay()

# Initialize OpenGL and run the main loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Ball Catching Game")
    glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    glutDisplayFunc(game_loop)
    glutKeyboardFunc(keyboard)
    glutIdleFunc(game_loop)
    glutMainLoop()

if __name__ == "__main__":
    main()
