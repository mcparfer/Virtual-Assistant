import pygame
import textwrap

COLOR1 = (0, 0, 255)
COLOR2 = (0, 200, 255)
BLACK = (255, 255, 255)
TRANSPARENT = (0, 0, 0)


# -----------------------------------------------------
# ----------------- CLASES GEOMÉTRICAS ----------------
# -----------------------------------------------------

class GeometricShape:
    """
        Crea una instancia de una Figura Geométrica.

        Args:
            screen (pygame.Surface): La superficie en la que se dibujará la figura.
            x (int): La coordenada x de la figura.
            y (int): La coordenada y de la figura.
            size (int): El tamaño de la figura.
            color (tuple): El color de la figura en formato RGB.
            alpha (int, optional): El valor de transparencia de la figura.
            image (str, optional): La ruta de la imagen que contendrá la figura.
    """

    def __init__(self, screen, x, y, size, color, alpha=0, image=""):
        self.screen = screen
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.alpha = alpha
        self.image = image

    def draw(self):
        """Método que dibuja e inserta la figura en la pantalla."""

        surface = None
        if self.alpha > 0:
            surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            surface.set_alpha(self.alpha)
        else:
            surface = pygame.Surface((self.size, self.size))
        pygame.draw.polygon(surface, self.color, self.points)
        
        if self.image:      # Inserta una imagen en el centro de la figura si la hubiera.
            image = pygame.image.load(self.image)
            image = pygame.transform.scale(image, (self.size, self.size))
            image_x = (self.size - image.get_width()) // 2
            image_y = (self.size - image.get_height()) // 2
            surface.blit(image, (image_x, image_y))
        
        self.screen.blit(surface, (self.x, self.y))
    
    def get_screen_coordinates(self):
        """ Método que devuelve las coordenadas de la figura en la pantalla. """

        return [(point[0] + self.x, point[1] + self.y) for point in self.points]


class Diamond(GeometricShape):
    """ Crea una instancia de un Diamante, 
    heredando los métodos de la clase padre GeometricShape. """

    def __init__(self, screen, x, y, size, color, alpha=100, image=""):

        # Invocación del constructor de la clase padre.
        super().__init__(screen, x, y, size, color, alpha, image)

        # Proporciones base de un diamante.
        self.points = [(self.size // 2, 0),             
                       (self.size, self.size // 2), 
                       (self.size // 2, self.size), 
                       (0, self.size // 2)]


class Triangle(GeometricShape):
    """ Crea una instancia de un Triangulo, 
    heredando los métodos de la clase GeometricShape. """
    
    def __init__(self, screen, x, y, size, color, alpha=100, image=""):
        super().__init__(screen, x, y, size, color, alpha, image)
        self.points = [(self.size, 0),
                       (0, self.size),
                       (self.size, self.size)]
        

class Half_Diamond(GeometricShape):
    """ Crea una instancia de un SemiDiamante, 
    heredando los métodos de la clase GeometricShape. """

    def __init__(self, screen, x, y, size, color, alpha=100, image=""):
        super().__init__(screen, x, y, size, color, alpha, image)
        self.points = [(self.size // 2, 0),
                       (self.size, self.size // 2),
                       (5 * self.size // 6, 4 * self.size // 6),
                       (self.size // 6, 4 * self.size // 6),
                       (0, self.size // 2)]


class Bar(GeometricShape):
    """ Crea una instancia de una Barra de Dialogo (rectángulo), 
    heredando los métodos de la clase GeometricShape. """

    def __init__(self, screen, x, y, size, color=COLOR1):
        super().__init__(screen, x, y, size, color)
        self.points = [(0, 0),
                       (self.size, 0),                       
                       (self.size, self.size // 3),
                       (0, self.size // 3)]
        
    def undo(self):
        """ Método que sobrepinta con una figura transparente la
        instancia de barra de diálogo anteriormente creada. """

        self.color = TRANSPARENT
        self.draw()

    def add_text(self, text):
        """ Método que dibuja una Barra de Diálogo e incluye texto en su interior. """
        
        bg_color = COLOR1
        text_color = BLACK

        font = pygame.font.Font("assets/Atari.ttf", 22)
        rect_x, rect_y = self.x, self.y
        y = rect_y + 20

        self.draw()

        if isinstance(text, str):
            lines = textwrap.wrap(text, width=50)

            for line in lines:
                text_rendered = font.render(line, True, text_color, bg_color)
                self.screen.blit(text_rendered, (rect_x + 20, y))
                y += font.get_height() + 5

        elif isinstance(text, list):
            for text_item in text:
                lines = textwrap.wrap(text_item, width=50)

                for line in lines:
                    text_rendered = font.render(
                        line, True, text_color, bg_color)
                    self.screen.blit(text_rendered, (rect_x + 20, y))
                    y += font.get_height() + 5


# -----------------------------------------------------
# ----------------- DISPLAY ELEMENTOS -----------------
# -----------------------------------------------------

# GUI
# Dibuja todos elementos del tamaño seleccionado en la pantalla.
def draw_elements(screen, size_options, selected_size, main_menu):

    size = size_options[selected_size]

    if main_menu:
        decoration = Half_Diamond(screen, *size["bg_dec"], COLOR2)
        log = Diamond(screen, *size["bg_log"], COLOR2)
        menu = Diamond(screen, *size["menu"], COLOR1, alpha=200, image='assets/menu.png')
        corner = Triangle(screen, *size["corner"], COLOR1, image='assets/resize.png')

    else:
        decoration = Half_Diamond(screen, *size["bg_dec"], COLOR1)
        menu = Diamond(screen, *size["menu"], COLOR2)
        log = Diamond(screen, *size["bg_log"], COLOR1, image='assets/log.png')
        corner = Triangle(screen, *size["corner"], COLOR2, alpha=200, image='assets/back.png')

    off = Diamond(screen, *size["off"], COLOR1, image='assets/off.png')

    # Dibuja los elementos en la pantalla 
    menu.draw()
    decoration.draw()
    off.draw()
    corner.draw()
    log.draw()

    coor_off = off.get_screen_coordinates()
    coor_corner = corner.get_screen_coordinates()
    coor_log = log.get_screen_coordinates()

    coor_cal, coor_mail, coor_ai, coor_pc = coor_submenu(size["menu"])

    # Devuelve las coordenadas de cada elemento necesarias para el hover.
    return coor_off, coor_corner, coor_log, coor_cal, coor_mail, coor_ai, coor_pc

# Coordenadas de los triangulos que conforman el diamante del menu principal.
def coor_submenu(menu):

    # Coordenadas Calendario.
    coor_cal = [
        (menu[0] + menu[2] / 2, menu[1]),
        (menu[0], menu[1] + menu[2] / 2),
        (menu[0] + menu[2] / 2, menu[1] + menu[2] / 2)
    ]

    # Coordenadas Mail.
    coor_mail = [
        (menu[0] + menu[2] / 2, menu[1]),
        (menu[0] + menu[2], menu[1] + menu[2] / 2),
        (menu[0] + menu[2] / 2, menu[1] + menu[2] / 2)
    ]

    # Coordenadas AI Chat.
    coor_ai = [
        (menu[0] + menu[2] / 2, menu[1] + menu[2]),
        (menu[0], menu[1] + menu[2] / 2),
        (menu[0] + menu[2] / 2, menu[1] + menu[2] / 2)
    ]

    # Coordenadas Control PC.
    coor_pc = [
        (menu[0] + menu[2] / 2, menu[1] + menu[2]),
        (menu[0] + menu[2], menu[1] + menu[2] / 2),
        (menu[0] + menu[2] / 2, menu[1] + menu[2] / 2)
    ]

    return coor_cal, coor_mail, coor_ai, coor_pc

# HOVER
# El elemento queda bordeado si el ratón se situa sobre él.
def hover(screen, main_menu, mouse_pos, coor_off, coor_corner, coor_log, coor_cal, coor_mail, coor_ai, coor_pc):

    if main_menu:

        if is_inside_polygon(mouse_pos, coor_cal):
            pygame.draw.lines(screen, (255, 0, 255), True, coor_cal, 3)
        if is_inside_polygon(mouse_pos, coor_mail):
            pygame.draw.lines(screen, (255, 255, 0), True, coor_mail, 3)
        if is_inside_polygon(mouse_pos, coor_ai):
            pygame.draw.lines(screen, (0, 255, 0), True, coor_ai, 3)
        if is_inside_polygon(mouse_pos, coor_pc):
            pygame.draw.lines(screen, (0, 255, 255), True, coor_pc, 3)
    else:
        if is_inside_polygon(mouse_pos, coor_log):
            pygame.draw.lines(screen, (255, 255, 255), True, coor_log, 3)

    if is_inside_polygon(mouse_pos, coor_corner):
        pygame.draw.lines(screen, (255, 255, 255), True, coor_corner, 3)
    if is_inside_polygon(mouse_pos, coor_off):
        pygame.draw.lines(screen, (255, 255, 255), True, coor_off, 3)


# -----------------------------------------------------
# ------ COMPROBAR POSICIÓN DE RATON EN ELEMENTO ------
# -----------------------------------------------------

def is_inside_polygon(point, polygon):

    """Comprueba si el ratón está dentro del polígono. 
    Esto es de chatgpt, no voy a mentir, demasiadas mates."""
    
    x, y = point
    vertices = polygon
    num_vertices = len(vertices)

    total_area = get_polygon_area(vertices)

    sum_areas = 0
    for i in range(num_vertices):
        v1 = vertices[i]
        v2 = vertices[(i+1) % num_vertices]
        sum_areas += getArea2((x, y), v1, v2)

    return abs(total_area - sum_areas) < 1e-6

def getArea2(pointA, pointB, pointC):
    x1, y1 = pointA
    x2, y2 = pointB
    x3, y3 = pointC
    return abs((x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))/2.0)

def get_polygon_area(vertices):
    num_vertices = len(vertices)
    area = 0
    for i in range(num_vertices):
        v1 = vertices[i]
        v2 = vertices[(i+1) % num_vertices]
        area += v1[0]*v2[1] - v1[1]*v2[0]
    return abs(area) / 2.0
