import tkinter as tk
import socket
import threading

# Conectarse al servidor
#Aquí se crea un socket del cliente y se conecta al servidor en la dirección IP "127.0.0.1" (localhost) y el puerto 2000.
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 2000))

# Crear la ventana principal
window = tk.Tk()
window.title("Triqui")

turno = 0  # Inicializar el turno en el cliente
player_symbol = None

#juego_iniciado se establece en False para indicar que el juego aún no ha comenzado, y puntuacion se inicializa en 0.
# Variable para verificar si el juego ha comenzado
juego_iniciado = False

puntuacion = 0

# Función para enviar mensajes al servidor
def enviar_mensaje(mensaje):
    client.send(mensaje.encode("utf-8"))

def actualizar_tablero(movimiento, jugador_simbolo):
    tablero[movimiento] = jugador_simbolo
    botones[movimiento].config(text=jugador_simbolo)


#Esta función maneja las respuestas del servidor, actualizando la interfaz gráfica 
# y mostrando mensajes en la consola según el tipo de respuesta recibida.
# Función para manejar las respuestas del servidor
def manejar_respuesta():
    global juego_iniciado, turno, player_symbol, puntuacion

    while True:
        data = client.recv(1024).decode("utf-8")
        if data:
            data_parts = data.split("#")
            if data_parts[0] == "BIENVENIDA":
                print("¡Bienvenido al juego de Triqui!")
                juego_iniciado = True
            elif data_parts[0] == "INSCRIBIR":
                if data_parts[1] == "OK":
                    print("Inscripción exitosa.")
                    nombre_entry.config(state=tk.DISABLED)
                    inscribir_button.config(state=tk.DISABLED)
                    player_symbol = data_parts[3]
                elif data_parts[1] == "NOK":
                    error_text = data_parts[2]
                    print(f"Error de inscripción: {error_text}")
            elif data_parts[0] == "TURNO":
                turno = int(data_parts[1])
                if turno == 1:
                    print("Es tu turno. Puedes hacer un movimiento.")
                else:
                    print("Es el turno del oponente.")
            elif data_parts[0] == "JUGADA":
                estado = data_parts[1]
                movimiento = int(data_parts[2])
                jugador_simbolo = data_parts[3]
                if estado == "OK" and turno == 1:
                    # Actualizar el tablero después de recibir el movimiento
                    window.after(0, actualizar_tablero, movimiento, jugador_simbolo)
                elif estado == "NOK":
                    error_text = data_parts[3]
                    print(f"Error en la jugada: {error_text}")
            elif data_parts[0] == "OK":
                ganador = data_parts[1]
                print(f"¡{ganador} ha ganado!")
            elif data_parts[0] == "NOK":
                error_text = data_parts[1]
                print(f"Error: {error_text}")
            elif data_parts[0] == "PUNTUACION":
                puntuacion = int(data_parts[2])
                print(f"Puntuación: {puntuacion}")
                window.after(0, actualizar_puntuacion)

# Función para inscribir al jugador
#Esta función se llama cuando el jugador intenta inscribirse. 
# Obtiene el nombre del jugador de la entrada de texto y envía 
# un mensaje al servidor para procesar la inscripción.
def inscribir_jugador():
    nombre = nombre_entry.get()
    enviar_mensaje(f"#INSCRIBIR#{nombre}#")

#Esta función se llama cuando el jugador hace clic en un botón del tablero. 
# Verifica si el juego ha comenzado y es el turno del jugador, 
# luego envía un mensaje al servidor indicando el movimiento.
# Función para hacer un movimiento
def hacer_movimiento(movimiento):
    global juego_iniciado
    if juego_iniciado and turno == 0:
        if tablero[movimiento] == " ":
            enviar_mensaje(f"#JUGADA#{movimiento}#")
    else:
        print("Esperando a que ambos jugadores se inscriban y el juego comience.")


# Crear la ventana de inscripción
""" window = tk.Tk()
window.title("Triqui") """
inscripcion_frame = tk.Frame(window)
inscripcion_frame.pack()
nombre_label = tk.Label(inscripcion_frame, text="Ingresa tu nombre:")
nombre_label.pack(side=tk.LEFT)
nombre_entry = tk.Entry(inscripcion_frame)
nombre_entry.pack(side=tk.LEFT)
inscribir_button = tk.Button(inscripcion_frame, text="Inscribirse", command=inscribir_jugador)
inscribir_button.pack(side=tk.LEFT)

def actualizar_puntuacion():
    label_puntuacion.config(text=f"Puntuación: {puntuacion}")

# Crear una etiqueta para mostrar la puntuación
label_puntuacion = tk.Label(window, text="Puntuación: 0")
label_puntuacion.pack()

#Estas líneas crean la interfaz gráfica para el tablero del juego con nueve botones que representan 
# las celdas del triqui. Cada botón tiene una función asociada (hacer_movimiento) 
# que se activa cuando se hace clic.
# Crear la ventana del juego
juego_frame = tk.Frame(window)
juego_frame.pack()
tablero = [" "] * 9
botones = []
for i in range(9):
    boton = tk.Button(juego_frame, text=" ", width=5, height=2, command=lambda i=i: hacer_movimiento(i))
    boton.grid(row=i // 3, column=i % 3)
    botones.append(boton)

# Iniciar un hilo para manejar las respuestas del servidor
thread = threading.Thread(target=manejar_respuesta)
thread.daemon = True
thread.start()

# Iniciar la ventana principal
window.mainloop()
