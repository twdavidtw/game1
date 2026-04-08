import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
COLS = WIDTH // GRID_SIZE
ROWS = HEIGHT // GRID_SIZE

# Game State
game_state = {
    'players': {}, # id -> {pos, dir, body, score, color, name}
    'food': {'x': random.randint(0, COLS-1), 'y': random.randint(0, ROWS-1)},
    'is_running': False
}

colors = ['green', 'blue', 'yellow', 'purple', 'orange']

def reset_player(sid, name):
    game_state['players'][sid] = {
        'id': sid,
        'name': name,
        'pos': {'x': random.randint(5, COLS-10), 'y': random.randint(5, ROWS-10)},
        'dir': {'x': 1, 'y': 0},
        'body': [],
        'score': 0,
        'color': random.choice(colors)
    }

def game_loop():
    while True:
        try:
            socketio.sleep(0.2) # 5 FPS
            if not game_state['players']:
                continue
            
            # Update each player
            for sid, player in list(game_state['players'].items()):
                # Update body (add current head to body)
                player['body'].insert(0, {'x': player['pos']['x'], 'y': player['pos']['y']})
                
                # Move head
                player['pos']['x'] = (player['pos']['x'] + player['dir']['x']) % COLS
                player['pos']['y'] = (player['pos']['y'] + player['dir']['y']) % ROWS
                
                # Check food
                if player['pos']['x'] == game_state['food']['x'] and player['pos']['y'] == game_state['food']['y']:
                    player['score'] += 1
                    game_state['food'] = {'x': random.randint(0, COLS-1), 'y': random.randint(0, ROWS-1)}
                    socketio.emit('score_sound', broadcast=True)
                else:
                    if len(player['body']) > player['score']:
                        player['body'].pop()
                        
                # Check collision with self
                for segment in player['body']:
                    if player['pos']['x'] == segment['x'] and player['pos']['y'] == segment['y']:
                        # Reset player on collision
                        reset_player(sid, player['name'])
                        socketio.emit('chat', {'name': '系統', 'msg': f"{player['name']} 撞到自己了！"}, broadcast=True)
                        break
            
            # Broadcast state
            socketio.emit('game_update', game_state)
        except Exception as e:
            print(f"Error in game_loop loop iteration: {e}")

@app.route('/')
def index():
    return render_template('index.html')

# Background thread for game loop
thread = None
thread_lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(game_loop)
    print(f"Client connected: {threading.get_ident()}")

@socketio.on('join')
def handle_join(data):
    from flask import request
    sid = request.sid
    name = data.get('name', f"玩家_{random.randint(100, 999)}")
    
    if len(game_state['players']) >= 2:
        emit('chat', {'name': '系統', 'msg': "遊戲已滿，您將進入觀戰模式。"})
    else:
        reset_player(sid, name)
        emit('chat', {'name': '系統', 'msg': f"歡迎 {name} 加入遊戲！"})
        emit('init', {'id': sid})
    
    emit('chat', {'name': '系統', 'msg': f"{name} 進入了聊天室。"}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    from flask import request
    sid = request.sid
    if sid in game_state['players']:
        name = game_state['players'][sid]['name']
        del game_state['players'][sid]
        emit('chat', {'name': '系統', 'msg': f"{name} 離開了實體。"}, broadcast=True)

@socketio.on('move')
def handle_move(data):
    from flask import request
    sid = request.sid
    if sid in game_state['players']:
        new_dir = data.get('dir') # {x, y}
        player = game_state['players'][sid]
        # Prevent 180 degree turns
        if (new_dir['x'] * -1 != player['dir']['x']) or (new_dir['y'] * -1 != player['dir']['y']):
            player['dir'] = new_dir

@socketio.on('chat')
def handle_chat(data):
    from flask import request
    sid = request.sid
    name = "觀眾"
    if sid in game_state['players']:
        name = game_state['players'][sid]['name']
    
    msg = data.get('msg', '')
    if msg:
        emit('chat', {'name': name, 'msg': msg}, broadcast=True)

if __name__ == '__main__':
    import os
    # Start game loop in background
    socketio.start_background_task(game_loop)
    # Use PORT or SERVER_PORT from environment variables (assigned by Render/Heroku/FalixNodes)
    port = int(os.environ.get('PORT', os.environ.get('SERVER_PORT', 5000)))
    print(f"Starting server on port {port}...")
    socketio.run(app, debug=True, host='0.0.0.0', port=port)
