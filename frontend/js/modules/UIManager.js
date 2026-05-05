/**
 * UI 管理模块
 * 管理游戏界面更新
 */

export class UIManager {
  constructor() {
    this.elements = {};
  }

  /**
   * 缓存 DOM 元素
   * @param {object} selectors
   */
  cacheElements(selectors) {
    for (const [key, selector] of Object.entries(selectors)) {
      this.elements[key] = document.querySelector(selector);
    }
  }

  /**
   * 获取缓存的元素
   * @param {string} key
   * @returns {HTMLElement|null}
   */
  get(key) {
    return this.elements[key] || document.getElementById(key);
  }

  /**
   * 更新玩家信息
   * @param {string} playerPrefix - 'player1' 或 'player2'
   * @param {object} playerState
   * @param {object} roomState
   * @param {boolean} isMe
   */
  updatePlayerInfo(playerPrefix, playerState, roomState, isMe) {
    if (!playerState) {
      this.updateText(`${playerPrefix}-name`, "等待玩家...");
      this.updateText(`${playerPrefix}-status`, "等待中");
      this.showOverlay(playerPrefix, "等待加入");
      return;
    }

    // 更新昵称
    const nickname =
      roomState[`${playerPrefix}_nickname`] ||
      `${playerPrefix === "player1" ? "玩家1" : "玩家2"}`;
    this.updateText(`${playerPrefix}-name`, nickname);
    this.toggleClass(`${playerPrefix}-name`, "me", isMe);

    // 更新状态
    let statusText, statusClass;
    if (playerState.game_over) {
      statusText = "游戏结束";
      statusClass = "gameover";
    } else if (roomState.global_paused) {
      statusText = "已暂停";
      statusClass = "paused";
    } else if (roomState.game_active) {
      statusText = "游戏中";
      statusClass = "playing";
    } else {
      statusText = "准备";
      statusClass = "ready";
    }

    this.updateText(`${playerPrefix}-status`, statusText);
    this.updateClass(`${playerPrefix}-status`, `player-status ${statusClass}`);

    // 更新分数
    this.updateText(`${playerPrefix}-score`, playerState.score);
    this.updateText(`${playerPrefix}-lines`, playerState.lines_cleared);
    this.updateText(`${playerPrefix}-level`, playerState.level);

    // 更新准备状态
    const isReady = roomState[`${playerPrefix}_ready`];
    this.toggleVisibility(
      `${playerPrefix}-ready-status`,
      isReady && !roomState.game_active,
    );

    // 更新暂停次数
    const pauses = roomState[`${playerPrefix}_pauses`] || 0;
    this.updateText(`${playerPrefix}-pauses`, pauses);
    this.toggleClass(`${playerPrefix}-pause-count`, "empty", pauses === 0);

    // 更新覆盖层
    this.updatePlayerOverlay(playerPrefix, playerState, roomState, isReady);
  }

  /**
   * 更新玩家覆盖层
   * @param {string} playerPrefix
   * @param {object} playerState
   * @param {object} roomState
   * @param {boolean} isReady
   */
  updatePlayerOverlay(playerPrefix, playerState, roomState, isReady) {
    const overlay = this.get(`${playerPrefix}-overlay`);
    if (!overlay) return;

    let showOverlay = false;
    let titleText = "";

    if (playerState.game_over) {
      showOverlay = true;
      titleText = "游戏结束";
    } else if (!roomState.game_active) {
      showOverlay = true;
      titleText = isReady ? "等待对手确认" : "点击准备";
    } else if (roomState.global_paused) {
      showOverlay = true;
      titleText = "已暂停";
    }

    this.toggleVisibility(`${playerPrefix}-overlay`, showOverlay);
    if (showOverlay) {
      this.updateText(`${playerPrefix}-overlay-title`, titleText);
    }
  }

  /**
   * 更新胜者显示
   * @param {object} roomState
   */
  updateWinner(roomState) {
    const winnerDisplay = this.get("winner-display");
    if (!winnerDisplay) return;

    if (roomState.winner) {
      winnerDisplay.classList.remove("hidden");
      let text = "";
      if (roomState.winner === "tie") {
        text = "平局！";
      } else {
        const winnerName =
          roomState.winner === roomState.player1?.player_id
            ? roomState.player1_nickname
            : roomState.player2_nickname;
        text = `${winnerName} 获胜！`;
      }
      winnerDisplay.textContent = text;
    } else {
      winnerDisplay.classList.add("hidden");
    }
  }

  /**
   * 更新按钮状态
   * @param {object} roomState
   * @param {string} playerType
   */
  updateButtonStates(roomState, playerType) {
    const isPlayer = playerType === "player1" || playerType === "player2";
    const gameActive = roomState.game_active;
    const gameOver =
      roomState.winner ||
      roomState.player1?.game_over ||
      roomState.player2?.game_over;
    const isPaused = roomState.global_paused;
    const isReady = roomState[`${playerType}_ready`];

    // 暂停按钮
    const canPause = isPlayer && gameActive && !gameOver;
    const canPauseAction =
      canPause && (isPaused || (roomState[`${playerType}_pauses`] || 0) > 0);
    this.setButtonState(
      "btn-pause-game",
      canPauseAction,
      isPaused ? "恢复" : "暂停",
    );

    // 重置按钮：游戏已结束（可以重置）
    const canReset = isPlayer && gameOver && !roomState.global_paused;
    this.setButtonState("btn-reset-game", canReset, "重置");

    // 开始按钮
    const canStart = isPlayer && !gameActive && !isReady;
    this.setButtonState(
      "btn-start-game",
      canStart,
      isReady ? "已准备" : "准备",
    );
  }

  /**
   * 设置按钮状态
   * @param {string} id
   * @param {boolean} enabled
   * @param {string} text
   */
  setButtonState(id, enabled, text) {
    const btn = this.get(id);
    if (btn) {
      btn.disabled = !enabled;
      btn.style.opacity = enabled ? "1" : "0.5";
      btn.textContent = text;
    }
  }

  /**
   * 更新文本内容
   * @param {string} id
   * @param {string} text
   */
  updateText(id, text) {
    const el = this.get(id);
    if (el) el.textContent = String(text);
  }

  /**
   * 更新元素类名
   * @param {string} id
   * @param {string} className
   */
  updateClass(id, className) {
    const el = this.get(id);
    if (el) el.className = className;
  }

  /**
   * 切换类名
   * @param {string} id
   * @param {string} className
   * @param {boolean} add
   */
  toggleClass(id, className, add) {
    const el = this.get(id);
    if (el) {
      if (add) el.classList.add(className);
      else el.classList.remove(className);
    }
  }

  /**
   * 切换可见性
   * @param {string} id
   * @param {boolean} show
   */
  toggleVisibility(id, show) {
    const el = this.get(id);
    if (el) {
      if (show) el.classList.remove("hidden");
      else el.classList.add("hidden");
    }
  }

  /**
   * 显示覆盖层
   * @param {string} playerPrefix
   * @param {string} text
   */
  showOverlay(playerPrefix, text) {
    this.toggleVisibility(`${playerPrefix}-overlay`, true);
    this.updateText(`${playerPrefix}-overlay-title`, text);
  }

  /**
   * 更新连接状态显示
   * @param {string} status
   * @param {string} text
   */
  updateConnectionStatus(status, text) {
    const dot = document.querySelector(".status-dot");
    const statusText = document.querySelector(".status-text");

    if (dot) {
      if (status === "connected") dot.classList.add("connected");
      else dot.classList.remove("connected");
    }
    if (statusText) statusText.textContent = text;
  }

  /**
   * 渲染房间列表
   * @param {Array} rooms
   * @param {function} onJoinClick
   */
  renderRoomList(rooms, onJoinClick) {
    const container = this.get("room-list");
    if (!container) return;

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
                <button class="btn btn-small btn-secondary btn-join" data-room-id="${room.room_id}">
                    加入
                </button>
            </div>
        `,
      )
      .join("");

    // 绑定加入按钮事件
    container.querySelectorAll(".btn-join").forEach((btn) => {
      btn.addEventListener("click", () => {
        onJoinClick(btn.dataset.roomId);
      });
    });
  }

  /**
   * 添加聊天消息
   * @param {object} msg
   */
  addChatMessage(msg) {
    const chatMessages = this.get("chat-messages");
    if (!chatMessages) return;

    const isSystem = msg.type === "system";
    const div = document.createElement("div");
    div.className = `chat-message ${isSystem ? "system" : ""}`;
    div.innerHTML = `
            <span class="chat-sender">${msg.sender}:</span>
            <span class="chat-text">${msg.message}</span>
        `;

    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

export default UIManager;
