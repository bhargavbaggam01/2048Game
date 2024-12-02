from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

# Initialize game board
def init_board():
    board = [[0] * 4 for _ in range(4)]
    # Place 2 initial tiles
    add_new_tile(board)
    add_new_tile(board)
    return board

def add_new_tile(board):
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    if empty_cells:
        i, j = random.choice(empty_cells)
        board[i][j] = 2 if random.random() < 0.9 else 4

def move(board, direction):
    # Make a copy of the board
    board_copy = [row[:] for row in board]
    merged = [[False] * 4 for _ in range(4)]
    
    if direction in ['left', 'right']:
        for i in range(4):
            row = board[i]
            if direction == 'right':
                row = row[::-1]
            # Move and merge
            new_row = [0] * 4
            pos = 0
            for j in range(4):
                if row[j] != 0:
                    if pos > 0 and new_row[pos-1] == row[j] and not merged[i][pos-1]:
                        new_row[pos-1] *= 2
                        merged[i][pos-1] = True
                    else:
                        new_row[pos] = row[j]
                        pos += 1
            if direction == 'right':
                new_row = new_row[::-1]
            board[i] = new_row
            
    else:  # up or down
        for j in range(4):
            col = [board[i][j] for i in range(4)]
            if direction == 'down':
                col = col[::-1]
            # Move and merge
            new_col = [0] * 4
            pos = 0
            for i in range(4):
                if col[i] != 0:
                    if pos > 0 and new_col[pos-1] == col[i] and not merged[pos-1][j]:
                        new_col[pos-1] *= 2
                        merged[pos-1][j] = True
                    else:
                        new_col[pos] = col[i]
                        pos += 1
            if direction == 'down':
                new_col = new_col[::-1]
            for i in range(4):
                board[i][j] = new_col[i]
                
    # Check if board changed
    if board != board_copy:
        add_new_tile(board)
    return board

def game_over(board):
    # Check for any empty cells
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return False
                
    # Check for possible merges
    for i in range(4):
        for j in range(4):
            val = board[i][j]
            # Check right and down neighbors
            if (j < 3 and board[i][j+1] == val) or (i < 3 and board[i+1][j] == val):
                return False
    return True

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>2048 Game</title>
            <style>
                body {
                    background: #000;
                    color: #fff;
                    font-family: Arial, sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                }
                .board { 
                    display: grid; 
                    grid-template-columns: repeat(4, 80px); 
                    gap: 8px;
                    padding: 10px;
                    background: #1a1a1a;
                    border-radius: 10px;
                    box-shadow: 0 0 20px #0ff;
                }
                .cell { 
                    width: 80px; 
                    height: 80px; 
                    background: #333;
                    border: 2px solid #0ff;
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                    font-size: 24px;
                    font-weight: bold;
                    color: #0ff;
                    text-shadow: 0 0 10px #0ff;
                    border-radius: 5px;
                }
                button {
                    background: #000;
                    color: #0ff;
                    border: 2px solid #0ff;
                    padding: 10px 20px;
                    margin: 10px;
                    font-size: 18px;
                    border-radius: 5px;
                    cursor: pointer;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    box-shadow: 0 0 10px #0ff;
                    transition: all 0.3s ease;
                }
                button:hover {
                    background: #0ff;
                    color: #000;
                    box-shadow: 0 0 20px #0ff;
                }
                .instructions {
                    color: #0ff;
                    margin: 20px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <h1 style="color: #0ff; text-shadow: 0 0 20px #0ff;">2048 Game</h1>
            <div class="board" id="board"></div>
            <button onclick="newGame()">New Game</button>
            <div class="instructions">Use arrow keys to move tiles</div>
            <script>
                let board = [];
                
                function updateBoard() {
                    fetch('/get_board')
                        .then(response => response.json())
                        .then(data => {
                            board = data.board;
                            displayBoard();
                            if (data.game_over) {
                                alert('Game Over!');
                            }
                        });
                }
                
                function displayBoard() {
                    const boardDiv = document.getElementById('board');
                    boardDiv.innerHTML = '';
                    for (let i = 0; i < 4; i++) {
                        for (let j = 0; j < 4; j++) {
                            const cell = document.createElement('div');
                            cell.className = 'cell';
                            cell.textContent = board[i][j] || '';
                            boardDiv.appendChild(cell);
                        }
                    }
                }
                
                function handleKeyPress(event) {
                    const keyToDirection = {
                        'ArrowUp': 'up',
                        'ArrowDown': 'down',
                        'ArrowLeft': 'left',
                        'ArrowRight': 'right'
                    };
                    
                    const direction = keyToDirection[event.key];
                    if (direction) {
                        event.preventDefault();
                        fetch('/move/' + direction, {method: 'POST'})
                            .then(() => updateBoard());
                    }
                }
                
                function newGame() {
                    fetch('/new_game', {method: 'POST'})
                        .then(() => updateBoard());
                }
                
                document.addEventListener('keydown', handleKeyPress);
                updateBoard();
            </script>
        </body>
    </html>
    '''

# Game state
BOARD = init_board()

@app.route('/get_board')
def get_board():
    return jsonify({
        'board': BOARD,
        'game_over': game_over(BOARD)
    })

@app.route('/move/<direction>', methods=['POST'])
def make_move(direction):
    if direction in ['up', 'down', 'left', 'right']:
        move(BOARD, direction)
    return '', 204

@app.route('/new_game', methods=['POST'])
def new_game():
    global BOARD
    BOARD = init_board()
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
