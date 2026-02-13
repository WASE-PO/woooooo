# ============================================================
# 🤖 ETHIOPIAN ROBOT GIRL 3D - COMPETITION MASTER EDITION (V4)
# ============================================================
import cv2
import mediapipe as mp
import numpy as np
import math
import time
import os
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *

# --- Configuration ---
W, H = 1600, 900 
MSAA_SAMPLES = 4

# MediaPipe setup (Dual Hand Detection)
# MediaPipe setup (Dual Hand Detection)
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils # For drawing connections
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.3, # Ultra High Sensitivity
    min_tracking_confidence=0.3
)

# State Variables
rotation_x = 0
rotation_y = 0
zoom_scale = 1.0
walking_phase = 0
greeting_played = False

# Colors (Ethiopian Traditional Theme)
COLOR_SKIN = (0.35, 0.22, 0.15)     
COLOR_DRESS_WHITE = (0.98, 0.98, 0.98) 
COLOR_PATTERN_GREEN = (0.0, 0.5, 0.15)
COLOR_PATTERN_YELLOW = (0.9, 0.8, 0.0)
COLOR_PATTERN_RED = (0.8, 0.0, 0.0)
COLOR_GRASS = (0.1, 0.4, 0.1)       

def draw_sphere(radius, slices, stacks):
    quad = gluNewQuadric()
    gluSphere(quad, radius, slices, stacks)

def draw_cylinder(base, top, height, slices, stacks):
    quad = gluNewQuadric()
    gluCylinder(quad, base, top, height, slices, stacks)

def draw_box(width, height, depth):
    glPushMatrix()
    glScalef(width, height, depth)
    glBegin(GL_QUADS)
    glVertex3f(-0.5, -0.5, 0.5); glVertex3f(0.5, -0.5, 0.5); glVertex3f(0.5, 0.5, 0.5); glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(-0.5, -0.5, -0.5); glVertex3f(-0.5, 0.5, -0.5); glVertex3f(0.5, 0.5, -0.5); glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5); glVertex3f(-0.5, 0.5, 0.5); glVertex3f(0.5, 0.5, 0.5); glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(-0.5, -0.5, -0.5); glVertex3f(0.5, -0.5, -0.5); glVertex3f(0.5, -0.5, 0.5); glVertex3f(-0.5, -0.5, 0.5)
    glEnd()
    glPopMatrix()



def draw_ketema_floor():
    glPushMatrix()
    glTranslatef(0, -1.1, 0)
    glColor3fv(COLOR_GRASS)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-10, 0, -10); glVertex3f(10, 0, -10); glVertex3f(10, 0, 10); glVertex3f(-10, 0, 10)
    glEnd()
    glPopMatrix()

def draw_ethiopian_robot_girl(walking_phase):
    glPushMatrix()
    glTranslatef(0, -1.0, 0)
    bounce = math.sin(walking_phase * 2) * 0.05
    glTranslatef(0, bounce, 0)

    # 1. HEAD
    glPushMatrix()
    glTranslatef(0, 3.8, 0)
    glColor3fv(COLOR_SKIN)
    draw_sphere(0.4, 32, 32)
    # Eyes
    # Eyes
    glColor3f(1.0, 1.0, 0); # Yellow LED
    for side in [-1, 1]:
        glPushMatrix(); glTranslatef(side * 0.15, 0, 0.3); draw_sphere(0.04, 8, 8); glPopMatrix()
    glPopMatrix()

    # 2. TORSO
    glPushMatrix()
    glTranslatef(0, 2.7, 0)
    glColor3fv(COLOR_DRESS_WHITE)
    glPushMatrix(); glScalef(1.0, 1.4, 0.6); draw_sphere(0.8, 32, 32); glPopMatrix()
    # Tibeb Pattern
    glPushMatrix()
    glTranslatef(0, 0, 0.4)
    for i, col in enumerate([COLOR_PATTERN_GREEN, COLOR_PATTERN_YELLOW, COLOR_PATTERN_RED]):
        glColor3fv(col); glPushMatrix(); glTranslatef(0, 0.15 - i*0.12, 0); draw_box(1.2, 0.1, 0.1); glPopMatrix()
    glPopMatrix()
    glPopMatrix()

    # 3. Arms/Legs
    for side in [-1, 1]:
        # ARMS
        glPushMatrix()
        glTranslatef(side * 0.9, 3.2, 0)
        swing = math.sin(walking_phase + (math.pi if side == 1 else 0)) * 25
        glRotatef(swing, 1, 0, 0)
        glColor3fv(COLOR_SKIN)
        draw_sphere(0.15, 16, 16); draw_cylinder(0.1, 0.08, 1.0, 16, 1)
        glPopMatrix()
        
        # LEGS
        glPushMatrix()
        glTranslatef(side * 0.35, -0.5, 0)
        leg_swing = math.sin(walking_phase + (0 if side == 1 else math.pi)) * 20
        glRotatef(leg_swing, 1, 0, 0)
        glColor3fv(COLOR_SKIN); glRotatef(90, 1, 0, 0); draw_cylinder(0.12, 0.1, 1.2, 16, 1)
        glPopMatrix()

    # 4. SKIRT
    glPushMatrix(); glTranslatef(0, 1.5, 0); glRotatef(90, 1, 0, 0); glColor3fv(COLOR_DRESS_WHITE); draw_cylinder(0.7, 1.3, 2.0, 32, 1); glPopMatrix()

    glPopMatrix()

def count_fingers(hand_landmarks):
    """Count raised fingers (Index and Middle)"""
    fingers = 0
    # Landmarks for tips: Index=8, Middle=12
    # Landmarks for bases: Index=6, Middle=10
    if hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y:
        fingers += 1
    if hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y:
        fingers += 1
    return fingers

def main():
    global rotation_x, rotation_y, zoom_scale, walking_phase, greeting_played
    
    pygame.init(); pygame.mixer.init()
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, MSAA_SAMPLES)
    
    screen = pygame.display.set_mode((W, H), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("ETHIOPIAN ROBOT GIRL 4K - GESTURE LIGHT BULB")
    
    glEnable(GL_DEPTH_TEST); glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
    glLightfv(GL_LIGHT0, GL_POSITION, [15, 15, 15, 1])
    glMatrixMode(GL_PROJECTION); gluPerspective(45, W/H, 0.1, 100); glMatrixMode(GL_MODELVIEW)
    
    # Try multiple camera initialization methods
    cap = None
    print("Attempting to open camera...")
    
    # Method 1: Default with DSHOW
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if cap.isOpened():
        print("✓ Camera opened with CAP_DSHOW")
    else:
        print("✗ CAP_DSHOW failed, trying default...")
        cap.release()
        # Method 2: Default without backend
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✓ Camera opened with default backend")
        else:
            print("✗ Default failed, trying index 1...")
            cap.release()
            # Method 3: Try camera index 1
            cap = cv2.VideoCapture(1)
            if cap.isOpened():
                print("✓ Camera opened at index 1")
            else:
                print("\n" + "="*60)
                print("ERROR: Could not open any camera!")
                print("="*60)
                print("Possible solutions:")
                print("1. Close other apps using the camera (Teams, Zoom, etc.)")
                print("2. Check Windows camera privacy settings")
                print("3. Try running: python camera_test.py")
                print("="*60)
                return
    
    clock = pygame.time.Clock()
    
    if os.path.exists("greeting.mp3"):
        pygame.mixer.music.load("greeting.mp3")

    print("\n" + "="*60)
    print("ETHIOPIAN ROBOT GIRL - Hand Tracking Active")
    print("="*60)
    print("Controls:")
    print("  - Move hand LEFT/RIGHT: Rotate 360°")
    print("  - Move hand UP/DOWN: Tilt")
    print("  - Press ESC to exit")
    print("="*60 + "\n")

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                cap.release(); cv2.destroyAllWindows(); pygame.quit(); return

        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            if results.multi_hand_landmarks:
                if not greeting_played:
                    try: pygame.mixer.music.play(); greeting_played = True
                    except: pass
                
                # Use primary hand for finger logic
                hand = results.multi_hand_landmarks[0]
                print(f"✓ Hand detected! Position: X={hand.landmark[8].x:.2f}, Y={hand.landmark[8].y:.2f}")
                
                # Movement logic
                tip = hand.landmark[8]
                # Horizontal Rotation (Left/Right) - 360 degrees
                rotation_y += ((tip.x - 0.5) * 720 - rotation_y) * 0.1
                
                # Vertical Rotation (Up/Down) - 180 degrees tilt
                # tip.y is 0 at top, 1 at bottom.
                rotation_x += ((tip.y - 0.5) * 180 - rotation_x) * 0.1
                
                walking_phase += 0.15
            else:
                rotation_y += 0.5
                walking_phase += 0.05
                greeting_played = False

            # Monitor HUD
            small_cam = cv2.resize(frame, (320, 180))
            
            # Draw green dots AND lines on hands for debugging
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        small_cam, 
                        hand_landmarks, 
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
                    )

            txt = f"Review Hand: {len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0}"
            cv2.putText(small_cam, txt, (10, 30), 1, 1.0, (0, 255, 0), 2)
            cv2.imshow("Hand Control Monitor", small_cam)
            cv2.waitKey(1)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity(); glClearColor(0, 0, 0.01, 1)
        gluLookAt(0, 1.5, 10, 0, 1.5, 0, 0, 1, 0)
        
        # Enable lighting
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 0.8, 1])
        
        # Draw floor
        draw_ketema_floor()
        
        # Apply transformations for rotation
        glScalef(zoom_scale, zoom_scale, zoom_scale)
        glRotatef(rotation_x, 1, 0, 0)  # Vertical rotation (up/down)
        glRotatef(rotation_y, 0, 1, 0)  # Horizontal rotation (left/right)
        
        # Draw the robot girl
        draw_ethiopian_robot_girl(walking_phase)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
