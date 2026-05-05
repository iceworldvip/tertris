/**
 * 俄罗斯方块 AI对战版
 * 支持玩家与AI对战
 * 使用 TETRIS_CONFIG 配置中心和 KeyConfigManager 按键管理器
 */

class AIGame {
  constructor() {
    this.nickname = "";
    this.roomId = null;
    this.difficulty = "normal";
    this.ws = null;
    this.isConnected = false;

    // 游戏状态
    this.roomState = null;
    this.playerGame = null;
    this.aiGame = null;

    // 游戏时间追踪
    this.gameStartTime = null;
    this.scoreSubmitted = false;

    // Canvas
    this.playerCanvas = document.getElementById("player-board");
    this.playerCtx = this.playerCanvas.getContext("2d");
    this.aiCanvas = document.getElementById("ai-board");
    this.aiCtx = this.aiCanvas.getContext("2d");
    this.nextCanvas = document.getElementById("next-piece");
    this.nextCtx = this.nextCanvas.getContext("2d");

    // 方块颜色 - 使用配置中心的颜色
    this.colors = TETRIS_CONFIG.COLORS;

    // 按键状态
    this.keysPressed = new Set();
    this.lastMoveTime = 0;
    this.moveDelay = TETRIS_CONFIG.TIMING.MOVE_DELAY;
    this.lastHardDropTime = 0;
    this.hardDropDelay = TETRIS_CONFIG.TIMING.HARD_DROP_DELAY;
    this.lastPauseTime = 0;
    this.pauseDelay = TETRIS_CONFIG.TIMING.PAUSE_DELAY;

    // 道具系统
    this.selectedItemIndex = -1;

    // 初始化按键配置管理器
    this.keyConfigManager = new KeyConfigManager(
      TETRIS_CONFIG.STORAGE.AI_KEY_CONFIG,
      TETRIS_CONFIG.KEYS.AI_MODE,
    );

    this.init();
  }

  init() {
    this.bindLobbyEvents();
    this.bindGameEvents();
    this.generateNickname();
    this.updateInstructions();
    this.updateInitialItemText();
  }

  generateNickname() {
    const adj =
      TETRIS_CONFIG.NICKNAME.ADJECTIVES[
        Math.floor(Math.random() * TETRIS_CONFIG.NICKNAME.ADJECTIVES.length)
      ];
    const noun =
      TETRIS_CONFIG.NICKNAME.NOUNS[
        Math.floor(Math.random() * TETRIS_CONFIG.NICKNAME.NOUNS.length)
      ];
    const num = Math.floor(Math.random() * 100);
    const nickname = `${adj}${noun}${num}`;
    document.getElementById("nickname").value = nickname;
    this.nickname = nickname;
  }

  updateInstructions() {
    const instructions = document.querySelector(".instructions ul");
    const keyConfig = this.keyConfigManager.getConfig();
    if (instructions) {
      instructions.innerHTML = `
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.moveLeft)}</span> <span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.moveRight)}</span> 左右移动</li>
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.rotate)}</span> 旋转</li>
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.moveDown)}</span> 加速下落</li>
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.hardDrop)}</span> 直接落下</li>
                <li><span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.pause)}</span> 暂停</li>
            `;
    }
  }

  // ========== 大厅界面事件 ==========
  bindLobbyEvents() {
    // 难度选择
    document.querySelectorAll(".difficulty-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document
          .querySelectorAll(".difficulty-btn")
          .forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this.difficulty = btn.dataset.diff;
        this.updateDifficultyDesc();
      });
    });

    // 创建AI房间
    document
      .getElementById("btn-create-ai-room")
      .addEventListener("click", () => {
        this.nickname =
          document.getElementById("nickname").value.trim() || "玩家";
        this.createAIRoom();
      });

    // 按键设置按钮
    const keySettingsBtn = document.getElementById("btn-key-settings");
    if (keySettingsBtn) {
      keySettingsBtn.addEventListener("click", () =>
        this.keyConfigManager.showModal(),
      );
    }

    // 创建按键设置弹窗
    this.keyConfigManager.createModal();
  }

  updateDifficultyDesc() {
    const desc = {
      easy: "AI随机落子，移动缓慢，适合新手练习",
      normal: "AI会评估位置，偶尔失误，适合普通玩家",
      hard: "AI采用最优策略，反应迅速，挑战性极高",
    };
    document.getElementById("difficulty-desc").textContent =
      desc[this.difficulty];
  }

  // ========== 游戏界面事件 ==========
  bindGameEvents() {
    // 键盘控制
    document.addEventListener("keydown", (e) => this.handleKeyDown(e));
    document.addEventListener("keyup", (e) => this.handleKeyUp(e));

    window.addEventListener("blur", () => {
      this.keysPressed.clear();
    });

    // 游戏控制按钮
    document.getElementById("btn-start-game").addEventListener("click", () => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "start_game" }));
      }
    });

    document.getElementById("btn-pause-game").addEventListener("click", () => {
      const now = Date.now();
      if (now - this.lastPauseTime < this.pauseDelay) return;
      this.lastPauseTime = now;

      const isPaused = this.roomState && this.roomState.global_paused;
      this.sendAction("pause", { intent: isPaused ? "resume" : "pause" });
    });

    document.getElementById("btn-reset-game").addEventListener("click", () => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "reset_game" }));
      }
    });

    document.getElementById("btn-leave-room").addEventListener("click", () => {
      this.leaveRoom();
    });
  }

  // ========== 键盘处理 ==========
  handleKeyDown(e) {
    // 如果正在绑定按键，处理绑定逻辑
    if (this.keyConfigManager.isBinding()) {
      e.preventDefault();
      this.keyConfigManager.handleBinding(e.key);
      this.updateInstructions();
      return;
    }

    if (!this.isConnected || !this.roomState || !this.roomState.game_active)
      return;
    const keyConfig = this.keyConfigManager.getConfig();
    if (this.roomState.global_paused && e.key !== keyConfig.pause) return;

    this.keysPressed.add(e.key);

    // 道具快捷键
    if (e.key === keyConfig.item1) {
      this.useItem(0);
      return;
    }
    if (e.key === keyConfig.item2) {
      this.useItem(1);
      return;
    }

    // 其他按键
    switch (e.key) {
      case keyConfig.moveLeft:
        e.preventDefault();
        this.sendAction("move_left");
        break;
      case keyConfig.moveRight:
        e.preventDefault();
        this.sendAction("move_right");
        break;
      case keyConfig.moveDown:
        e.preventDefault();
        this.sendAction("move_down");
        break;
      case keyConfig.rotate:
        e.preventDefault();
        this.sendAction("rotate");
        break;
      case keyConfig.hardDrop:
        e.preventDefault();
        this.sendHardDrop();
        break;
      case keyConfig.pause:
        e.preventDefault();
        this.sendPause();
        break;
    }
  }

  handleKeyUp(e) {
    this.keysPressed.delete(e.key);
  }

  sendHardDrop() {
    const now = Date.now();
    if (now - this.lastHardDropTime < this.hardDropDelay) return;
    this.lastHardDropTime = now;
    this.sendAction("hard_drop");
  }

  sendPause() {
    const now = Date.now();
    if (now - this.lastPauseTime < this.pauseDelay) return;
    this.lastPauseTime = now;

    const isPaused = this.roomState && this.roomState.global_paused;
    this.sendAction("pause", { intent: isPaused ? "resume" : "pause" });
  }

  useItem(index) {
    if (
      !this.playerGame ||
      !this.playerGame.items ||
      index >= this.playerGame.items.length
    )
      return;

    const itemType = this.playerGame.items[index];
    const target = itemType === "add_garbage" ? "opponent" : "self";

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "use_item",
          item_index: index,
          target: target,
        }),
      );
    }
  }

  // ========== WebSocket通信 ==========
  async createAIRoom() {
    try {
      const response = await fetch(TETRIS_CONFIG.API.AI_ROOMS, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nickname: this.nickname,
          difficulty: this.difficulty,
        }),
      });

      const data = await response.json();
      if (data.room_id) {
        this.roomId = data.room_id;
        this.connectToRoom();
      } else {
        alert("创建房间失败: " + (data.message || "未知错误"));
      }
    } catch (error) {
      console.error("创建AI房间失败:", error);
      alert("创建房间失败，请检查网络连接");
    }
  }

  connectToRoom() {
    const wsUrl = TETRIS_CONFIG.WS.AI(this.roomId);
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const fullUrl = `${protocol}//${window.location.host}${wsUrl}`;

    this.ws = new WebSocket(fullUrl);

    this.ws.onopen = () => {
      console.log("WebSocket connected");
      this.isConnected = true;
      this.updateConnectionStatus(true);

      // 发送昵称
      this.ws.send(JSON.stringify({ nickname: this.nickname }));

      // 切换到游戏界面
      this.showGameScreen();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log("WebSocket closed");
      this.isConnected = false;
      this.updateConnectionStatus(false);
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      alert("连接错误，请返回大厅重试");
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case "joined":
        this.playerId = message.data.player_id;
        this.itemTriggerLines =
          message.data.room_state?.item_trigger_lines || 5;
        break;
      case "room_update":
        this.handleRoomUpdate(message.data);
        break;
      case "chat":
        this.addChatMessage(message.data);
        break;
      case "item_effect":
        this.showItemEffect(message.data);
        break;
      case "error":
        console.error("Server error:", message.message);
        break;
    }
  }

  handleRoomUpdate(data) {
    this.roomState = data;
    this.playerGame = data.player1;
    this.aiGame = data.player2;
    this.itemTriggerLines =
      data?.item_trigger_lines || this.itemTriggerLines || 5;

    // 更新玩家信息
    document.getElementById("player-name").textContent =
      data.player1_nickname || "玩家";
    document.getElementById("ai-name").innerHTML =
      `<span class="ai-indicator">${data.player2_nickname || "AI"}</span>`;
    document.getElementById("display-difficulty").textContent =
      this.getDifficultyText(data.difficulty);

    // 更新游戏板
    if (this.playerGame) {
      this.renderBoard(this.playerCtx, this.playerGame);
      this.updatePlayerInfo(this.playerGame, "player");
    }

    if (this.aiGame) {
      this.renderBoard(this.aiCtx, this.aiGame);
      this.updatePlayerInfo(this.aiGame, "ai");
    }

    // 更新下一个方块预览
    if (this.playerGame && this.playerGame.next_piece) {
      this.renderNextPiece(this.playerGame.next_piece);
    }

    // 更新道具
    if (this.playerGame) {
      this.updateItems(this.playerGame.items, this.playerGame.lines_for_item);
    }

    // 更新游戏状态
    this.updateGameStatus(data);

    // 检查胜者
    if (data.winner) {
      this.showWinner(data.winner);
    }
  }

  getDifficultyText(diff) {
    const map = { easy: "简单", normal: "普通", hard: "困难" };
    return map[diff] || "普通";
  }

  updatePlayerInfo(game, prefix) {
    document.getElementById(`${prefix}-score`).textContent = game.score;
    document.getElementById(`${prefix}-lines`).textContent = game.lines_cleared;
    document.getElementById(`${prefix}-level`).textContent = game.level;
  }

  updateGameStatus(data) {
    const playerReadyEl = document.getElementById("player-ready-status");
    const aiReadyEl = document.getElementById("ai-ready-status");
    const startBtn = document.getElementById("btn-start-game");
    const pauseBtn = document.getElementById("btn-pause-game");
    const playerOverlay = document.getElementById("player-overlay");
    const aiOverlay = document.getElementById("ai-overlay");

    // 更新准备状态
    playerReadyEl.classList.toggle("hidden", !data.player1_ready);
    aiReadyEl.classList.toggle("hidden", !data.player2_ready);

    // 更新按钮文本
    if (data.game_active) {
      // 游戏开始
      if (!this.gameStartTime) {
        this.gameStartTime = Date.now();
        this.scoreSubmitted = false;
      }
      startBtn.textContent = "游戏中";
      startBtn.disabled = true;
      pauseBtn.textContent = data.global_paused ? "继续" : "暂停";
      playerOverlay.classList.add("hidden");
      aiOverlay.classList.add("hidden");
    } else if (data.player1_ready && data.player2_ready) {
      startBtn.textContent = "等待开始";
      startBtn.disabled = true;
    } else {
      startBtn.textContent = data.player1_ready ? "已准备" : "准备";
      startBtn.disabled = data.player1_ready;
    }

    // 更新暂停次数
    document.getElementById("player-pauses").textContent =
      data.player1_pauses || 0;

    // 游戏结束状态
    if (data.winner) {
      startBtn.textContent = "重新开始";
      startBtn.disabled = false;

      // 提交分数
      if (!this.scoreSubmitted && this.playerGame) {
        this.submitScore();
      }
    }
  }

  async submitScore() {
    if (!this.playerGame || this.scoreSubmitted) return;

    this.scoreSubmitted = true;

    const playTime = this.gameStartTime
      ? Math.floor((Date.now() - this.gameStartTime) / 1000)
      : 0;

    const scoreData = {
      player_name: this.nickname,
      score: this.playerGame.score,
      lines_cleared: this.playerGame.lines_cleared,
      level: this.playerGame.level,
      game_mode: "ai",
      difficulty: this.difficulty,
      play_time: playTime,
    };

    try {
      const response = await fetch(TETRIS_CONFIG.API.SUBMIT_SCORE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scoreData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log("分数提交成功:", result);

        // 如果排名在前10，显示提示
        if (result.rank <= 10) {
          this.showLeaderboardNotification(result.rank, result.record.score);
        }
      }
    } catch (error) {
      console.error("提交分数失败:", error);
    }
  }

  showLeaderboardNotification(rank, score) {
    const notification = document.createElement("div");
    notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #1a1a2e;
            padding: 30px 40px;
            border-radius: 20px;
            text-align: center;
            z-index: 1000;
            box-shadow: 0 10px 50px rgba(0,0,0,0.5);
            animation: fadeIn 0.5s ease;
        `;
    notification.innerHTML = `
            <h2 style="margin: 0 0 15px 0; font-size: 2em;">🎉 恭喜！</h2>
            <p style="font-size: 1.3em; margin: 0 0 10px 0;">你的分数 <strong>${score.toLocaleString()}</strong></p>
            <p style="font-size: 1.1em; margin: 0 0 20px 0;">排名第 <strong>${rank}</strong> 位！</p>
            <button onclick="window.location.href='/leaderboard'" style="
                padding: 10px 25px;
                background: #1a1a2e;
                color: #FFD700;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
            ">查看排行榜</button>
            <button onclick="this.parentElement.remove()" style="
                padding: 10px 25px;
                background: transparent;
                color: #1a1a2e;
                border: 2px solid #1a1a2e;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                margin-left: 10px;
            ">继续游戏</button>
        `;

    document.body.appendChild(notification);

    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, 8000);
  }

  showWinner(winner) {
    const winnerDisplay = document.getElementById("winner-display");
    const isPlayerWin = winner === this.playerId;

    winnerDisplay.textContent = isPlayerWin ? "🎉 你赢了！" : "😔 AI赢了！";
    winnerDisplay.className =
      "winner-display " + (isPlayerWin ? "win" : "lose");
    winnerDisplay.classList.remove("hidden");

    setTimeout(() => {
      winnerDisplay.classList.add("hidden");
    }, 5000);
  }

  // ========== 渲染 ==========
  drawBlock(ctx, x, y, color, blockSize) {
    const px = x * blockSize;
    const py = y * blockSize;

    // 主体
    ctx.fillStyle = color;
    ctx.fillRect(px + 1, py + 1, blockSize - 2, blockSize - 2);

    // 高光
    ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
    ctx.fillRect(px + 1, py + 1, blockSize - 2, 4);
    ctx.fillRect(px + 1, py + 1, 4, blockSize - 2);

    // 阴影
    ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
    ctx.fillRect(px + 1, py + blockSize - 5, blockSize - 2, 4);
    ctx.fillRect(px + blockSize - 5, py + 1, 4, blockSize - 2);
  }

  renderBoard(ctx, game) {
    const canvas = ctx.canvas;
    const blockSize = canvas.width / TETRIS_CONFIG.BOARD.WIDTH;

    // 清空画布 - 使用深黑色背景
    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 绘制网格 - 使用与主题匹配的深色
    ctx.strokeStyle = "#1a1a1a";
    ctx.lineWidth = 1;
    for (let x = 0; x <= TETRIS_CONFIG.BOARD.WIDTH; x++) {
      ctx.beginPath();
      ctx.moveTo(x * blockSize, 0);
      ctx.lineTo(x * blockSize, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y <= TETRIS_CONFIG.BOARD.HEIGHT; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * blockSize);
      ctx.lineTo(canvas.width, y * blockSize);
      ctx.stroke();
    }

    if (!game) return;

    // 绘制已固定的方块
    for (let y = 0; y < TETRIS_CONFIG.BOARD.HEIGHT; y++) {
      for (let x = 0; x < TETRIS_CONFIG.BOARD.WIDTH; x++) {
        const cell = game.board[y] ? game.board[y][x] : null;
        if (cell !== null && cell !== -1) {
          this.drawBlock(ctx, x, y, this.colors[cell] || "#888", blockSize);
        }
      }
    }

    // 绘制当前方块
    if (game.current_piece) {
      const piece = game.current_piece;
      const color = this.colors[piece.shape_index] || "#fff";

      for (let y = 0; y < piece.shape.length; y++) {
        for (let x = 0; x < piece.shape[y].length; x++) {
          if (piece.shape[y][x]) {
            const boardX = piece.x + x;
            const boardY = piece.y + y;
            if (boardY >= 0) {
              this.drawBlock(ctx, boardX, boardY, color, blockSize);
            }
          }
        }
      }
    }
  }

  renderNextPiece(piece) {
    const ctx = this.nextCtx;
    const canvas = this.nextCanvas;
    const blockSize = 25;

    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!piece) return;

    const offsetX = (canvas.width - piece.shape[0].length * blockSize) / 2;
    const offsetY = (canvas.height - piece.shape.length * blockSize) / 2;

    const color = this.colors[piece.shape_index] || "#fff";

    for (let y = 0; y < piece.shape.length; y++) {
      for (let x = 0; x < piece.shape[y].length; x++) {
        if (piece.shape[y][x]) {
          const px = offsetX + x * blockSize;
          const py = offsetY + y * blockSize;

          // 主体
          ctx.fillStyle = color;
          ctx.fillRect(px + 1, py + 1, blockSize - 2, blockSize - 2);

          // 高光
          ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
          ctx.fillRect(px + 1, py + 1, blockSize - 2, 4);
          ctx.fillRect(px + 1, py + 1, 4, blockSize - 2);

          // 阴影
          ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
          ctx.fillRect(px + 1, py + blockSize - 5, blockSize - 2, 4);
          ctx.fillRect(px + blockSize - 5, py + 1, 4, blockSize - 2);
        }
      }
    }
  }

  updateInitialItemText() {
    // 在收到后端配置前，先尝试从配置更新提示文本
    const triggerLines = this.itemTriggerLines || 5;
    const itemsList = document.getElementById("items-list");
    if (itemsList && itemsList.querySelector(".empty-items")) {
      itemsList.innerHTML = `<p class="empty-items">消除${triggerLines}行获得道具</p>`;
    }
  }

  updateItems(items, linesForItem) {
    const itemsList = document.getElementById("items-list");
    const progressEl = document.getElementById("item-progress");
    const linesEl = document.getElementById("lines-progress");

    // 获取触发行数配置
    const triggerLines = this.itemTriggerLines || 5;

    // 更新进度条
    const progress = ((linesForItem || 0) / triggerLines) * 100;
    progressEl.style.width = `${progress}%`;
    linesEl.textContent = linesForItem || 0;
    document.getElementById("lines-total").textContent = triggerLines;

    // 更新道具列表
    if (!items || items.length === 0) {
      itemsList.innerHTML = `<p class="empty-items">消除${triggerLines}行获得道具</p>`;
      return;
    }

    itemsList.innerHTML = items
      .map((item, index) => {
        const itemIcons = {
          add_garbage: "🗑️",
          clear_line: "✨",
        };
        const itemNames = {
          add_garbage: "垃圾行(1-3行)",
          clear_line: "清行(1-2行)",
        };
        const icon = itemIcons[item] || "🎁";
        const name = itemNames[item] || item;
        const keyConfig = this.keyConfigManager.getConfig();
        const keyHint =
          index < 2 ? `<span class="key-hint">${index + 1}</span>` : "";
        return `<div class="item" data-index="${index}">${icon} ${name}${keyHint}</div>`;
      })
      .join("");

    // 绑定道具点击
    itemsList.querySelectorAll(".item").forEach((el) => {
      el.addEventListener("click", () => {
        const index = parseInt(el.dataset.index);
        this.useItem(index);
      });
    });
  }

  addChatMessage(data) {
    const chatMessages = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${data.type}`;

    const time = new Date(data.timestamp).toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });

    msgDiv.innerHTML = `
            <span class="chat-time">${time}</span>
            <span class="chat-sender">${data.sender}:</span>
            <span class="chat-text">${data.message}</span>
        `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  showItemEffect(data) {
    const result = data.result;
    this.addChatMessage({
      type: "system",
      sender: "系统",
      message: result.message,
      timestamp: new Date().toISOString(),
    });
  }

  // ========== 工具方法 ==========
  sendAction(action, extra = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "action",
          action: action,
          ...extra,
        }),
      );
    }
  }

  updateConnectionStatus(connected) {
    const statusEl = document.getElementById("connection-status");
    if (statusEl) {
      statusEl.className =
        "connection-status " + (connected ? "connected" : "disconnected");
      statusEl.querySelector(".status-text").textContent = connected
        ? "已连接"
        : "未连接";
    }
  }

  showGameScreen() {
    document.getElementById("lobby-screen").classList.remove("active");
    document.getElementById("game-screen").classList.add("active");
  }

  leaveRoom() {
    if (this.ws) {
      this.ws.close();
    }
    window.location.href = "/";
  }
}

// 启动游戏
const game = new AIGame();
