import pygame
import sys
import random
import math

# Initialisation
pygame.init()
# Fenêtre beaucoup plus grande (1600x900)
WIDTH, HEIGHT = 1600, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Réseau de Pétri - Simulation 4 Voies (Grand Format)")
clock = pygame.time.Clock()

# Couleurs
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRASS = (60, 170, 90)
ASPHALT = (60, 60, 60)
LINES = (220, 220, 220)
GREEN = (46, 204, 113)
ORANGE = (243, 156, 18)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
GRAY = (200, 200, 200)

# Polices plus grandes pour la nouvelle résolution
font = pygame.font.SysFont("arial", 18)
font_bold = pygame.font.SysFont("arial", 18, bold=True)
font_title = pygame.font.SysFont("arial", 26, bold=True)

CAR_COLORS = [(220, 50, 50), (50, 100, 220), (220, 220, 50), (240, 130, 40), (150, 50, 200), (255, 255, 255)]
moving_cars = []

# --- DÉFINITION DU RÉSEAU DE PÉTRI (Espacement corrigé) ---
# L'axe X du schéma va de 800 à 1600. L'axe Y va de 0 à 900.
places = {
    "P1": {"x": 1000, "y": 120, "tokens": 1, "nom": "P1 (Vert NS)", "col": GREEN},
    "P2": {"x": 1000, "y": 360, "tokens": 0, "nom": "P2 (Orange NS)", "col": ORANGE},
    "P3": {"x": 1000, "y": 600, "tokens": 0, "nom": "P3 (Rouge NS)", "col": RED},
    
    "P4": {"x": 1400, "y": 120, "tokens": 0, "nom": "P4 (Vert EO)", "col": GREEN},
    "P5": {"x": 1400, "y": 360, "tokens": 0, "nom": "P5 (Orange EO)", "col": ORANGE},
    "P6": {"x": 1400, "y": 600, "tokens": 1, "nom": "P6 (Rouge EO)", "col": RED},
    
    "P7": {"x": 950, "y": 740, "tokens": 0, "nom": "P7 (File Nord)", "col": BLUE},
    "P8": {"x": 1100, "y": 740, "tokens": 0, "nom": "P8 (File Sud)", "col": BLUE},
    "P9": {"x": 1300, "y": 740, "tokens": 0, "nom": "P9 (File Est)", "col": BLUE},
    "P10": {"x": 1450, "y": 740, "tokens": 0, "nom": "P10 (File Ouest)", "col": BLUE}
}

transitions = {
    # Coordonnées Y très espacées pour éviter le chevauchement des textes
    "T1": {"x": 1000, "y": 240, "w": 60, "h": 30, "nom": "T1 (Warn NS)"},
    "T2": {"x": 1200, "y": 480, "w": 60, "h": 30, "nom": "T2 (Go EO)"},
    "T3": {"x": 1400, "y": 240, "w": 60, "h": 30, "nom": "T3 (Warn EO)"},
    "T4": {"x": 1200, "y": 240, "w": 60, "h": 30, "nom": "T4 (Go NS)"},
    
    # Passages véhicules
    "T5": {"x": 950, "y": 850, "w": 60, "h": 30, "nom": "T5 (Pass N)"},
    "T6": {"x": 1100, "y": 850, "w": 60, "h": 30, "nom": "T6 (Pass S)"},
    "T7": {"x": 1300, "y": 850, "w": 60, "h": 30, "nom": "T7 (Pass E)"},
    "T8": {"x": 1450, "y": 850, "w": 60, "h": 30, "nom": "T8 (Pass W)"}
}

# Matrice W
arcs = [
    ("P1", "T1"), ("T1", "P2"),
    ("P2", "T2"), ("P6", "T2"), ("T2", "P3"), ("T2", "P4"),
    ("P4", "T3"), ("T3", "P5"),
    ("P5", "T4"), ("P3", "T4"), ("T4", "P6"), ("T4", "P1"),
    
    ("P1", "T5"), ("P7", "T5"), ("T5", "P1"),
    ("P1", "T6"), ("P8", "T6"), ("T6", "P1"),
    ("P4", "T7"), ("P9", "T7"), ("T7", "P4"),
    ("P4", "T8"), ("P10", "T8"), ("T8", "P4")
]

for t_id in transitions:
    transitions[t_id]["in"] = [arc[0] for arc in arcs if arc[1] == t_id]
    transitions[t_id]["out"] = [arc[1] for arc in arcs if arc[0] == t_id]

def draw_arrow(surface, color, start, end):
    pygame.draw.line(surface, color, start, end, 2)
    rotation = math.atan2(start[1] - end[1], end[0] - start[0]) + math.pi/2
    rad = 7
    pygame.draw.polygon(surface, color, [
        (end[0] + rad * math.sin(rotation), end[1] + rad * math.cos(rotation)),
        (end[0] + rad * math.sin(rotation - 2.5), end[1] + rad * math.cos(rotation - 2.5)),
        (end[0] + rad * math.sin(rotation + 2.5), end[1] + rad * math.cos(rotation + 2.5))
    ])

def draw_car(x, y, color, direction):
    w, h = (28, 44) if direction in ["N", "S"] else (44, 28)
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=4)
    if direction == "N": pygame.draw.rect(screen, (173, 216, 230), (x+5, y+28, 18, 10))
    elif direction == "S": pygame.draw.rect(screen, (173, 216, 230), (x+5, y+6, 18, 10))
    elif direction == "E": pygame.draw.rect(screen, (173, 216, 230), (x+28, y+5, 10, 18))
    elif direction == "W": pygame.draw.rect(screen, (173, 216, 230), (x+6, y+5, 10, 18))

def draw_traffic_light(x, y, is_vert, is_org, is_rouge):
    pygame.draw.rect(screen, BLACK, (x, y, 26, 75), border_radius=5)
    pygame.draw.circle(screen, RED if is_rouge else (60, 20, 20), (x+13, y+16), 8)
    pygame.draw.circle(screen, ORANGE if is_org else (60, 40, 10), (x+13, y+37), 8)
    pygame.draw.circle(screen, GREEN if is_vert else (20, 60, 20), (x+13, y+58), 8)

def dessiner_ui_gauche():
    # La moitié gauche fait maintenant 800x900
    pygame.draw.rect(screen, GRASS, (0, 0, 800, HEIGHT))
    pygame.draw.rect(screen, ASPHALT, (310, 0, 180, HEIGHT)) # Route NS plus large
    pygame.draw.rect(screen, ASPHALT, (0, 360, 800, 180))    # Route EO plus large
    
    # Lignes blanches
    for i in range(0, HEIGHT, 40): pygame.draw.line(screen, LINES, (400, i), (400, i+20), 3)
    for i in range(0, 800, 40): pygame.draw.line(screen, LINES, (i, 450), (i+20, 450), 3)

    # États des feux
    ns_v = places["P1"]["tokens"] > 0; ns_o = places["P2"]["tokens"] > 0; ns_r = places["P3"]["tokens"] > 0
    eo_v = places["P4"]["tokens"] > 0; eo_o = places["P5"]["tokens"] > 0; eo_r = places["P6"]["tokens"] > 0

    # Placement des feux
    draw_traffic_light(270, 270, ns_v, ns_o, ns_r) # Haut-Gauche
    draw_traffic_light(500, 550, ns_v, ns_o, ns_r) # Bas-Droit
    draw_traffic_light(500, 270, eo_v, eo_o, eo_r) # Haut-Droit
    draw_traffic_light(270, 550, eo_v, eo_o, eo_r) # Bas-Gauche

    # Files d'attente (Positions ajustées pour les routes larges)
    for i in range(min(places["P7"]["tokens"], 5)): draw_car(330, 300 - (i * 55), GRAY, "S") # Nord vers Sud
    for i in range(min(places["P8"]["tokens"], 5)): draw_car(430, 550 + (i * 55), GRAY, "N") # Sud vers Nord
    for i in range(min(places["P9"]["tokens"], 5)): draw_car(510 + (i * 55), 380, GRAY, "W") # Est vers Ouest
    for i in range(min(places["P10"]["tokens"], 5)): draw_car(240 - (i * 55), 470, GRAY, "E") # Ouest vers Est

    # Animation
    global moving_cars
    for c in moving_cars:
        c["x"] += c["dx"]; c["y"] += c["dy"]
        draw_car(c["x"], c["y"], c["color"], c["dir"])
    moving_cars = [c for c in moving_cars if -100 < c["x"] < 900 and -100 < c["y"] < 1000]

    # Panel Mode d'emploi agrandi et replacé
    box_x, box_y, box_w, box_h = 20, 600, 240, 280
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), border_radius=8)
    pygame.draw.rect(screen, BLACK, (box_x, box_y, box_w, box_h), 2, border_radius=8)
    screen.blit(font_title.render("Mode d'emploi", True, BLACK), (box_x + 15, box_y + 15))
    lignes = [
        "- Génération auto du trafic.",
        "- FEU ORANGE INTÉGRÉ.",
        "",
        "Cliquez dans cet ordre :",
        " 1. T1 (NS devient Orange)",
        " 2. T2 (EO devient Vert)",
        " 3. T3 (EO devient Orange)",
        " 4. T4 (NS redevient Vert)",
        "",
        "Boutons T5 à T8 :",
        " Les voitures ne passent",
        " QUE si le feu est Vert !"
    ]
    for idx, txt in enumerate(lignes):
        screen.blit(font.render(txt, True, BLACK), (box_x + 15, box_y + 55 + idx*18))

def dessiner_petri():
    # La moitié droite fait 800x900
    pygame.draw.rect(screen, WHITE, (800, 0, 800, HEIGHT))
    pygame.draw.line(screen, BLACK, (800, 0), (800, HEIGHT), 5)
    
    titre = font_title.render("Supervision du Carrefour (3 États)", True, BLACK)
    screen.blit(titre, (1200 - titre.get_width()//2, 30))

    # Dessin des Arcs
    for src, dst in arcs:
        x1, y1 = places[src]["x"] if src in places else transitions[src]["x"], places[src]["y"] if src in places else transitions[src]["y"]
        x2, y2 = places[dst]["x"] if dst in places else transitions[dst]["x"], places[dst]["y"] if dst in places else transitions[dst]["y"]
        draw_arrow(screen, GRAY, (x1, y1), (x2, y2))

    # Dessin des Places (Ronds)
    for p_id, p in places.items():
        is_active = p["tokens"] > 0
        c_color = p["col"] if is_active else WHITE
        
        pygame.draw.circle(screen, c_color, (p["x"], p["y"]), 28) # Ronds plus grands
        pygame.draw.circle(screen, BLACK, (p["x"], p["y"]), 28, 3)
        
        if p["tokens"] > 0:
            if "File" in p["nom"]: screen.blit(font_bold.render(str(p["tokens"]), True, WHITE), (p["x"] - 5, p["y"] - 11))
            else: pygame.draw.circle(screen, BLACK, (p["x"], p["y"]), 10)

        txt_surf = font_bold.render(p["nom"], True, BLACK)
        # Texte placé bien AU-DESSUS pour ne pas écraser les arcs ou les ronds
        screen.blit(txt_surf, (p["x"] - txt_surf.get_width()//2, p["y"] - 55))

    # Dessin des Transitions (Carrés)
    for t_id, t in transitions.items():
        rect = pygame.Rect(t["x"] - t["w"]//2, t["y"] - t["h"]//2, t["w"], t["h"])
        activable = all(places[p]["tokens"] >= 1 for p in t["in"])
        pygame.draw.rect(screen, GREEN if activable else RED, rect, border_radius=4)
        pygame.draw.rect(screen, BLACK, rect, 2, border_radius=4)
        
        txt_surf = font_bold.render(t["nom"], True, BLACK)
        # Texte placé bien EN-DESSOUS pour ne pas écraser les arcs ou les carrés
        screen.blit(txt_surf, (t["x"] - txt_surf.get_width()//2, t["y"] + 25))

def tirer_transition(t_id):
    t = transitions[t_id]
    if all(places[p]["tokens"] >= 1 for p in t["in"]):
        for p in t["in"]: places[p]["tokens"] -= 1
        for p in t["out"]: places[p]["tokens"] += 1
        
        color = random.choice(CAR_COLORS)
        vitesse = 10
        if t_id == "T5": moving_cars.append({"x": 330, "y": 300, "dx": 0, "dy": vitesse, "color": color, "dir": "S"})
        if t_id == "T6": moving_cars.append({"x": 430, "y": 550, "dx": 0, "dy": -vitesse, "color": color, "dir": "N"})
        if t_id == "T7": moving_cars.append({"x": 510, "y": 380, "dx": -vitesse, "dy": 0, "color": color, "dir": "W"})
        if t_id == "T8": moving_cars.append({"x": 240, "y": 470, "dx": vitesse, "dy": 0, "color": color, "dir": "E"})

running = True
while running:
    if random.random() < 0.02:
        file_cible = random.choice(["P7", "P8", "P9", "P10"])
        if places[file_cible]["tokens"] < 5: places[file_cible]["tokens"] += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for t_id, t in transitions.items():
                rect = pygame.Rect(t["x"] - t["w"]//2, t["y"] - t["h"]//2, t["w"], t["h"])
                if rect.collidepoint(pos): tirer_transition(t_id)

    dessiner_ui_gauche()
    dessiner_petri()
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()