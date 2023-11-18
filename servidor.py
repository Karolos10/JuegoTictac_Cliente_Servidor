import socket
import threading

# Inicializa el servidor
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 2000))
server.listen(2)  # Acepta hasta 2 clientes

#Se inicializan estructuras de datos para mantener información sobre los clientes, 
# nombres de jugadores, estado del juego y manejar el acceso seguro a la variable 
# 'winner' mediante un Lock.
clients = []
player_names = {}
turn = 0  # Indica el turno de los jugadores   
game_board = [' '] * 9  # Tablero de juego
winner = None
winner_lock = threading.Lock()  # Lock para asegurar el acceso seguro a 'winner'

#Se inicializan variables para llevar la puntuación de los jugadores 
# y se establece el máximo de jugadores y puntuación necesarios para ganar.
# Agregar puntuación y partidas ganadas
player_scores = {0: 0, 1: 0}

MAX_PLAYERS = 2
MAX_SCORE = 3

#Se define una función broadcast para enviar un mensaje a todos los clientes conectados.
def broadcast(message):
    for client in clients:
        client.send(message.encode('utf-8'))

#Se define una función handle_client para manejar las acciones de un cliente, 
# como la inscripción y la inicialización del juego. También se inicia un hilo 
# para manejar los movimientos del jugador.
def handle_client(client, player):
    #Manejo de inscripciones y mensajes iniciales
    try:
        name = client.recv(1024).decode('utf-8')

        if name in player_names.values():
            client.send("#NOK#Nombre ya en uso. Elige otro nombre.#".encode('utf-8'))
            client.close()
        else:
            player_names[player] = name

        while len(player_names) < MAX_PLAYERS:
            pass

        # Envía un mensaje de inicio una vez que se han inscrito dos jugadores
        broadcast("BIENVENIDA")

        game_start_message = "#INSCRIBIR#OK#"
        for p in player_names.values():
            game_start_message += f"{p}#"
        broadcast(game_start_message)

        broadcast(f"#TURNO#{turn}#")  # Inicializar el turno
        # Iniciar un hilo para manejar los movimientos del jugador
        thread = threading.Thread(target=handle_move, args=(client, player, player_names[player]))
        thread.start()
    except ConnectionResetError:
        print("Conexión cerrada inesperadamente.")
        client.close()

#Se define una función handle_move para manejar los movimientos de los jugadores. 
# Se verifica la validez del movimiento y se actualiza el estado del juego.
def handle_move(client, player, player_symbol):
    global turn
    while True:
        move_data = client.recv(1024).decode('utf-8')
        data_parts = move_data.split("#")

        if len(data_parts) == 3 and data_parts[0] == "JUGADA":
            move_str = data_parts[1]
            try:
                move = int(move_str)
            except ValueError:
                current_player.send("#NOK#Movimiento no válido. Inténtalo de nuevo.#".encode('utf-8'))
                continue

            if 0 <= move < 9 and game_board[move] == ' ' and player == turn:
                game_board[move] = player_symbol
                current_name = player_names[player]
                broadcast(f"#JUGADA#OK#{move}#{player_symbol}#")  # Envía el movimiento a todos los clientes

                # Comprobar si hay un ganador y manejarlo de manera segura con el Lock
                with winner_lock:
                    if not winner and check_winner(game_board):
                        winner = current_name
                        player_scores[player] += 1
                        if player_scores[player] == MAX_SCORE:
                            broadcast(f"#OK#{current_name} es el campeón de la partida#")

                turn = 1 - turn
                broadcast(f"#TURNO#{turn}#")
            else:
                current_player.send("#JUGADA#NOK#Movimiento no válido. Inténtalo de nuevo.#".encode('utf-8'))

#Se define una función check_winner para verificar si hay un ganador basándose en el estado actual del tablero.
def check_winner(board):
    for i in range(0, 3):
        if board[i] == board[i + 3] == board[i + 6] != ' ':
            return True
        if board[i * 3] == board[i * 3 + 1] == board[i * 3 + 2] != ' ':
            return True
    if board[0] == board[4] == board[8] != ' ' or board[2] == board[4] == board[6] != ' ':
        return True
    return False

#Se espera a que se conecten suficientes jugadores y se inicia un hilo para cada cliente.
# Espera a que los jugadores se conecten
while len(clients) < MAX_PLAYERS:
    client, address = server.accept()
    clients.append(client)
    thread = threading.Thread(target=handle_client, args=(client, len(clients)))
    thread.start()

#Se ejecuta el bucle principal del juego, donde se manejan los turnos y las 
# jugadas hasta que haya un ganador o se alcance la puntuación máxima.
while winner is None and player_scores[0] < MAX_SCORE and player_scores[1] < MAX_SCORE:
    current_player = clients[turn]
    other_player = clients[1 - turn]

    #La logica para menejar los turnos y las jugadas
    if turn in player_names:
        current_name = player_names[turn]
    else:
        current_name = "Jugador 1"

    if 1 - turn in player_names:
        other_name = player_names[1 - turn]
    else:
        other_name = "Jugador 2"

    broadcast(f"#TURNO#{turn}#")  # Indicar el turno antes de cada jugada

    broadcast(f"#JUGADA#{current_name}#")
    move = current_player.recv(1024).decode('utf-8')
    move = int(move)

    if 0 <= move < 9 and game_board[move] == ' ':
        game_board[move] = 'X' if turn == 0 else 'O'
        current_player.send(f"#OK#Has hecho una jugada en la casilla {move}#".encode('utf-8'))
        other_player.send(f"#JUGADA#{current_name}#{move}#".encode('utf-8'))

        # Comprobar si hay un ganador y manejarlo de manera segura con el Lock
        with winner_lock:
            if not winner and check_winner(game_board):
                winner = current_name
                player_scores[turn] += 1
                if player_scores[turn] == MAX_SCORE:
                    broadcast(f"#OK#{current_name} es el campeón de la partida#")

        turn = 1 - turn
        broadcast(f"#TURNO#{turn}#")  # Indicar el turno después de cada jugada
    else:
        current_player.send("#NOK#Movimiento no válido. Inténtalo de nuevo.#".encode('utf-8'))
