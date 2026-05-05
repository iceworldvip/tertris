/**
 * 俄罗斯方块对战版 - 支持双人和聊天
 * 使用 TETRIS_CONFIG 配置中心和 KeyConfigManager 按键管理器
 */

class TetrisGame {
  constructor() {
    this.nickname = "";
    this.roomId = null;

    // 随机昵称词库 - 使用配置中心
    this.nicknameAdjectives = TETRIS_CONFIG.NICKNAME.ADJECTIVES;
    this.nicknameNouns = TETRIS_CONFIG.NICKNAME.NOUNS;
    this.playerType = null; // 'player1', 'player2', 'spectator'
    this.playerId = null;
    this.ws = null;
    this.isConnected = false;

    // 游戏状态
    this.roomState = null;
    this.player1Game = null;
    this.player2Game = null;

    // Canvas
    this.p1Canvas = document.getElementById("player1-board");
    this.p1Ctx = this.p1Canvas.getContext("2d");
    this.p2Canvas = document.getElementById("player2-board");
    this.p2Ctx = this.p2Canvas.getContext("2d");
    this.nextCanvas = document.getElementById("next-piece");
    this.nextCtx = this.nextCanvas.getContext("2d");

    // 方块颜色 - 使用配置中心
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
    this.pendingItemType = null;

    // 初始化按键配置管理器
    this.keyConfigManager = new KeyConfigManager(
      TETRIS_CONFIG.STORAGE.VERSUS_KEY_CONFIG,
      TETRIS_CONFIG.KEYS.FULL,
    );

    this.init();
  }

  init() {
    this.bindLobbyEvents();
    this.bindGameEvents();
    this.loadRoomList();

    // 生成并设置随机昵称
    const randomNickname = this.generateRandomNickname();
    document.getElementById("nickname").value = randomNickname;
    this.nickname = randomNickname;

    // 初始化按键设置UI
    this.initKeyConfigUI();

    // 更新操作说明
    this.updateInstructions();

    // 初始化道具提示文本
    this.updateInitialItemText();
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

    // 更新道具说明，添加快捷键
    const itemHelp = document.querySelector(".item-help");
    if (itemHelp) {
      itemHelp.innerHTML = `
                <li><span class="item-icon">🗑️</span> 垃圾行 - 给对手加1-3行 <span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.item1)}</span></li>
                <li><span class="item-icon">✨</span> 清行 - 自己消1-2行 <span class="key">${this.keyConfigManager.getKeyDisplayName(keyConfig.item2)}</span></li>
            `;
    }
  }

  generateRandomNickname() {
    const adj =
      this.nicknameAdjectives[
        Math.floor(Math.random() * this.nicknameAdjectives.length)
      ];
    const noun =
      this.nicknameNouns[Math.floor(Math.random() * this.nicknameNouns.length)];
    const num = Math.floor(Math.random() * 100);
    return `${adj}${noun}${num}`;
  }

  // ========== 大厅界面事件 ==========
  bindLobbyEvents() {
    // 创建房间
    document.getElementById("btn-create-room").addEventListener("click", () => {
      this.nickname =
        document.getElementById("nickname").value.trim() || "玩家";
      this.createRoom();
    });

    // 加入房间
    document.getElementById("btn-join-room").addEventListener("click", () => {
      const roomId = document
        .getElementById("room-id-input")
        .value.trim()
        .toUpperCase();
      if (roomId) {
        this.nickname =
          document.getElementById("nickname").value.trim() || "玩家";
        this.joinRoom(roomId);
      }
    });

    // 刷新房间列表
    document
      .getElementById("btn-refresh-rooms")
      .addEventListener("click", () => {
        this.loadRoomList();
      });

    // 回车键加入房间
    document
      .getElementById("room-id-input")
      .addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          document.getElementById("btn-join-room").click();
        }
      });
  }

  // ========== 游戏界面事件 ==========
  bindGameEvents() {
    // 键盘控制
    this.keydownHandler = (e) => this.handleKeyDown(e);
    this.keyupHandler = (e) => this.handleKeyUp(e);
    document.addEventListener("keydown", this.keydownHandler);
    document.addEventListener("keyup", this.keyupHandler);

    // 窗口失去焦点时清空按键状态
    window.addEventListener("blur", () => {
      this.keysPressed.clear();
    });

    // 游戏控制按钮
    document.getElementById("btn-start-game").addEventListener("click", () => {
      // 发送准备/开始游戏消息给服务器
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(
          JSON.stringify({
            type: "start_game",
          }),
        );
      }
    });

    document.getElementById("btn-pause-game").addEventListener("click", () => {
      // 防抖检查
      const now = Date.now();
      if (now - this.lastPauseTime < this.pauseDelay) {
        return; // 忽略快速点击
      }
      this.lastPauseTime = now;

      // 根据当前状态发送明确的意图
      const isPaused = this.roomState && this.roomState.global_paused;
      const intent = isPaused ? "resume" : "pause";
      this.sendAction("pause", { intent });
    });

    document.getElementById("btn-reset-game").addEventListener("click", () => {
      // 发送重置确认消息
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(
          JSON.stringify({
            type: "reset_game",
          }),
        );
      }
    });

    // 离开房间
    document.getElementById("btn-leave-room").addEventListener("click", () => {
      this.leaveRoom();
    });

    // 聊天
    document.getElementById("btn-send-chat").addEventListener("click", () => {
      this.sendChat();
    });

    document.getElementById("chat-input").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.sendChat();
      }
    });

    // 道具目标选择
    document.getElementById("btn-target-self").addEventListener("click", () => {
      this.useItem("self");
    });

    document
      .getElementById("btn-target-opponent")
      .addEventListener("click", () => {
        this.useItem("opponent");
      });

    document.getElementById("btn-cancel-item").addEventListener("click", () => {
      this.closeItemModal();
    });
  }

  // ========== 房间操作 ==========
  async loadRoomList() {
    try {
      const response = await fetch(TETRIS_CONFIG.API.ROOMS);
      const data = await response.json();
      this.renderRoomList(data.rooms);
    } catch (error) {
      console.error("加载房间列表失败:", error);
    }
  }

  renderRoomList(rooms) {
    const container = document.getElementById("room-list");
    if (rooms.length === 0) {
      container.innerHTML = '<p class="empty">暂无房间，创建一个吧！</p>';
      return;
    }

    container.innerHTML = rooms
      .map(
        (room) => `
            <div class="room-item" data-room-id="${room.room_id}">
                <div class="room-item-info">
                    <div class="room-item-id">房间 ${room.room_id}</div>
                    <div class="room-item-status">
                        玩家: ${room.player_count}/2 | 观战: ${room.spectator_count}人
                        ${room.game_started ? "| 游戏中" : ""}
                    </div>
                </div>
                <button class="btn btn-small btn-secondary" onclick="game.joinRoom('${room.room_id}')">
                    加入
                </button>
            </div>
        `,
      )
      .join("");

    // 绑定加入按钮
    container.querySelectorAll(".room-item").forEach((item) => {
      const roomId = item.dataset.roomId;
      item.querySelector("button").addEventListener("click", () => {
        this.nickname =
          document.getElementById("nickname").value.trim() || "玩家";
        this.joinRoom(roomId);
      });
    });
  }

  async createRoom() {
    try {
      const response = await fetch(TETRIS_CONFIG.API.ROOMS, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nickname: this.nickname }),
      });
      const data = await response.json();
      this.joinRoom(data.room_id);
    } catch (error) {
      console.error("创建房间失败:", error);
      alert("创建房间失败");
    }
  }

  joinRoom(roomId) {
    this.roomId = roomId;

    // 切换到游戏界面
    document.getElementById("lobby-screen").classList.remove("active");
    document.getElementById("game-screen").classList.add("active");
    document.getElementById("display-room-id").textContent = roomId;

    // 连接WebSocket
    this.connectWebSocket();
  }

  leaveRoom() {
    if (this.ws) {
      this.ws.close();
    }
    this.resetGame();

    // 切换回大厅
    document.getElementById("game-screen").classList.remove("active");
    document.getElementById("lobby-screen").classList.add("active");

    // 刷新房间列表
    this.loadRoomList();
  }

  // ========== WebSocket连接 ==========
  connectWebSocket() {
    const wsUrl = TETRIS_CONFIG.WS.ROOM(this.roomId);
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const fullUrl = `${protocol}//${window.location.host}${wsUrl}`;
    this.ws = new WebSocket(fullUrl);

    this.ws.onopen = () => {
      console.log("WebSocket已连接");
      this.isConnected = true;
      this.updateConnectionStatus("connected", "已连接");

      // 发送昵称
      this.ws.send(
        JSON.stringify({
          type: "join",
          nickname: this.nickname,
        }),
      );
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log("WebSocket已断开");
      this.isConnected = false;
      this.updateConnectionStatus("disconnected", "已断开");
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket错误:", error);
      this.updateConnectionStatus("disconnected", "连接错误");
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case "joined":
        this.playerType = message.data.player_type;
        this.playerId = message.data.player_id;
        this.roomState = message.data.room_state;
        this.itemTriggerLines =
          message.data.room_state?.item_trigger_lines || 5;
        this.updateUI();
        break;

      case "room_update":
        this.roomState = message.data;
        this.itemTriggerLines =
          message.data?.item_trigger_lines || this.itemTriggerLines || 5;
        this.updateUI();
        this.drawGames();
        break;

      case "chat":
        this.addChatMessage(message.data);
        break;

      case "error":
        console.error("服务器错误:", message.message);
        alert(message.message);
        // 如果是昵称重复错误，返回大厅
        if (
          message.message.includes("昵称") ||
          message.message.includes("已被使用")
        ) {
          this.leaveRoom();
        }
        break;

      case "item_effect":
        this.handleItemEffect(message.data);
        break;
    }
  }

  // ========== UI更新 ==========
  updateUI() {
    if (!this.roomState) return;

    // 更新玩家1信息
    if (this.roomState.player1) {
      const p1Name = this.roomState.player1_nickname || "玩家1";
      document.getElementById("player1-name").textContent = p1Name;
      document
        .getElementById("player1-name")
        .classList.toggle("me", this.playerType === "player1");

      let p1StatusText, p1StatusClass;
      if (this.roomState.player1.game_over) {
        p1StatusText = "游戏结束";
        p1StatusClass = "gameover";
      } else if (this.roomState.global_paused) {
        p1StatusText = "已暂停";
        p1StatusClass = "paused";
      } else if (this.roomState.game_active) {
        p1StatusText = "游戏中";
        p1StatusClass = "playing";
      } else {
        p1StatusText = "准备";
        p1StatusClass = "ready";
      }
      document.getElementById("player1-status").textContent = p1StatusText;
      document.getElementById("player1-status").className =
        `player-status ${p1StatusClass}`;

      document.getElementById("player1-score").textContent =
        this.roomState.player1.score;
      document.getElementById("player1-lines").textContent =
        this.roomState.player1.lines_cleared;
      document.getElementById("player1-level").textContent =
        this.roomState.player1.level;

      // 更新准备状态
      const p1ReadyStatus = document.getElementById("player1-ready-status");
      if (this.roomState.player1_ready && !this.roomState.game_active) {
        p1ReadyStatus.classList.remove("hidden");
      } else {
        p1ReadyStatus.classList.add("hidden");
      }

      // 更新暂停次数
      const p1Pauses = document.getElementById("player1-pauses");
      const p1PauseCount = p1Pauses.parentElement;
      p1Pauses.textContent = this.roomState.player1_pauses || 0;
      if ((this.roomState.player1_pauses || 0) === 0) {
        p1PauseCount.classList.add("empty");
      } else {
        p1PauseCount.classList.remove("empty");
      }

      // 更新覆盖层
      const p1Overlay = document.getElementById("player1-overlay");
      if (this.roomState.player1.game_over) {
        p1Overlay.classList.remove("hidden");
        document.getElementById("player1-overlay-title").textContent =
          "游戏结束";
      } else if (!this.roomState.game_active) {
        p1Overlay.classList.remove("hidden");
        const waitingText = this.roomState.player1_ready
          ? "等待对手确认"
          : "点击准备";
        document.getElementById("player1-overlay-title").textContent =
          waitingText;
      } else if (this.roomState.global_paused) {
        p1Overlay.classList.remove("hidden");
        document.getElementById("player1-overlay-title").textContent = "已暂停";
      } else {
        p1Overlay.classList.add("hidden");
      }
    } else {
      document.getElementById("player1-name").textContent = "等待玩家...";
      document.getElementById("player1-status").textContent = "等待中";
      document.getElementById("player1-overlay").classList.remove("hidden");
      document.getElementById("player1-overlay-title").textContent = "等待加入";
    }

    // 更新玩家2信息
    if (this.roomState.player2) {
      const p2Name = this.roomState.player2_nickname || "玩家2";
      document.getElementById("player2-name").textContent = p2Name;
      document
        .getElementById("player2-name")
        .classList.toggle("me", this.playerType === "player2");

      let p2StatusText, p2StatusClass;
      if (this.roomState.player2.game_over) {
        p2StatusText = "游戏结束";
        p2StatusClass = "gameover";
      } else if (this.roomState.global_paused) {
        p2StatusText = "已暂停";
        p2StatusClass = "paused";
      } else if (this.roomState.game_active) {
        p2StatusText = "游戏中";
        p2StatusClass = "playing";
      } else {
        p2StatusText = "准备";
        p2StatusClass = "ready";
      }
      document.getElementById("player2-status").textContent = p2StatusText;
      document.getElementById("player2-status").className =
        `player-status ${p2StatusClass}`;

      document.getElementById("player2-score").textContent =
        this.roomState.player2.score;
      document.getElementById("player2-lines").textContent =
        this.roomState.player2.lines_cleared;
      document.getElementById("player2-level").textContent =
        this.roomState.player2.level;

      // 更新准备状态
      const p2ReadyStatus = document.getElementById("player2-ready-status");
      if (this.roomState.player2_ready && !this.roomState.game_active) {
        p2ReadyStatus.classList.remove("hidden");
      } else {
        p2ReadyStatus.classList.add("hidden");
      }

      // 更新暂停次数
      const p2Pauses = document.getElementById("player2-pauses");
      const p2PauseCount = p2Pauses.parentElement;
      p2Pauses.textContent = this.roomState.player2_pauses || 0;
      if ((this.roomState.player2_pauses || 0) === 0) {
        p2PauseCount.classList.add("empty");
      } else {
        p2PauseCount.classList.remove("empty");
      }

      // 更新覆盖层
      const p2Overlay = document.getElementById("player2-overlay");
      if (this.roomState.player2.game_over) {
        p2Overlay.classList.remove("hidden");
        document.getElementById("player2-overlay-title").textContent =
          "游戏结束";
      } else if (!this.roomState.game_active) {
        p2Overlay.classList.remove("hidden");
        const waitingText = this.roomState.player2_ready
          ? "等待对手确认"
          : "点击准备";
        document.getElementById("player2-overlay-title").textContent =
          waitingText;
      } else if (this.roomState.global_paused) {
        p2Overlay.classList.remove("hidden");
        document.getElementById("player2-overlay-title").textContent = "已暂停";
      } else {
        p2Overlay.classList.add("hidden");
      }
    } else {
      document.getElementById("player2-name").textContent = "等待玩家...";
      document.getElementById("player2-status").textContent = "等待中";
      document.getElementById("player2-overlay").classList.remove("hidden");
      document.getElementById("player2-overlay-title").textContent = "等待加入";
    }

    // 更新胜者显示
    const winnerDisplay = document.getElementById("winner-display");
    if (this.roomState.winner) {
      winnerDisplay.classList.remove("hidden");
      if (this.roomState.winner === "tie") {
        winnerDisplay.textContent = "平局！";
      } else {
        const winnerName =
          this.roomState.winner === this.roomState.player1?.player_id
            ? this.roomState.player1_nickname
            : this.roomState.player2_nickname;
        winnerDisplay.textContent = `${winnerName} 获胜！`;
      }
    } else {
      winnerDisplay.classList.add("hidden");
    }

    // 更新观战人数
    document.getElementById("spectator-count").textContent =
      `观战: ${this.roomState.spectator_count}人`;

    // 加载聊天记录
    if (this.roomState.chat_history) {
      this.loadChatHistory(this.roomState.chat_history);
    }

    // 更新按钮状态（只有游戏开始后才能暂停和重置）
    const isPlayer =
      this.playerType === "player1" || this.playerType === "player2";
    const gameActive = this.roomState.game_active;
    const gameOver =
      this.roomState.player1?.game_over ||
      this.roomState.player2?.game_over ||
      this.roomState.winner;

    // 暂停按钮：游戏开始且未结束，且是当前玩家
    // 恢复操作不需要检查暂停次数
    const pauseBtn = document.getElementById("btn-pause-game");
    const isPaused = this.roomState.global_paused;
    const canPauseAction = isPlayer && gameActive && !gameOver;
    const canPause =
      canPauseAction &&
      (isPaused || // 恢复操作不需要检查次数
        (this.playerType === "player1" &&
          (this.roomState.player1_pauses || 0) > 0) ||
        (this.playerType === "player2" &&
          (this.roomState.player2_pauses || 0) > 0));
    pauseBtn.disabled = !canPause;
    pauseBtn.style.opacity = canPause ? "1" : "0.5";
    // 根据状态显示按钮文字
    pauseBtn.textContent = isPaused ? "恢复" : "暂停";

    // 重置按钮：游戏已结束（可以重置）
    const resetBtn = document.getElementById("btn-reset-game");
    const canReset = isPlayer && gameOver && !this.roomState.global_paused;
    resetBtn.disabled = !canReset;
    resetBtn.style.opacity = canReset ? "1" : "0.5";

    // 开始游戏按钮：游戏未开始且是当前玩家且未准备
    const startBtn = document.getElementById("btn-start-game");
    const isReady =
      (this.playerType === "player1" && this.roomState.player1_ready) ||
      (this.playerType === "player2" && this.roomState.player2_ready);
    const canStart = isPlayer && !gameActive && !isReady;
    startBtn.disabled = !canStart;
    startBtn.style.opacity = canStart ? "1" : "0.5";
    // 根据当前玩家准备状态显示按钮文字
    if (this.playerType === "player1") {
      startBtn.textContent = this.roomState.player1_ready ? "已准备" : "准备";
    } else if (this.playerType === "player2") {
      startBtn.textContent = this.roomState.player2_ready ? "已准备" : "准备";
    }

    // 更新道具栏
    this.updateItemsUI();
  }

  // ========== 道具系统 ==========
  updateInitialItemText() {
    // 在收到后端配置前，先尝试从配置更新提示文本
    const triggerLines = this.itemTriggerLines || 5;
    const itemsList = document.getElementById("items-list");
    if (itemsList && itemsList.querySelector(".empty-items")) {
      itemsList.innerHTML = `<p class="empty-items">消除${triggerLines}行获得道具</p>`;
    }
  }

  updateItemsUI() {
    // 只为自己显示道具
    const myGame =
      this.playerType === "player1"
        ? this.roomState.player1
        : this.playerType === "player2"
          ? this.roomState.player2
          : null;

    if (!myGame) {
      document.getElementById("items-container").classList.add("hidden");
      return;
    }

    document.getElementById("items-container").classList.remove("hidden");

    // 获取触发行数配置
    const triggerLines = this.itemTriggerLines || 5;

    // 更新进度条
    const linesForItem = myGame.lines_for_item || 0;
    const progressPercent = (linesForItem / triggerLines) * 100;
    document.getElementById("item-progress").style.width =
      `${progressPercent}%`;
    document.getElementById("lines-progress").textContent = linesForItem;
    document.getElementById("lines-total").textContent = triggerLines;

    // 更新道具列表
    const itemsList = document.getElementById("items-list");
    const items = myGame.items || [];

    if (items.length === 0) {
      itemsList.innerHTML = `<p class="empty-items">消除${triggerLines}行获得道具</p>`;
    } else {
      itemsList.innerHTML = items
        .map((item, index) => {
          const itemInfo = this.getItemInfo(item);
          const selectedClass =
            index === this.selectedItemIndex ? "selected" : "";
          return `
                    <div class="item-badge ${item} ${selectedClass}" data-index="${index}">
                        <span class="item-icon">${itemInfo.icon}</span>
                        <span>${itemInfo.name}</span>
                    </div>
                `;
        })
        .join("");

      // 绑定点击事件
      itemsList.querySelectorAll(".item-badge").forEach((badge) => {
        badge.addEventListener("click", (e) => {
          const index = parseInt(e.currentTarget.dataset.index);
          this.onItemClick(index);
        });
      });
    }
  }

  getItemInfo(itemType) {
    const itemMap = {
      add_garbage: { name: "垃圾行", icon: "🗑️", desc: "给对手加1-3行" },
      clear_line: { name: "清行", icon: "✨", desc: "自己消1-2行" },
    };
    return itemMap[itemType] || { name: "未知", icon: "❓", desc: "" };
  }

  onItemClick(index) {
    if (this.selectedItemIndex === index) {
      // 再次点击取消选择
      this.selectedItemIndex = -1;
      this.updateItemsUI();
      return;
    }

    this.selectedItemIndex = index;

    const myGame =
      this.playerType === "player1"
        ? this.roomState.player1
        : this.roomState.player2;
    const itemType = myGame.items[index];
    this.pendingItemType = itemType;

    // 根据道具类型决定是否需要选择目标
    if (itemType === "add_garbage") {
      // 垃圾行直接对对手使用
      this.useItem("opponent");
    } else if (itemType === "clear_line") {
      // 清行直接对自己使用
      this.useItem("self");
    }

    this.selectedItemIndex = -1;
    this.updateItemsUI();
  }

  showItemModal(itemType) {
    const modal = document.getElementById("item-target-modal");
    const itemInfo = this.getItemInfo(itemType);
    document.getElementById("item-modal-desc").textContent =
      `${itemInfo.name} ${itemInfo.desc} - 选择使用目标`;
    modal.classList.remove("hidden");
  }

  closeItemModal() {
    document.getElementById("item-target-modal").classList.add("hidden");
    this.pendingItemType = null;
  }

  useItem(target) {
    if (this.selectedItemIndex < 0 && !this.pendingItemType) return;

    const itemIndex =
      this.selectedItemIndex >= 0
        ? this.selectedItemIndex
        : this.findItemIndex(this.pendingItemType);

    if (itemIndex < 0) return;

    // 发送使用道具消息
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // 对于tetris_clear，后端使用固定的3x3中心消除，不需要额外参数
      this.ws.send(
        JSON.stringify({
          type: "use_item",
          item_index: itemIndex,
          target: target,
        }),
      );
    }

    this.closeItemModal();
    this.selectedItemIndex = -1;
    this.pendingItemType = null;
  }

  findItemIndex(itemType) {
    const myGame =
      this.playerType === "player1"
        ? this.roomState.player1
        : this.roomState.player2;
    if (!myGame || !myGame.items) return -1;
    return myGame.items.indexOf(itemType);
  }

  handleItemEffect(data) {
    const result = data.result;
    const fromNickname = data.from_nickname;

    // 显示道具效果通知
    const effect = result.effect || {};
    let message = "";

    if (effect.type === "add_garbage") {
      const linesAdded = result.lines_added || 1;
      if (result.to_player && result.to_player.includes(this.playerType)) {
        message = `${fromNickname} 给你添加了 ${linesAdded} 行垃圾行！`;
      } else {
        message = `${fromNickname} 给对手添加了 ${linesAdded} 行垃圾行！`;
      }
    } else if (effect.type === "clear_line") {
      const linesCleared = result.lines_cleared || 1;
      message = `${fromNickname} 清除了 ${linesCleared} 行！`;
    }

    if (message) {
      this.showNotification(message);
    }
  }

  showNotification(message) {
    // 创建通知元素
    const notification = document.createElement("div");
    notification.className = "item-notification";
    notification.textContent = message;
    document.body.appendChild(notification);

    // 3秒后移除
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  updateConnectionStatus(status, text) {
    const dot = document.querySelector(".status-dot");
    const statusText = document.querySelector(".status-text");

    if (status === "connected") {
      dot.classList.add("connected");
    } else {
      dot.classList.remove("connected");
    }
    statusText.textContent = text;
  }

  // ========== 游戏渲染 ==========
  drawGames() {
    if (this.roomState) {
      if (this.roomState.player1) {
        this.drawBoard(this.p1Ctx, this.roomState.player1);
      } else {
        this.drawEmptyBoard(this.p1Ctx);
      }

      if (this.roomState.player2) {
        this.drawBoard(this.p2Ctx, this.roomState.player2);
      } else {
        this.drawEmptyBoard(this.p2Ctx);
      }

      // 绘制下一个方块（显示当前玩家的）
      const myGame =
        this.playerType === "player1"
          ? this.roomState.player1
          : this.playerType === "player2"
            ? this.roomState.player2
            : null;
      if (myGame && myGame.next_piece) {
        this.drawNextPiece(myGame.next_piece);
      }
    }
  }

  drawBoard(ctx, gameState) {
    const blockSize = TETRIS_CONFIG.BOARD.BLOCK_SIZE;
    const width = TETRIS_CONFIG.BOARD.WIDTH;
    const height = TETRIS_CONFIG.BOARD.HEIGHT;

    // 清空画布
    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, width * blockSize, height * blockSize);

    // 绘制网格
    ctx.strokeStyle = "#1a1a1a";
    ctx.lineWidth = 1;
    for (let x = 0; x <= width; x++) {
      ctx.beginPath();
      ctx.moveTo(x * blockSize, 0);
      ctx.lineTo(x * blockSize, height * blockSize);
      ctx.stroke();
    }
    for (let y = 0; y <= height; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * blockSize);
      ctx.lineTo(width * blockSize, y * blockSize);
      ctx.stroke();
    }

    // 绘制已固定的方块
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const cell = gameState.board[y][x];
        if (cell !== -1) {
          this.drawBlock(ctx, x, y, this.colors[cell], blockSize);
        }
      }
    }

    // 绘制当前方块
    if (gameState.current_piece) {
      const piece = gameState.current_piece;
      for (let y = 0; y < piece.shape.length; y++) {
        for (let x = 0; x < piece.shape[y].length; x++) {
          if (piece.shape[y][x]) {
            const boardX = piece.x + x;
            const boardY = piece.y + y;
            if (boardY >= 0) {
              this.drawBlock(ctx, boardX, boardY, piece.color, blockSize);
            }
          }
        }
      }
    }
  }

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

  drawEmptyBoard(ctx) {
    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, 300, 600);

    ctx.fillStyle = "#333";
    ctx.font = "20px Arial";
    ctx.textAlign = "center";
    ctx.fillText("等待玩家加入...", 150, 300);
  }

  drawNextPiece(nextPiece) {
    const ctx = this.nextCtx;
    const blockSize = 25;

    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, 120, 120);

    if (!nextPiece) return;

    const shape = nextPiece.shape;
    const offsetX = (120 - shape[0].length * blockSize) / 2;
    const offsetY = (120 - shape.length * blockSize) / 2;

    for (let y = 0; y < shape.length; y++) {
      for (let x = 0; x < shape[y].length; x++) {
        if (shape[y][x]) {
          const px = offsetX + x * blockSize;
          const py = offsetY + y * blockSize;

          ctx.fillStyle = nextPiece.color;
          ctx.fillRect(px + 1, py + 1, blockSize - 2, blockSize - 2);

          ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
          ctx.fillRect(px + 1, py + 1, blockSize - 2, 3);
        }
      }
    }
  }

  // ========== 键盘控制 ==========
  handleKeyDown(e) {
    // 如果正在绑定按键，处理绑定逻辑
    if (this.keyConfigManager.isBinding()) {
      e.preventDefault();
      this.keyConfigManager.handleBinding(e.key);
      this.updateInstructions();
      return;
    }

    // 忽略浏览器自动重复的键盘事件
    if (e.repeat) return;

    if (this.keysPressed.has(e.key)) return;
    this.keysPressed.add(e.key);

    const now = Date.now();
    if (now - this.lastMoveTime < this.moveDelay) return;
    this.lastMoveTime = now;

    // 只有玩家可以控制
    if (this.playerType !== "player1" && this.playerType !== "player2") return;

    // 使用按键配置映射
    const keyConfig = this.keyConfigManager.getConfig();
    const key = e.key;

    if (key === keyConfig.moveLeft) {
      e.preventDefault();
      this.sendAction("move_left");
    } else if (key === keyConfig.moveRight) {
      e.preventDefault();
      this.sendAction("move_right");
    } else if (key === keyConfig.moveDown) {
      e.preventDefault();
      this.sendAction("move_down");
    } else if (key === keyConfig.rotate) {
      e.preventDefault();
      this.sendAction("rotate");
    } else if (key === keyConfig.hardDrop) {
      e.preventDefault();
      // hard_drop 独立防抖检查
      const nowDrop = Date.now();
      if (nowDrop - this.lastHardDropTime >= this.hardDropDelay) {
        this.lastHardDropTime = nowDrop;
        this.sendAction("hard_drop");
      }
    } else if (key.toLowerCase() === keyConfig.pause.toLowerCase()) {
      e.preventDefault();
      this.sendAction("pause");
    } else if (key === keyConfig.item1) {
      e.preventDefault();
      this.useItemByIndex(0);
    } else if (key === keyConfig.item2) {
      e.preventDefault();
      this.useItemByIndex(1);
    } else if (key === keyConfig.item3) {
      e.preventDefault();
      this.useItemByIndex(2);
    }
  }

  handleKeyUp(e) {
    this.keysPressed.delete(e.key);
  }

  // ========== 道具快捷键使用 ==========
  useItemByIndex(index) {
    // 检查是否在游戏中
    if (!this.roomState || !this.roomState.game_active) return;

    const myGame =
      this.playerType === "player1"
        ? this.roomState.player1
        : this.playerType === "player2"
          ? this.roomState.player2
          : null;

    if (!myGame || !myGame.items || index >= myGame.items.length) return;

    const itemType = myGame.items[index];

    // 根据道具类型自动选择目标
    if (itemType === "add_garbage") {
      // 垃圾行 → 自动对对手使用
      this.sendUseItem(index, "opponent");
    } else if (itemType === "clear_line") {
      // 清行 → 自动对自己使用
      this.sendUseItem(index, "self");
    } else if (itemType === "tetris_clear") {
      // 形状消除 → 对自己使用（需要额外参数）
      const targetParams = {};
      if (myGame.current_piece) {
        targetParams.shape = myGame.current_piece.shape;
        targetParams.x = myGame.current_piece.x;
        targetParams.y = myGame.current_piece.y;
      }
      this.sendUseItem(index, "self", targetParams);
    }
  }

  sendUseItem(itemIndex, target, targetParams = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "use_item",
          item_index: itemIndex,
          target: target,
          target_params: targetParams,
        }),
      );
    }
  }

  // ========== 按键设置UI ==========
  initKeyConfigUI() {
    // 创建设置按钮
    const settingsBtn = document.createElement("button");
    settingsBtn.id = "btn-key-settings";
    settingsBtn.className = "btn btn-small btn-secondary";
    settingsBtn.textContent = "⚙️ 按键设置";
    settingsBtn.style.marginTop = "10px";

    // 将按钮添加到中间区域
    const centerArea = document.querySelector(".center-area");
    const gameControls = document.querySelector(".game-controls");
    centerArea.insertBefore(settingsBtn, gameControls.nextSibling);

    // 绑定点击事件
    settingsBtn.addEventListener("click", () =>
      this.keyConfigManager.showModal(),
    );

    // 创建按键设置弹窗
    this.keyConfigManager.createModal();
  }

  // ========== 消息发送 ==========
  sendAction(action, extraData = {}) {
    if (!this.isConnected || !this.ws) return;

    this.ws.send(
      JSON.stringify({
        type: "action",
        action: action,
        ...extraData,
      }),
    );
  }

  sendChat() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();

    if (!message || !this.isConnected) return;

    this.ws.send(
      JSON.stringify({
        type: "chat",
        message: message,
      }),
    );

    input.value = "";
  }

  // ========== 聊天显示 ==========
  loadChatHistory(messages) {
    const container = document.getElementById("chat-messages");
    container.innerHTML = "";
    messages.forEach((msg) => this.addChatMessage(msg));
  }

  addChatMessage(msg) {
    const container = document.getElementById("chat-messages");
    const isOwn = msg.sender === this.nickname;
    const isSystem = msg.type === "system";

    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${isSystem ? "system" : isOwn ? "own" : "other"}`;

    if (!isSystem) {
      msgDiv.innerHTML = `
                <div class="sender">${msg.sender}</div>
                <div class="content">${this.escapeHtml(msg.message)}</div>
            `;
    } else {
      msgDiv.innerHTML = `<div class="content">${this.escapeHtml(msg.message)}</div>`;
    }

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  showMessage(text) {
    // 可以添加一个 toast 提示
    console.log(text);
  }

  resetGame() {
    this.roomId = null;
    this.playerType = null;
    this.playerId = null;
    this.roomState = null;
    this.ws = null;
    this.isConnected = false;

    // 重置道具系统
    this.selectedItemIndex = -1;
    this.pendingItemType = null;
    this.closeItemModal();

    // 清空画布
    this.drawEmptyBoard(this.p1Ctx);
    this.drawEmptyBoard(this.p2Ctx);
    this.nextCtx.fillStyle = "#0a0a0a";
    this.nextCtx.fillRect(0, 0, 120, 120);

    // 清空聊天
    document.getElementById("chat-messages").innerHTML = "";
  }
}

// 启动游戏
const game = new TetrisGame();
