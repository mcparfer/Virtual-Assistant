import base64
import datetime
import logging
import os
import threading
import time

import pyttsx3
import pyautogui
import speech_recognition as sr
from dateutil import parser
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from playwright.sync_api import sync_playwright
from pydub import AudioSegment
from pydub.playback import play

my_data = {"running": True} # Indicador de si la app esta activa.

# -----------------------------------------------------
# --------------- CONFIGURACIÓN LOGGING ---------------
# -----------------------------------------------------

logging.basicConfig(filename='app.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)


# -----------------------------------------------------
# -------------- CREDENCIALES DE GOOGLE ---------------
# -----------------------------------------------------

TOKEN_PATH = 'auth/token.json'
CREDENTIALS_PATH = 'auth/credentials.json'

# Areas de acceso que el usuario debe permitir a mi app.
SCOPES = [  
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

creds = None

if os.path.exists(TOKEN_PATH):  # Comprueba la existencia del token del usuario.
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        logging.info("User authentication completed.")
    except Exception as e:
        logging.warning(f"Failed to load credentials from file {TOKEN_PATH}: {str(e)}")

else:
    creds = None

if not creds or not creds.valid:    # Si no existe token o el existente no es válido...
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logging.info("User token has been refreshed.")
        except Exception as e:
            logging.error(f"Failed to refresh credentials: {str(e)}")

    else:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)   # El usuario debe logarse con su cuenta de Google.
            logging.info("User authentication completed.")
        except Exception as e:
            logging.error(f"Failed user authentication: {str(e)}")

    if creds: # Actualiza el token del usuario.
        try:
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
            logging.info(f"Token has been saved to the file {TOKEN_PATH}.")
        except Exception as e:
            logging.error(f"Failed to save token to the file {TOKEN_PATH}: {str(e)}")


# -----------------------------------------------------
# ---------------- MANEJO CANCELACIONES ---------------
# -----------------------------------------------------

class CancelException(Exception):
    """ Clase de excepción para cancelar la ejecución de una
    funcionalidad en ejecución. """

    def __init__(self):
        self.msg = "Functionality execution has been canceled."
        super().__init__(self.msg)
    
    def display_cancel(self, bar, func):    # Muestra un mensaje de cancelación.
        bar.add_text(self.msg)
        text_to_speech(self.msg)
        logging.warning(f"{func} functionality execution has been canceled.")

    @staticmethod   # Método encargado de comprobar y levantar la excepción.
    def check_cancel(str):
        if "cancel" in str and "operation" in str:
            raise CancelException
        
        
# -----------------------------------------------------
# -------- MANEJO DEL HISTORIAL DE CONVERSACIÓN -------
# -----------------------------------------------------

class ChatHistory:
    """ Clase que maneja y almacena el historial del chat
    entre el usuario y el asistente virtual. """

    chat_txt = ''
    
    @staticmethod   # Limpia el historial del chat.
    def clear_log():
        ChatHistory.chat_txt = ''

    @staticmethod   # Añade texto + timestamp.
    def add_text(text):
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        ChatHistory.chat_txt += timestamp + text + "\n"

    @staticmethod   # Añade un título.
    def add_title(title):
        ChatHistory.chat_txt += "*** " + title + " ***\n"
    
    @staticmethod   # Obtiene el contenido del historial del chat.
    def get_log_txt():
        return ChatHistory.chat_txt
    

# -----------------------------------------------------
# ------------- FUNCIONES DE TEXTO Y HABLA ------------
# -----------------------------------------------------

def play_sound():
    """ Reproduce el sonido que indica la activación del micrófono. """
    sound = AudioSegment.from_wav("assets/bleep.wav")
    play(sound)


def speech_to_text(bar):
    """ Convierte el audio grabado por el micrófono del PC a texto. """

    times = 0   # Intentos de capturar audio.
    r = sr.Recognizer()
    with sr.Microphone() as source_mic: # Instancia del micrófono del PC.

        while True:
            if not my_data["running"]:  # Comprueba que la app esté activa.
                logging.warning("Failed to convert speech to text: App is not running.")
                break

            sound_thread = threading.Thread(target=play_sound)
            sound_thread.start()    # Alerta al usuario de que puede hablar.
            
            r.adjust_for_ambient_noise(source_mic, duration=0.5)    # Ajuste de ruido.

            try:
                audio = r.listen(source_mic, timeout=5) # Recoge la entrada de audio.

                try:
                    text = r.recognize_google(audio, language="en-US").lower()  # Convierte audio a texto.
                    ChatHistory.add_text(f"User: {text.capitalize()}.") # Registro del user en el History Chat.

                    CancelException.check_cancel(text)  # Comprueba si hay que cancelar la acción.
                    return text

                except sr.UnknownValueError:    # La entrada de audio es ininteligible.
                    logging.warning("Failed to convert speech to text: Speech is unintelligible.")

                    times += 1
                    if times >= 3:
                        text = "Sorry, I can't understand what you're trying to say. Try later in a quieter environment."
                        bar.add_text(text)
                        text_to_speech(text)
                        raise CancelException
                    
                    text = "Sorry, I couldn't hear you. Can you repeat it?"
                    #bar.add_text(text)
                    text_to_speech(text)
                    continue
                
                except sr.RequestError: # Sin conexión a internet.
                    logging.error("Failed to convert speech to text: No internet connection.")
                    
                    text = "No internet connection. Please check your device's internet connection."
                    bar.add_text(text)
                    text_to_speech(text)
                    raise CancelException

            except sr.WaitTimeoutError: # El micrófono no escucha nada.
                logging.warning("Failed to convert speech to text: No audio input has been detected.")

                times += 1
                if times >= 3:
                    text = "Sorry, I can't hear anything. No audio input has been detected."
                    bar.add_text(text)
                    text_to_speech(text)
                    raise CancelException

                text = "No audio input has been detected. Try again."
                #bar.add_text(text)
                text_to_speech(text)
                continue

            except CancelException as e:    # En caso de cancelación, lo maneja la funcionalidad.
                raise

            except Exception as e:
                error_message = f"Failed to convert speech to text: {str(e)}."
                
                logging.error(error_message)
                bar.add_text(error_message)
                text_to_speech(error_message)
                break


def text_to_speech(text):
    """ Convierte texto a audio. """
    
    engine = pyttsx3.init() # Inicializamos el engine.
    
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)   # Voz inglesa.
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-50)     # Velocidad de la voz.

    try:
        engine.say(text)    # Convierte el texto en audio.
        engine.runAndWait()
        ChatHistory.add_text(f"VA: {text}.")    # Registro del VA en el History Chat.

    except Exception as e:
        logging.error(f"Failed to convert text to speech: {str(e)}")


def virtual_assistant_dialogue(virtual_ask, bar):
    """ El VA inicia o continúa la comunicación con el usuario
    y posteriormente escucha la respuesta del usuario. Finalmente devuelve 
    la respuesta del usuario para que pueda volver a ser analizada. """
    
    text_to_speech(virtual_ask) # Convierte el texto del VA en audio
    return speech_to_text(bar)  # Devuelve el audio del usuario en texto.


# -----------------------------------------------------
# ----------- FUNCIONALIDAD: GOOGLE CALENDAR ----------
# -----------------------------------------------------

def google_calendar_show(bar):
    """ Muestra los siguientes 5 futuros eventos en el calendario. """

    logging.info("Calendar Functionality: Displaying next events...")

    now = datetime.datetime.utcnow().isoformat() + 'Z'   # Fecha y hora actual.
   
    try:
        service = build('calendar', 'v3', credentials=creds, static_discovery=False) # Servicio de Google Calendar.

        events = service.events().list(calendarId='primary', 
                                       timeMin=now, 
                                       maxResults=5,
                                       singleEvents=True, 
                                       orderBy='startTime'
                                       ).execute().get('items', []) # Lista con los próximos 5 eventos.

        if not events:  # Si no hay eventos próximos...
            bar.add_text('No upcoming events found.')
            text_to_speech('No upcoming events found.')

        else:   # Si hay eventos próximos...
            events_list = ["--- NEXT EVENTS ---"]
            virtual_text = ""

            for i, event in enumerate(events):

                # Fecha de inicio.
                start = event['start'].get('dateTime', event['start'].get('date'))
                str_date = datetime.datetime.fromisoformat(start).strftime('%d of %B %Y at %H:%M')
                str_date_spoken = datetime.datetime.fromisoformat(start).strftime('%d of %B %Y at %Hh%Mm')

                # Nombre del evento.
                event_summary = event['summary']

                if i == 0:  # El asistente solo lee el primer evento.
                    virtual_text = f"It seems your next event '{event_summary}' is at {str_date_spoken}."

                events_list.append(str_date + " -> Event: " + event_summary)
                ChatHistory.add_text(str_date + " -> Event: " + event_summary)

            # Y muestra el resto de eventos en una lista.
            bar.add_text(events_list)
            text_to_speech(virtual_text)

    except HttpError as e:
        logging.error(f"Failed to retrieve calendar events. No internet connection: {str(e)}")

        error_message = "Failed to retrieve calendar events. Please check your device's internet connection."
        bar.add_text(error_message)
        text_to_speech(error_message)

    except Exception as e:
        logging.error(f"Failed to retrieve calendar events: {str(e)}")

        error_message = "Failed to retrieve calendar events."
        bar.add_text(error_message)
        text_to_speech(error_message)


def google_calendar_create(bar):
    """ Crea un nuevo evento en el calendario. """

    logging.info("Calendar Functionality: Creating a new event...")

    try:
        service = build('calendar', 'v3', credentials=creds, static_discovery=False) # Servicio de Google Calendar.

        # Esto se muestra en el código de dialogo inicial.
        event_info = ["--- EVENT INFORMATION ---",
                      "Specify the event...",
                      "Specify the description of the event...",
                      "Specify the start time... Example: 1 April 9pm",
                      "Specify the end time... Example: 2 April 10am"]
        bar.add_text(event_info)
        
        summary = virtual_assistant_dialogue(event_info[1], bar)    # Solicita campo del evento.
        event_info[1] = f"Event: {summary.capitalize()}"            # Actualiza el cuadro de diálogo.
        bar.add_text(event_info)                                    # Muestra el nuevo cuadro de diálogo.

        description = virtual_assistant_dialogue(event_info[2], bar)
        event_info[2] = f"Description: {description.capitalize()}"
        bar.add_text(event_info)
        
        start = None
        end = None

        while not start:
            date_input = virtual_assistant_dialogue(event_info[3], bar)
            try:
                start = parser.parse(date_input).isoformat()
            except ValueError:
                text_to_speech("Invalid date format. Please try again.")

        event_info[3] = f"Start Time: {start}"
        bar.add_text(event_info)
        
        while not end:
            date_input = virtual_assistant_dialogue(event_info[4], bar)
            try:
                check_end = parser.parse(date_input).isoformat()
                if start >= check_end:
                    text_to_speech("End date should be later than the start date. Please try again.")
                else:
                    end = check_end
            except ValueError:
                text_to_speech("Invalid date format. Please try again.")

        event_info[4] = f"End Time: {end}"
        bar.add_text(event_info)

        # Creación del objecto evento.
        event = {
            'summary': summary.capitalize(),
            'description': description.capitalize(),
            'start': {
                'dateTime': start + '+02:00',
            },
            'end': {
                'dateTime': end + '+02:00'
            }
        }
        event = service.events().insert(calendarId='primary', body=event).execute()     # Inserción.
        [ChatHistory.add_text(elem) for elem in event_info]     # Registro del evento en el Chat History.
        ChatHistory.add_text('Event created: %s' % (event.get('htmlLink')))

        text_to_speech("The new event has been succesfully added.")
        time.sleep(5)
    
    except CancelException as e:
        raise

    except HttpError as e:
        logging.error(f"Failed to create a new event. No internet connection: {str(e)}")

        error_message = "Failed to create a new event. Please check your device's internet connection."
        bar.add_text(error_message)
        text_to_speech(error_message)

    except Exception as e:
        logging.error(f"Failed to create a new event: {str(e)}")

        error_message = "Failed to create a new event."
        bar.add_text(error_message)
        text_to_speech(error_message)


def cal_func(bar):
    """ Gestiona la funcionalidad de Calendario. """

    logging.info('Initializing Calendar Functionality...')

    try:
        ChatHistory.clear_log() # Limpia el Chat History anterior.
        ChatHistory.add_title("GOOGLE CALENDAR FUNCTIONALITY")

        va_text = "You are in Calendar. What would you like to do?"
        bar.add_text(va_text)                
        user_text = virtual_assistant_dialogue(va_text, bar)

        if "show" in user_text:
            google_calendar_show(bar)
        elif "create" in user_text:
            google_calendar_create(bar)
        else:
            logging.warning("Calendar Functionality: Invalid user request.")  # Petición invalida
            error_message = [
                "I'm sorry, I can't understand your request.",
                "Please use one of the following keywords:",
                "- SHOW: to display your upcoming events.",
                "- CREATE: to generate a new event."
            ]
            bar.add_text(error_message)
            text_to_speech(' '.join(error_message[:2]))

    except CancelException as e:
        e.display_cancel(bar, "Calendar")
    
    except Exception as e:
        error_message = f"Failed to open Calendar Functionality: {str(e)}."

        logging.error(error_message)
        bar.add_text(error_message)
        text_to_speech(error_message)


# -----------------------------------------------------
# ------------ FUNCIONALIDAD: GOOGLE GMAIL ------------
# -----------------------------------------------------

def get_email_content(service, msg_id):
    """ Obtiene información de cada email a partir de su ID. """

    try:
        message = service.users().messages().get(userId='me', id=msg_id).execute()

        # Obtenemos los datos que mostraremos al usuario a través de las cabeceras.
        headers = message['payload']['headers']
        src = [header['value']
               for header in headers if header['name'].lower() == 'from'][0]
        date = [header['value']
                for header in headers if header['name'].lower() == 'date'][0]
        subject = [header['value']
                   for header in headers if header['name'].lower() == 'subject'][0]
        return src, date, subject

    except HttpError as e:
        raise
    except Exception as e:
        raise


def google_mail_show(bar):
    """ Muestra los últimos 10 emails sin leer. """

    logging.info('Email Functionality: Displaying unread emails...')

    try:
        service = build('gmail', 'v1', credentials=creds, static_discovery=False)   # Servicio de Gmail.

        messages = service.users().messages().list(userId='me',
                                                   labelIds=['INBOX'],
                                                   q='category:primary is:unread',
                                                   maxResults=5
                                                   ).execute().get('messages', [])  # Últimos 5 correos no leídos.

        if not messages:    # Si no hay correos sin leer...
            bar.add_text('You have no unread messages.')
            text_to_speech('You have no unread messages.')

        else:    # Si hay correos sin leer...
            bar.add_text('These are your last unread emails...')
            text_to_speech('These are your last unread emails...')

            for message in messages:
                msg_list = ["LAST UNREAD EMAILS: "]

                src, date, subject = get_email_content(service, message['id'])
                msg_list.append(f'From: {src}')
                msg_list.append(f'Date: {date}')
                msg_list.append(f'Subject: {subject}')

                [ChatHistory.add_text(elem) for elem in msg_list]   # Resgistro en Chat History.
                bar.add_text(msg_list)
                time.sleep(3) # Muestra un correo cada 3 segundos.

    except HttpError as e:
        logging.error(f"Failed to retrieve unread emails. No internet connection: {str(e)}")

        error_message = "Failed to retrieve unread emails. Please check your device's internet connection."
        bar.add_text(error_message)
        text_to_speech(error_message)

    except Exception as e:
        logging.error(f"Failed to retrieve unread emails: {str(e)}")

        error_message = "Failed to retrieve unread emails."
        bar.add_text(error_message)
        text_to_speech(error_message)


def google_mail_create(bar):
    """ Crea y envía un nuevo correo. """

    logging.info('Email Functionality: Creating a new mail...')

    try:
        service = build('gmail', 'v1', credentials=creds, static_discovery=False)   # Servicio de Gmail.

        # Esto se muestra en el código de dialogo inicial.
        email_info = ["EMAIL INFORMATION: ",
                    "Specify the receiver name...",
                    "Specify the receiver domain...",
                    "Specify the subject...",
                    "Specify the message..."]
        bar.add_text(email_info)

        to_name = virtual_assistant_dialogue(email_info[1], bar).replace(" ", "").lower()
        email_info[1] = f"To: {to_name}"
        bar.add_text(email_info)

        to_domain = virtual_assistant_dialogue(email_info[2], bar)
        email_info[1] = f"To: {to_name}@{to_domain}"
        del email_info[2]
        bar.add_text(email_info)

        subject = virtual_assistant_dialogue(email_info[2], bar)
        email_info[2] = f"Subject: {subject.capitalize()}"
        bar.add_text(email_info)

        msg_text = virtual_assistant_dialogue(email_info[3], bar)
        email_info[3] = f"Message: {msg_text.capitalize()}"
        bar.add_text(email_info)

        message = MIMEText(msg_text.capitalize())    # Crea un objeto mensaje a través del contenido del mismo.
        message['to'] = f"{to_name}@{to_domain}"    # Modifica los campos.
        message['subject'] = subject.capitalize()

        # El mensaje y su contenido se codifican para que puedan ser enviados de forma segura.
        email = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}
        message_result = service.users().messages().send(
            userId="me",
            body=email
        ).execute()
        logging.info('Message Id: %s' % message_result['id'])

        [ChatHistory.add_text(elem) for elem in email_info]    # Registro nuevo correo en Chat History.
        text_to_speech("The new email has been succesfully send.")
        time.sleep(5)

    except CancelException as e:
        raise
    
    except HttpError as e:
        logging.error(f"Failed to create and sent the new email. No internet connection: {str(e)}")

        error_message = "Failed to create and sent the new email. Please check your device's internet connection."
        bar.add_text(error_message)
        text_to_speech(error_message)

    except Exception as e:
        logging.error(f"Failed to create and sent the new email: {str(e)}")

        error_message = "Failed to create and sent the new email."
        bar.add_text(error_message)
        text_to_speech(error_message)


def mail_func(bar):
    """ Gestiona la funcionalidad de Email. """
    logging.info('Initializing Email Functionality...')

    try:
        ChatHistory.clear_log() # Limpia el Chat History.
        ChatHistory.add_title("GOOGLE EMAIL FUNCTIONALITY")

        virtual_text = "You are in Email. What would you like to do?"
        bar.add_text(virtual_text)
        user_text = virtual_assistant_dialogue(virtual_text, bar)

        if "show" in user_text:
            google_mail_show(bar)                     
        elif "create" in user_text:
            google_mail_create(bar)
        else:
            
            logging.warning("Email Functionality: Invalid user request.") # Petición invalida
            error_message = [
                "I'm sorry, I can't understand your request.",
                "Please use one of the following keywords:",
                "- SHOW: to display your last unread emails.",
                "- CREATE: to generate a new email."
            ]
            bar.add_text(error_message)
            text_to_speech(' '.join(error_message[:2]))

    except CancelException as e:
        e.display_cancel(bar, "Email")
    
    except Exception as e:
        error_message = f"Failed to open Email Functionality: {str(e)}."

        logging.error(error_message)
        bar.add_text(error_message)
        text_to_speech(error_message)
        

# -----------------------------------------------------
# --------------- FUNCIONALIDAD: AI CHAT --------------
# -----------------------------------------------------

def ai_func(bar):
    """ A través de una herramienta de automatización diseñada para navegadores,
    hace uso de las AI disponibles en internet para obtener una respuesta de caracter
    general a partir de la entrada de voz generada por el usuario. """

    logging.info('Initializing AI Chat...')

    ChatHistory.clear_log()  # Prepara el log del dialogo.
    ChatHistory.add_title("AI CHAT FUNCTIONALITY")

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)  # Navegador no visible para el usuario.
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.aichatting.net/")

            virtual_text = "What would you like to ask?"
            bar.add_text(virtual_text)
            user_input = virtual_assistant_dialogue(virtual_text, bar)

            number = 3  # Parametro de configuración de la pag web usada.

            while True:     
                # Se busca y rellena el elemento donde el usuario introduce la informacion.
                page.get_by_placeholder("Enter text here...").fill(user_input + '. Answer in less than 50 words.', timeout=10000)
                page.get_by_placeholder("Enter text here...").press("Enter")

                # Espera cierta condición que implica que la IA ya ha terminado de escribir su respuesta.
                page.get_by_placeholder("Enter text here...").fill(' ', timeout=10000)

                # Extrae e imprime el contenido del elemento con la respuesta de la IA.
                output = page.query_selector(f"li:nth-child({number}) span").inner_text()

                bar.add_text(output)
                text_to_speech(output)

                if "bye" in user_input:     # El bucle se rompe cuando el usuario se despide.
                    break

                user_input = speech_to_text(bar)
                number += 2

            context.close()
            browser.close()
    
    except CancelException as e:
        e.display_cancel(bar, "AI Chat")

    except HttpError as e:
        logging.error(f"Failed to connect to AI Chat. No internet connection: {str(e)}")

        error_message = "Failed to connect to AI Chat. Please check your device's internet connection."
        bar.add_text(error_message)
        text_to_speech(error_message)

    except Exception as e:
        logging.error(f"Failed to connect to AI Chat: {str(e)}")

        error_message = "Failed to connect to AI Chat."
        bar.add_text(error_message)
        text_to_speech(error_message)


# -----------------------------------------------------
# ------------- FUNCIONALIDAD: PC CONTROL -------------
# -----------------------------------------------------

def open_app(user_text, bar):
    """ Abre la barra de búsqueda y escribe el nombre de la app. """
    
    logging.info("Control PC Functionality: Opening the app...")
    
    words = user_text.split()
    index = words.index("open")

    if words[-1] == "open":
        error_message = f"I'm sorry. You haven't specify an app to open."

        bar.add_text(error_message)
        text_to_speech(error_message)
        logging.warning(error_message)

        raise CancelException
    
    else:
        app = words[index + 1]  # La palabra que sigue a open es la aplicacion que abriremos.
        
        pyautogui.press('win')  # Utiliza la barra de busqueda para buscar
        time.sleep(1)
        pyautogui.typewrite(app)
        time.sleep(1)
        pyautogui.press('enter')

        text = f"Opening the app {app}..."
        bar.add_text(text)
        text_to_speech(text)

        # Tras 3 segundos, comprueba si se ha abierto.
        time.sleep(3)
        def get_title(arr, app):
            for title in arr:
                title_lower = title.lower()
                if app in title_lower:
                    return title
            return "" 

        window_app = get_title(pyautogui.getAllTitles(), app)

        if window_app != "":
            text = f"The application {app} has been succesfully open."

            bar.add_text(text)
            text_to_speech(text)
            logging.info(text)
        
        else:
            error_message = f"Failed to open {app} application."

            bar.add_text(error_message)
            text_to_speech(error_message)
            logging.warning(error_message)


def close_app(user_text, bar):
    """Cierra la aplicación, sin importar si se encuentra en primer plano o no."""

    logging.info("Control PC Functionality: Closing the app...")

    words = user_text.split()
    index = words.index("close")

    if words[-1] == "close":
        error_message = f"I'm sorry. You haven't specify an app to close."

        bar.add_text(error_message)
        text_to_speech(error_message)
        logging.warning(error_message)
        
        raise CancelException
    
    else:    
        app = words[index + 1]      # La palabra que sigue a close es la aplicacion que cerraremos.

        # Obtiene el nombre de la pestaña y busca su PID.
        def get_title(arr, app):
            for title in arr:
                title_lower = title.lower()
                if app in title_lower:
                    return title
            return "None" 

        window_app = get_title(pyautogui.getAllTitles(), app)
        output = os.popen(f'tasklist /fi "WindowTitle eq {window_app}" /fo csv').read().strip()

        if ":" in output.split("\n")[0]:
            error_message = f"There is no {app} application open."

            bar.add_text(error_message)
            text_to_speech(error_message)
            logging.warning(error_message) 

        else:              
            pid = output.split("\n")[1].split(",")[1].replace('"', '')

            output = os.popen(f'taskkill /PID {pid}').read().strip()    # Ejecuta el comando para cerrar la aplicación (Windows).

            # Comprueba si se ha cerrado.
            if not "ERROR" in output:
                text = f"The application {app} has been succesfully closed."

                bar.add_text(text)
                text_to_speech(text)
                logging.info(text)
            
            else:
                error_message = f"Failed to close {app} application."

                bar.add_text(error_message)
                text_to_speech(error_message)
                logging.warning(error_message)


def screenshot(bar):
    """Realiza una captura de pantalla."""

    logging.info("Control PC Functionality: Taking a screenshot...")

    try:
        virtual_text = "Do you want to save the printscreen afterwards?"
        bar.add_text(virtual_text)
        user_input = virtual_assistant_dialogue(virtual_text, bar)

        text = ""

        if "yes" in user_input:
            pyautogui.hotkey('win', 'printscreen')
            text = "The screenshot has been successfully saved in your Images Folder."
        else:
            pyautogui.press('printscreen')
            text = "The screenshot has been successfully taken."

        bar.add_text(text)
        text_to_speech(text)
        logging.info(text)
    
    except CancelException as e:
        raise


def volume_level(user_text, bar):
    """Ajusta el nivel de volumen."""

    logging.info("Control PC Functionality: Changing volume level...")

    text = ""

    if "up" in user_text:
        pyautogui.press('volumeup', presses=15, interval=0.1)
        text = "The volume has been successfully raised."
    elif "down" in user_text:
        pyautogui.press('volumedown', presses=15, interval=0.1)
        text = "The volume has been successfully lowered."
    else:
        pyautogui.press('volumemute')
        text = "The PC has been succesfully muted."

    bar.add_text(text)
    text_to_speech(text)
    logging.info(text)


def control_func(bar):
    """ Gestiona la funcionalidad de Control PC. """

    logging.info('Initializing Control PC Functionality...')

    try: 
        ChatHistory.clear_log() # Prepara el log del dialogo.
        ChatHistory.add_title("CONTROL PC")

        virtual_text = "You are in Controls. What do you want to do?"
        bar.add_text(virtual_text)
        user_text = virtual_assistant_dialogue(virtual_text, bar)

        if "open" in user_text:
            open_app(user_text, bar)
        elif "close" in user_text:
            close_app(user_text, bar)
        elif "screen" in user_text:
            screenshot(bar)
        elif "volume" in user_text or "sound" in user_text:
            volume_level(user_text, bar)
        else:
            logging.warning("PC Control Functionality: Invalid user request.") # Petición invalida
            error_message = [
                "I'm sorry, I can't understand your request.",
                "Please use one of the following keywords:",
                "- OPEN / CLOSE: to open / close an application.",
                "- SCREEN: to taken a screenshot.",
                "- VOLUME (UP/DOWN/MUTE): to control PC volume level."
            ]
            bar.add_text(error_message)
            text_to_speech(' '.join(error_message[:2]))

    except CancelException as e:
        e.display_cancel(bar, "PC Control")
    
    except Exception as e:
        error_message = f"Failed to open PC Control Functionality: {str(e)}."

        logging.error(error_message)
        bar.add_text(error_message)
        text_to_speech(error_message)


# -----------------------------------------------------
# ------------ FUNCIONALIDAD: CHAT HISTORY ------------
# -----------------------------------------------------

def chat_history_func(bar):
    """Devuelve una salida con la conversación del asistente y el
    usuario de la funcionalidad anterior."""

    logging.info("Initializing Chat History Functionality...")

    try:
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')  # Ruta del directorio del usuario.
        file_path = os.path.join(desktop, 'chat_history.txt')
        file = open(file_path, 'w')             # Crea el fichero.
        file.write(ChatHistory.get_log_txt())   # Rellena el fichero.

        text = "The Chat history output has been saved to your desktop."

        bar.add_text(text)
        text_to_speech(text)
        logging.info(text)
    
    except Exception as e:
        error_message = f"Failed to create Chat History output: {str(e)}."

        logging.error(error_message)
        bar.add_text(error_message)
        text_to_speech(error_message)