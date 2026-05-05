/**
 * 单人积分赛游戏逻辑
 * 使用 TETRIS_CONFIG 配置中心和 KeyConfigManager 按键管理器
 */

class SoloGame {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.nextCanvas = document.getElementById('next-canvas');
        this.nextCtx = this.nextCanvas.getContext('2d');
        
        this.board = [];
        this.currentPiece = null;
        this.nextPiece = null;
        this.score = 0;
        this.level = 1;
        this.lines = 0;
        this.gameRunning = false;
        this.gamePaused = false;
        this.gameOver = false;
        this.tickRate = TETRIS_CONFIG.TIMING.TICK_RATE;
        this.lastTick = 0;
        this.animationId = null;
        
        this.scoreSubmitted = false;
        this.highScore = localStorage.getItem(TETRIS_CONFIG.STORAGE.HIGH_SCORE) || 0;
        
        // 初始化按键配置管理器
        this.keyConfigManager = new KeyConfigManager(
            TETRIS_CONFIG.STORAGE.SOLO_KEY_CONFIG,
            TETRIS_CONFIG.KEYS.BASE
        );
        
        this.init();
    }
    
    init() {
        this.resetBoard();
        this.bindEvents();
        this.draw();
        this.drawNext();
        this.keyConfigManager.createModal();
        this.updateInstructions();
    }
    
    resetBoard() {
        this.board = Array(TETRIS_CONFIG.BOARD.HEIGHT).fill(null)
            .map(() => Array(TETRIS_CONFIG.BOARD.WIDTH).fill(0));
    }
    
    bindEvents() {
        document.getElementById('btn-start').addEventListener('click', () => this.startGame());
        document.getElementById('btn-restart').addEventListener('click', () => this.startGame());
        document.getElementById('btn-submit-score').addEventListener('click', () => this.submitScore());
        
        // 按键设置按钮
        const keySettingsBtn = document.getElementById('btn-key-settings');
        if (keySettingsBtn) {
            keySettingsBtn.addEventListener('click', () => this.keyConfigManager.showModal());
        }
        
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }
    
    startGame() {
        this.resetBoard();
        this.currentPiece = null;
        this.nextPiece = this.createPiece();
        this.score = 0;
        this.level = 1;
        this.lines = 0;
        this.tickRate = TETRIS_CONFIG.TIMING.TICK_RATE;
        this.gameRunning = true;
        this.gamePaused = false;
        this.gameOver = false;
        this.scoreSubmitted = false;
        
        this.updateUI();
        this.hideGameOver();
        this.spawnPiece();
        
        document.getElementById('btn-start').disabled = true;
        document.getElementById('btn-start').textContent = '游戏进行中...';
        
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.lastTick = performance.now();
        this.gameLoop();
    }
    
    createPiece() {
        const shapeIndex = Math.floor(Math.random() * TETRIS_CONFIG.SHAPES.length);
        return {
            shape: TETRIS_CONFIG.SHAPES[shapeIndex],
            color: TETRIS_CONFIG.COLORS[shapeIndex],
            x: Math.floor(TETRIS_CONFIG.BOARD.WIDTH / 2) - Math.floor(TETRIS_CONFIG.SHAPES[shapeIndex][0].length / 2),
            y: 0,
            shapeIndex: shapeIndex
        };
    }
    
    spawnPiece() {
        this.currentPiece = this.nextPiece;
        this.nextPiece = this.createPiece();
        this.drawNext();
        
        if (this.checkCollision(this.currentPiece, 0, 0)) {
            this.endGame();
            return;
        }
    }
    
    checkCollision(piece, dx, dy, newShape = null) {
        const shape = newShape || piece.shape;
        for (let y = 0; y < shape.length; y++) {
            for (let x = 0; x < shape[y].length; x++) {
                if (shape[y][x]) {
                    const newX = piece.x + x + dx;
                    const newY = piece.y + y + dy;
                    
                    if (newX < 0 || newX >= TETRIS_CONFIG.BOARD.WIDTH || 
                        newY >= TETRIS_CONFIG.BOARD.HEIGHT) {
                        return true;
                    }
                    
                    if (newY >= 0 && this.board[newY][newX]) {
                        return true;
                    }
                }
            }
        }
        return false;
    }
    
    lockPiece() {
        for (let y = 0; y < this.currentPiece.shape.length; y++) {
            for (let x = 0; x < this.currentPiece.shape[y].length; x++) {
                if (this.currentPiece.shape[y][x]) {
                    const boardY = this.currentPiece.y + y;
                    const boardX = this.currentPiece.x + x;
                    if (boardY >= 0) {
                        this.board[boardY][boardX] = this.currentPiece.shapeIndex + 1;
                    }
                }
            }
        }
        this.clearLines();
        this.spawnPiece();
    }
    
    clearLines() {
        let linesCleared = 0;
        
        for (let y = TETRIS_CONFIG.BOARD.HEIGHT - 1; y >= 0; y--) {
            if (this.board[y].every(cell => cell !== 0)) {
                this.board.splice(y, 1);
                this.board.unshift(Array(TETRIS_CONFIG.BOARD.WIDTH).fill(0));
                linesCleared++;
                y++;
            }
        }
        
        if (linesCleared > 0) {
            this.lines += linesCleared;
            const points = [0, 100, 300, 600, 1000];
            this.score += points[linesCleared] * this.level;
            
            const newLevel = Math.floor(this.lines / 10) + 1;
            if (newLevel > this.level) {
                this.level = newLevel;
                this.tickRate = Math.max(
                    TETRIS_CONFIG.TIMING.MIN_TICK_RATE,
                    TETRIS_CONFIG.TIMING.TICK_RATE - (this.level - 1) * TETRIS_CONFIG.TIMING.LEVEL_SPEEDUP
                );
            }
            
            this.updateUI();
        }
    }
    
    movePiece(dx, dy) {
        if (!this.gameRunning || this.gamePaused || this.gameOver) return false;
        
        if (!this.checkCollision(this.currentPiece, dx, dy)) {
            this.currentPiece.x += dx;
            this.currentPiece.y += dy;
            this.draw();
            return true;
        }
        
        if (dy > 0) {
            this.lockPiece();
        }
        return false;
    }
    
    rotatePiece() {
        if (!this.gameRunning || this.gamePaused || this.gameOver) return;
        
        let rotated = this.currentPiece.shape[0].map((_, i) =>
            this.currentPiece.shape.map(row => row[i]).reverse()
        );
        
        // I方块特殊处理：使用标准SRS旋转
        if (this.currentPiece.shapeIndex === 0) {
            const rows = this.currentPiece.shape.length;
            const cols = this.currentPiece.shape[0].length;
            
            if (rows === 4 && cols === 4) {
                // 检测当前是水平还是垂直状态
                const isHorizontal = this.currentPiece.shape[1].reduce((a, b) => a + b, 0) === 4;
                
                if (isHorizontal) {
                    // 水平 -> 垂直：向左偏移1格
                    const adjusted = Array(4).fill(null).map(() => Array(4).fill(0));
                    for (let y = 0; y < 4; y++) {
                        for (let x = 0; x < 4; x++) {
                            if (rotated[y] && rotated[y][x]) {
                                const newX = x - 1;
                                const newY = y;
                                if (newX >= 0 && newX < 4 && newY >= 0 && newY < 4) {
                                    adjusted[newY][newX] = 1;
                                }
                            }
                        }
                    }
                    rotated = adjusted;
                } else {
                    // 垂直 -> 水平：向上偏移1格
                    const adjusted = Array(4).fill(null).map(() => Array(4).fill(0));
                    for (let y = 0; y < 4; y++) {
                        for (let x = 0; x < 4; x++) {
                            if (rotated[y] && rotated[y][x]) {
                                const newX = x;
                                const newY = y - 1;
                                if (newX >= 0 && newX < 4 && newY >= 0 && newY < 4) {
                                    adjusted[newY][newX] = 1;
                                }
                            }
                        }
                    }
                    rotated = adjusted;
                }
            }
        }
        
        // 尝试旋转，如果碰撞则尝试 wall kick
        const kicks = [0, -1, 1, -2, 2];
        for (const kick of kicks) {
            if (!this.checkCollision(this.currentPiece, kick, 0, rotated)) {
                this.currentPiece.x += kick;
                this.currentPiece.shape = rotated;
                this.draw();
                return;
            }
        }
    }
    
    hardDrop() {
        if (!this.gameRunning || this.gamePaused || this.gameOver) return;
        
        let dropDistance = 0;
        while (!this.checkCollision(this.currentPiece, 0, dropDistance + 1)) {
            dropDistance++;
        }
        
        this.score += dropDistance * 2;
        this.currentPiece.y += dropDistance;
        this.lockPiece();
        this.updateUI();
    }
    
    togglePause() {
        if (!this.gameRunning || this.gameOver) return;
        this.gamePaused = !this.gamePaused;
    }
    
    endGame() {
        this.gameRunning = false;
        this.gameOver = true;
        
        if (this.score > this.highScore) {
            this.highScore = this.score;
            localStorage.setItem(TETRIS_CONFIG.STORAGE.HIGH_SCORE, this.highScore);
        }
        
        this.showGameOver();
        document.getElementById('btn-start').disabled = false;
        document.getElementById('btn-start').textContent = '开始游戏';
    }
    
    showGameOver() {
        const overlay = document.getElementById('game-over-overlay');
        overlay.classList.remove('hidden');
        document.getElementById('final-score').textContent = this.score;
        
        const highScoreText = this.score >= this.highScore 
            ? '🏆 新纪录！' 
            : `历史最高分: ${this.highScore}`;
        document.getElementById('high-score').textContent = highScoreText;
        
        document.getElementById('btn-submit-score').disabled = false;
        document.getElementById('submitted-message').classList.add('hidden');
    }
    
    hideGameOver() {
        document.getElementById('game-over-overlay').classList.add('hidden');
    }
    
    async submitScore() {
        if (this.scoreSubmitted) return;
        
        const nickname = document.getElementById('nickname-input').value.trim() || '匿名玩家';
        const btn = document.getElementById('btn-submit-score');
        btn.disabled = true;
        btn.textContent = '提交中...';
        
        try {
            const response = await fetch(TETRIS_CONFIG.API.SUBMIT_SCORE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    player_name: nickname,
                    score: this.score,
                    lines_cleared: this.lines,
                    level: this.level,
                    game_mode: 'single',
                    difficulty: 'normal',
                    play_time: 0
                })
            });
            
            if (response.ok) {
                this.scoreSubmitted = true;
                document.getElementById('btn-submit-score').disabled = true;
                document.getElementById('submitted-message').classList.remove('hidden');
            } else {
                alert('提交失败，请重试');
                btn.disabled = false;
                btn.textContent = '提交到排行榜';
            }
        } catch (error) {
            console.error('提交分数失败:', error);
            alert('提交失败，请检查网络连接');
            btn.disabled = false;
            btn.textContent = '提交到排行榜';
        }
    }
    
    handleKeyDown(e) {
        // 如果正在绑定按键，处理绑定逻辑
        if (this.keyConfigManager.isBinding()) {
            e.preventDefault();
            this.keyConfigManager.handleBinding(e.key);
            this.updateInstructions();
            return;
        }
        
        if (!this.gameRunning) return;
        
        const keyConfig = this.keyConfigManager.getConfig();
        const key = e.key;
        
        if (key === keyConfig.moveLeft) {
            e.preventDefault();
            this.movePiece(-1, 0);
        } else if (key === keyConfig.moveRight) {
            e.preventDefault();
            this.movePiece(1, 0);
        } else if (key === keyConfig.moveDown) {
            e.preventDefault();
            if (this.movePiece(0, 1)) {
                this.score += 1;
                this.updateUI();
            }
        } else if (key === keyConfig.rotate) {
            e.preventDefault();
            this.rotatePiece();
        } else if (key === keyConfig.hardDrop) {
            e.preventDefault();
            this.hardDrop();
        } else if (key.toLowerCase() === keyConfig.pause.toLowerCase()) {
            e.preventDefault();
            this.togglePause();
        }
    }
    
    gameLoop() {
        if (!this.gameRunning) return;
        
        const now = performance.now();
        
        if (!this.gamePaused && now - this.lastTick >= this.tickRate) {
            this.movePiece(0, 1);
            this.lastTick = now;
        }
        
        this.draw();
        this.animationId = requestAnimationFrame(() => this.gameLoop());
    }
    
    draw() {
        // 清空画布 - 使用更深的背景色
        this.ctx.fillStyle = '#0a0a0a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制网格线
        this.ctx.strokeStyle = '#1a1a1a';
        this.ctx.lineWidth = 1;
        for (let x = 0; x <= TETRIS_CONFIG.BOARD.WIDTH; x++) {
            this.ctx.beginPath();
            this.ctx.moveTo(x * TETRIS_CONFIG.BOARD.BLOCK_SIZE, 0);
            this.ctx.lineTo(x * TETRIS_CONFIG.BOARD.BLOCK_SIZE, this.canvas.height);
            this.ctx.stroke();
        }
        for (let y = 0; y <= TETRIS_CONFIG.BOARD.HEIGHT; y++) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y * TETRIS_CONFIG.BOARD.BLOCK_SIZE);
            this.ctx.lineTo(this.canvas.width, y * TETRIS_CONFIG.BOARD.BLOCK_SIZE);
            this.ctx.stroke();
        }
        
        // 绘制已固定的方块
        for (let y = 0; y < TETRIS_CONFIG.BOARD.HEIGHT; y++) {
            for (let x = 0; x < TETRIS_CONFIG.BOARD.WIDTH; x++) {
                if (this.board[y][x]) {
                    this.drawBlock(this.ctx, x, y, TETRIS_CONFIG.COLORS[this.board[y][x] - 1]);
                }
            }
        }
        
        // 绘制当前方块
        if (this.currentPiece) {
            for (let y = 0; y < this.currentPiece.shape.length; y++) {
                for (let x = 0; x < this.currentPiece.shape[y].length; x++) {
                    if (this.currentPiece.shape[y][x]) {
                        this.drawBlock(
                            this.ctx,
                            this.currentPiece.x + x,
                            this.currentPiece.y + y,
                            this.currentPiece.color
                        );
                    }
                }
            }
        }
        
        // 绘制暂停提示
        if (this.gamePaused) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.fillStyle = '#00d4ff';
            this.ctx.font = 'bold 36px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('PAUSED', this.canvas.width / 2, this.canvas.height / 2);
        }
    }
    
    drawNext() {
        this.nextCtx.fillStyle = '#0a0a0a';
        this.nextCtx.fillRect(0, 0, this.nextCanvas.width, this.nextCanvas.height);
        
        // 绘制网格背景
        this.nextCtx.strokeStyle = '#1a1a1a';
        this.nextCtx.lineWidth = 1;
        
        if (!this.nextPiece) return;
        
        const blockSize = 25;
        
        for (let x = 0; x <= 4; x++) {
            this.nextCtx.beginPath();
            this.nextCtx.moveTo(x * blockSize, 0);
            this.nextCtx.lineTo(x * blockSize, this.nextCanvas.height);
            this.nextCtx.stroke();
        }
        for (let y = 0; y <= 4; y++) {
            this.nextCtx.beginPath();
            this.nextCtx.moveTo(0, y * blockSize);
            this.nextCtx.lineTo(this.nextCanvas.width, y * blockSize);
            this.nextCtx.stroke();
        }
        
        const offsetX = (this.nextCanvas.width - this.nextPiece.shape[0].length * blockSize) / 2;
        const offsetY = (this.nextCanvas.height - this.nextPiece.shape.length * blockSize) / 2;
        
        for (let y = 0; y < this.nextPiece.shape.length; y++) {
            for (let x = 0; x < this.nextPiece.shape[y].length; x++) {
                if (this.nextPiece.shape[y][x]) {
                    const px = offsetX + x * blockSize;
                    const py = offsetY + y * blockSize;
                    
                    // 主体
                    this.nextCtx.fillStyle = this.nextPiece.color;
                    this.nextCtx.fillRect(px + 1, py + 1, blockSize - 2, blockSize - 2);
                    
                    // 高光
                    this.nextCtx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                    this.nextCtx.fillRect(px + 1, py + 1, blockSize - 2, 4);
                    this.nextCtx.fillRect(px + 1, py + 1, 4, blockSize - 2);
                    
                    // 阴影
                    this.nextCtx.fillStyle = 'rgba(0, 0, 0, 0.3)';
                    this.nextCtx.fillRect(px + 1, py + blockSize - 5, blockSize - 2, 4);
                    this.nextCtx.fillRect(px + blockSize - 5, py + 1, 4, blockSize - 2);
                }
            }
        }
    }
    
    drawBlock(ctx, x, y, color) {
        const px = x * TETRIS_CONFIG.BOARD.BLOCK_SIZE;
        const py = y * TETRIS_CONFIG.BOARD.BLOCK_SIZE;
        const blockSize = TETRIS_CONFIG.BOARD.BLOCK_SIZE;
        
        // 主体
        ctx.fillStyle = color;
        ctx.fillRect(px + 1, py + 1, blockSize - 2, blockSize - 2);
        
        // 高光
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.fillRect(px + 1, py + 1, blockSize - 2, 4);
        ctx.fillRect(px + 1, py + 1, 4, blockSize - 2);
        
        // 阴影
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(px + 1, py + blockSize - 5, blockSize - 2, 4);
        ctx.fillRect(px + blockSize - 5, py + 1, 4, blockSize - 2);
    }
    
    updateUI() {
        document.getElementById('score').textContent = this.score;
        document.getElementById('level').textContent = this.level;
        document.getElementById('lines').textContent = this.lines;
    }
    
    updateInstructions() {
        const instructions = document.querySelector('.instructions ul');
        if (instructions) {
            const keyConfig = this.keyConfigManager.getConfig();
            instructions.innerHTML = `
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.moveLeft)}</span> <span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.moveRight)}</span> 左右移动</li>
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.rotate)}</span> 旋转方块</li>
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.moveDown)}</span> 加速下降</li>
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.hardDrop)}</span> 直接落地</li>
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.pause)}</span> 暂停/继续</li>
            `;
        }
    }
}

// 启动游戏
const game = new SoloGame();
