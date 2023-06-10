import sys
import pygame
import win32api
import win32con
import win32gui
import threading
import logging

from gui import *
from ui_functions import my_data, cal_func, mail_func, ai_func, control_func, chat_history_func

# -----------------------------------------------------
# --------------- CONFIGURACIÓN LOGGING ---------------
# -----------------------------------------------------

# Configuración de log
logging.basicConfig(filename='app.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)


# -----------------------------------------------------
# ---------- CONFIGURACION VENTANA ASISTENTE ----------
# -----------------------------------------------------

# Inicializa pygame
pygame.init()

# Ventana Asistente
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
hwnd = pygame.display.get_wm_info()["window"]

# Añade transparencias y siempre en primer plano.
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(
    hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
win32gui.SetLayeredWindowAttributes(
    hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)
win32gui.SetWindowPos(
    hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

# Obtiene el tamaño de la pantalla
WIDTH, HEIGHT = screen.get_width(), screen.get_height()


# -----------------------------------------------------
# ------------- CONFIGURACIÓN ASISTENTE ---------------
# -----------------------------------------------------

size_options = {
    "small": {
        "bar": [WIDTH - 900, HEIGHT - 250, 600], "menu": [WIDTH - 225, HEIGHT - 300, 202],
        "off": [WIDTH - 285, HEIGHT - 176, 90], "corner": [WIDTH - 150, HEIGHT - 150, 150],
        "bg_log": [WIDTH - 127, HEIGHT - 337, 150], "bg_dec": [WIDTH - 247, HEIGHT - 150, 225]
    },
    "large": {
        "bar": [WIDTH - 1000, HEIGHT - 280, 600], "menu": [WIDTH - 300, HEIGHT - 400, 270],
        "off": [WIDTH - 380, HEIGHT - 235, 120], "corner": [WIDTH - 200, HEIGHT - 200, 200],
        "bg_log": [WIDTH - 170, HEIGHT - 450, 200], "bg_dec": [WIDTH - 330, HEIGHT - 200, 300]
    }
}

# Tamaños del asistente
size, nosize = "small", "large"

# FPS
clock = pygame.time.Clock()

# Estado inicial menu
main_menu = True

# Hilo secundario donde actuará la funcionalidad para no bloquear el main loop.
thread = None


# -----------------------------------------------------
# ---------------- FUNCION PRINCIPAL ------------------
# -----------------------------------------------------

def main():

    global size, nosize
    global main_menu
    global thread

    # BUCLE PRINCIPAL
    while True:

        # Posición del ratón
        mouse_pos = pygame.mouse.get_pos()

        # Display
        coordinates = draw_elements(screen, size_options, size, main_menu)
        coor_off, coor_corner, coor_log, coor_cal, coor_mail, coor_ai, coor_pc = coordinates

        # Hover
        hover(screen, main_menu, mouse_pos, *coordinates)

        # REGISTRO DE EVENTOS
        for event in pygame.event.get():

            # Creación instancia caja dialogo
            box_size = size_options[size]["bar"]
            bar = Bar(screen, *box_size)

            # Evento Alt + F4
            if event.type == pygame.QUIT:
                logging.info('You closed the app!')
                my_data["running"] = False
                
                pygame.quit()
                sys.exit()

            # Eventos de ratón.
            elif event.type == pygame.MOUSEBUTTONUP:

                # Menú principal
                if main_menu:

                    # Calendario.
                    if is_inside_polygon(mouse_pos, coor_cal):

                        main_menu = False
                        logging.info('You clicked Calendar!')
                        
                        thread = threading.Thread(target=cal_func, args=(bar,))
                        thread.start()

                    # Email.
                    if is_inside_polygon(mouse_pos, coor_mail):

                        main_menu = False
                        logging.info('You clicked Email!')

                        thread = threading.Thread(target=mail_func, args=(bar,))
                        thread.start()

                    # AI Chat.
                    if is_inside_polygon(mouse_pos, coor_ai):

                        main_menu = False
                        logging.info('You clicked AI Chat!')
                        
                        thread = threading.Thread(target=ai_func, args=(bar,))
                        thread.start()

                    # Control PC.
                    if is_inside_polygon(mouse_pos, coor_pc):

                        main_menu = False
                        logging.info('You clicked Control PC!')

                        thread = threading.Thread(target=control_func, args=(bar,))
                        thread.start()

                    # Cambiar tamaño asistente.
                    if is_inside_polygon(mouse_pos, coor_corner):

                        logging.info('You clicked Resize!')

                        screen.fill((0, 0, 0))
                        size, nosize = nosize, size

                # Dentro de una funcionalidad.
                else:

                    # Chat History
                    if is_inside_polygon(mouse_pos, coor_log):

                        main_menu = True
                        logging.info('You clicked Chat History!')

                        if not thread or not thread.is_alive():
                            thread = threading.Thread(target=chat_history_func, args=(bar,))
                            thread.start()

                    # Go Back to Main Menu.
                    if is_inside_polygon(mouse_pos, coor_corner):

                        main_menu = True
                        logging.info('You clicked Back!')

                # Botón de apagado.
                if is_inside_polygon(mouse_pos, coor_off):

                    logging.info('You clicked Off!')
                    my_data["running"] = False

                    pygame.quit()
                    sys.exit()

            # Eventos de teclado (cambia la posición del asistente).
            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_UP:
                    screen.fill((0, 0, 0))

                    for elem in size_options[size]:
                        size_options[size][elem][1] -= 4

                elif event.key == pygame.K_DOWN:
                    screen.fill((0, 0, 0))

                    for elem in size_options[size]:
                        size_options[size][elem][1] += 4


            # Limpia el cuadro de dialogo si no hay funcionalidades activas. 
            if not thread or not thread.is_alive():
                bar.undo()

            # Evita volver al menú principal mientras las funcionalidad este activa.
            else:
                main_menu = False

        # Actualiza la pantalla.
        pygame.display.update()
        clock.tick(20)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.critical(f"Error: {str(e)}")
    finally:
        pygame.quit()
        sys.exit()
