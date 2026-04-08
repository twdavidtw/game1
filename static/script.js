const socket = io();
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const GRID_SIZE = 20;
const COLS = canvas.width / GRID_SIZE;
const ROWS = canvas.height / GRID_SIZE;

let myId = null;
let gameState = null;

// UI Elements
const setup = document.getElementById('setup');
const gameContainer = document.getElementById('game-container');
const joinBtn = document.getElementById('join-btn');
const usernameInput = document.getElementById('username');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const messagesArea = document.getElementById('messages');
const statsArea = document.getElementById('player-info');

// Audio setup
const bgMusic = new Audio('/static/background.wav');
bgMusic.loop = true;
const scoreSound = new Audio('/static/score.wav');

// Join Game
joinBtn.onclick = () => {
    const name = usernameInput.value.trim() || '匿名的蛇';
    socket.emit('join', { name });
    setup.style.display = 'none';
    gameContainer.style.display = 'flex';
    
    // Start background music
    bgMusic.play().catch(e => console.log("Audio play failed:", e));
};

// Controls
// Controls (Keyboard)
document.addEventListener('keydown', (e) => {
    let dir = null;
    if (e.key === 'ArrowUp' || e.key === 'w') dir = { x: 0, y: -1 };
    if (e.key === 'ArrowDown' || e.key === 's') dir = { x: 0, y: 1 };
    if (e.key === 'ArrowLeft' || e.key === 'a') dir = { x: -1, y: 0 };
    if (e.key === 'ArrowRight' || e.key === 'd') dir = { x: 1, y: 0 };

    if (dir) {
        socket.emit('move', { dir });
    }
});

// Controls (Mobile D-Pad)
const setupDPad = () => {
    const emitMove = (dir) => socket.emit('move', { dir });
    
    document.getElementById('up-btn')?.addEventListener('pointerdown', (e) => { e.preventDefault(); emitMove({ x: 0, y: -1 }); });
    document.getElementById('down-btn')?.addEventListener('pointerdown', (e) => { e.preventDefault(); emitMove({ x: 0, y: 1 }); });
    document.getElementById('left-btn')?.addEventListener('pointerdown', (e) => { e.preventDefault(); emitMove({ x: -1, y: 0 }); });
    document.getElementById('right-btn')?.addEventListener('pointerdown', (e) => { e.preventDefault(); emitMove({ x: 1, y: 0 }); });
};
setupDPad();

// Chat
const sendMessage = () => {
    const msg = chatInput.value.trim();
    if (msg) {
        socket.emit('chat', { msg });
        chatInput.value = '';
    }
};

sendBtn.onclick = sendMessage;
chatInput.onkeydown = (e) => { if (e.key === 'Enter') sendMessage(); };

// Socket Events
socket.on('init', (data) => {
    myId = data.id;
});

socket.on('chat', (data) => {
    const msgEl = document.createElement('div');
    msgEl.className = 'message';
    msgEl.innerHTML = `<span class="name">${data.name}:</span><span>${data.msg}</span>`;
    messagesArea.appendChild(msgEl);
    messagesArea.scrollTop = messagesArea.scrollHeight;
});

socket.on('game_update', (state) => {
    gameState = state;
    render();
    updateStats();
});

socket.on('score_sound', () => {
    scoreSound.currentTime = 0;
    scoreSound.play().catch(e => console.log("Sound play failed:", e));
});

// Rendering
function render() {
    if (!gameState) return;

    // Clear board
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw Grid (Subtle)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    for(let i=0; i<=COLS; i++) {
        ctx.beginPath(); ctx.moveTo(i*GRID_SIZE, 0); ctx.lineTo(i*GRID_SIZE, canvas.height); ctx.stroke();
    }
    for(let i=0; i<=ROWS; i++) {
        ctx.beginPath(); ctx.moveTo(0, i*GRID_SIZE); ctx.lineTo(canvas.width, i*GRID_SIZE); ctx.stroke();
    }

    // Draw Background Text
    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.font = 'bold 80px Outfit';
    ctx.textAlign = 'center';
    ctx.fillText('VICTOR GAME', canvas.width / 2, canvas.height / 2 + 30);

    // Draw Food
    ctx.fillStyle = '#ef4444';
    ctx.shadowBlur = 15;
    ctx.shadowColor = '#ef4444';
    ctx.fillRect(gameState.food.x * GRID_SIZE, gameState.food.y * GRID_SIZE, GRID_SIZE, GRID_SIZE);
    ctx.shadowBlur = 0;

    // Draw Players
    Object.values(gameState.players).forEach(player => {
        ctx.fillStyle = player.color;
        // Draw head
        ctx.fillRect(player.pos.x * GRID_SIZE, player.pos.y * GRID_SIZE, GRID_SIZE, GRID_SIZE);
        
        // Draw body
        ctx.globalAlpha = 0.6;
        player.body.forEach(seg => {
            ctx.fillRect(seg.x * GRID_SIZE, seg.y * GRID_SIZE, GRID_SIZE, GRID_SIZE);
        });
        ctx.globalAlpha = 1.0;

        // Label player name
        ctx.fillStyle = 'white';
        ctx.font = 'bold 12px Outfit';
        ctx.textAlign = 'center';
        ctx.fillText(player.name, player.pos.x * GRID_SIZE + 10, player.pos.y * GRID_SIZE - 5);
    });
}

function updateStats() {
    if (!gameState) return;
    let html = '';
    Object.values(gameState.players).forEach(player => {
        html += `<div class="player-score" style="border-left-color: ${player.color}">
            ${player.name}: ${player.score}
        </div>`;
    });
    statsArea.innerHTML = html || '<div class="player-score">觀看模式</div>';
}
