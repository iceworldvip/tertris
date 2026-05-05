/**
 * 俄罗斯方块游戏主类（模块化版本）
 * 整合所有模块的游戏控制器
 */

import { WebSocketClient } from './WebSocketClient.js';
import { Renderer } from './Renderer.js';
import { ItemSystem } from './ItemSystem.js';
import { InputHandler } from './InputHandler.js';
import { UIManager } from './UIManager.js';
import { NICKNAME_CONFIG, API_CONFIG } from './Config.js';

export class TetrisGame {
    constructor() {
        // 初始化状态
        this.nickname = '';
        this.roomId = null;
        this.playerType = null;
        this.playerId = null;
        this.roomState = null;

        // 初始化模块
        this.wsClient = new WebSocketClient();
        this.renderer = new Renderer(
            document.getElementById('player1-board'),
            document.getElementById('player2-board'),
            document.getElementById('next-piece')
        );
        this.itemSystem = new ItemSystem();
        this.inputHandler = new InputHandler();
        this.uiManager = new UIManager();

        // 绑定事件
        this.bindEvents();
        this.bindInputHandlers();
    }

    /**
     * 初始化游戏
     */
    init() {
        this.generateNickname();
        this.loadRoomList();
        this.setupLobbyEvents();
    }

    /**
     * 生成随机昵称
     */
    generateNickname() {
        const adj = NICKNAME_CONFIG.ADJECTIVES[Math.floor(Math.random() * NICKNAME_CONFIG.ADJECTIVES.length)];
        const noun = NICKNAME_CONFIG.NOUNS[Math.floor(Math.random() * NICKNAME_CONFIG.NOUNS.length)];
        const num = Math.floor(Math.random() * 100);
        this.nickname = `${adj}${noun}${num}`;

        const nicknameInput = document.getElementById('nickname');
        if (nicknameInput) nicknameInput.value = this.nickname;
    }

    /**
     * 绑定 WebSocket 事件
     */
    bindEvents() {
        this.wsClient.on('joined', (data) => {
            this.playerType = data.player_type;
            this.playerId = data.player_id;
            this.roomState = data.room_state;
            this.onJoined();
        });

        this.wsClient.on('roomUpdate', (data) => {
            this.roomState = data;
            this.onRoomUpdate();
        });

        this.wsClient.on('chat', (data) => {
            this.uiManager.addChatMessage(data);
        });

        this.wsClient.on('itemEffect', (data) => {
            const message = this.itemSystem.handleItemEffect(data, this.playerType);
            if (message) {
                this.itemSystem.showNotification(message);
            }
        });

        this.wsClient.on('error', (data) => {
            console.error('Server error:', data.message);
            alert(data.message);
        });

        this.wsClient.on('disconnected', () => {
            this.uiManager.updateConnectionStatus('disconnected', '已断开');
        });
    }

    /**
     * 绑定输入处理器
     */
    bindInputHandlers() {
        this.inputHandler.on('move', (direction) => {
            if (!this.canControl()) return;
            this.wsClient.sendAction(`move_${direction}`);
        });

        this.inputHandler.on('rotate', () => {
            if (!this.canControl()) return;
            this.wsClient.sendAction('rotate');
        });

        this.inputHandler.on('hardDrop', () => {
            if (!this.canControl()) return;
            this.wsClient.sendAction('hard_drop');
        });

        this.inputHandler.on('pause', () => {
            if (!this.roomState?.game_active) return;
            const isPaused = this.roomState.global_paused;
            this.wsClient.sendPause(isPaused ? 'resume' : 'pause');
        });

        this.inputHandler.on('useItem', (index) => {
            if (!this.canControl()) return;
            const myGame = this.getMyGame();
            if (!myGame?.items?.[index]) return;

            const itemType = myGame.items[index];
            const target = itemType === 'add_garbage' ? 'opponent' : 'self';
            this.wsClient.sendUseItem(index, target);
        });
    }

    /**
     * 设置大厅事件
     */
    setupLobbyEvents() {
        const createBtn = document.getElementById('btn-create-room');
        const joinBtn = document.getElementById('btn-join-room');
        const refreshBtn = document.getElementById('btn-refresh-rooms');
        const roomIdInput = document.getElementById('room-id-input');

        if (createBtn) {
            createBtn.addEventListener('click', () => this.createRoom());
        }

        if (joinBtn) {
            joinBtn.addEventListener('click', () => {
                const roomId = roomIdInput?.value.trim().toUpperCase();
                if (roomId) this.joinRoom(roomId);
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadRoomList());
        }

        if (roomIdInput) {
            roomIdInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') joinBtn?.click();
            });
        }

        // 游戏控制按钮
        const startBtn = document.getElementById('btn-start-game');
        const pauseBtn = document.getElementById('btn-pause-game');
        const resetBtn = document.getElementById('btn-reset-game');
        const leaveBtn = document.getElementById('btn-leave-room');
        const sendChatBtn = document.getElementById('btn-send-chat');
        const chatInput = document.getElementById('chat-input');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.wsClient.sendStartGame());
        }

        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                const isPaused = this.roomState?.global_paused;
                this.wsClient.sendPause(isPaused ? 'resume' : 'pause');
            });
        }

        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.wsClient.sendResetGame());
        }

        if (leaveBtn) {
            leaveBtn.addEventListener('click', () => this.leaveRoom());
        }

        if (sendChatBtn && chatInput) {
            sendChatBtn.addEventListener('click', () => {
                const text = chatInput.value.trim();
                if (text) {
                    this.wsClient.sendChat(text);
                    chatInput.value = '';
                }
            });

            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendChatBtn.click();
            });
        }
    }

    /**
     * 加载房间列表
     */
    async loadRoomList() {
        try {
            const response = await fetch(API_CONFIG.ROOMS);
            const data = await response.json();
            this.uiManager.renderRoomList(data.rooms || [], (roomId) => {
                this.joinRoom(roomId);
            });
        } catch (error) {
            console.error('加载房间列表失败:', error);
        }
    }

    /**
     * 创建房间
     */
    async createRoom() {
        try {
            const nicknameInput = document.getElementById('nickname');
            this.nickname = nicknameInput?.value.trim() || '玩家';

            const response = await fetch(API_CONFIG.ROOMS, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nickname: this.nickname })
            });

            const data = await response.json();
            this.joinRoom(data.room_id);
        } catch (error) {
            console.error('创建房间失败:', error);
            alert('创建房间失败');
        }
    }

    /**
     * 加入房间
     * @param {string} roomId
     */
    joinRoom(roomId) {
        this.roomId = roomId;

        // 切换界面
        document.getElementById('lobby-screen')?.classList.remove('active');
        document.getElementById('game-screen')?.classList.add('active');

        const displayRoomId = document.getElementById('display-room-id');
        if (displayRoomId) displayRoomId.textContent = roomId;

        // 连接 WebSocket
        this.wsClient.connect(roomId, this.nickname);
    }

    /**
     * 离开房间
     */
    leaveRoom() {
        this.wsClient.disconnect();
        this.roomState = null;

        // 切换回大厅
        document.getElementById('game-screen')?.classList.remove('active');
        document.getElementById('lobby-screen')?.classList.add('active');

        this.loadRoomList();
    }

    /**
     * 成功加入房间回调
     */
    onJoined() {
        this.uiManager.updateConnectionStatus('connected', '已连接');
        this.updateUI();
    }

    /**
     * 房间状态更新回调
     */
    onRoomUpdate() {
        this.updateUI();
        this.renderer.render(this.roomState, this.playerType);
    }

    /**
     * 更新 UI
     */
    updateUI() {
        if (!this.roomState) return;

        const isPlayer1 = this.playerType === 'player1';
        const isPlayer2 = this.playerType === 'player2';

        // 更新玩家信息
        this.uiManager.updatePlayerInfo(
            'player1',
            this.roomState.player1,
            this.roomState,
            isPlayer1
        );
        this.uiManager.updatePlayerInfo(
            'player2',
            this.roomState.player2,
            this.roomState,
            isPlayer2
        );

        // 更新胜者
        this.uiManager.updateWinner(this.roomState);

        // 更新观战人数
        this.uiManager.updateText('spectator-count', `观战: ${this.roomState.spectator_count}人`);

        // 更新按钮状态
        this.uiManager.updateButtonStates(this.roomState, this.playerType);

        // 更新道具 UI
        const myGame = this.getMyGame();
        this.itemSystem.updateItemsUI(
            myGame,
            document.getElementById('items-list'),
            document.getElementById('item-progress'),
            document.getElementById('lines-progress'),
            document.getElementById('lines-total')
        );
    }

    /**
     * 获取当前玩家的游戏状态
     * @returns {object|null}
     */
    getMyGame() {
        if (!this.roomState) return null;
        return this.playerType === 'player1' ? this.roomState.player1 :
               this.playerType === 'player2' ? this.roomState.player2 : null;
    }

    /**
     * 检查是否可以控制游戏
     * @returns {boolean}
     */
    canControl() {
        if (!this.roomState) return false;
        if (!this.roomState.game_active) return false;
        if (this.roomState.global_paused) return false;
        if (this.playerType !== 'player1' && this.playerType !== 'player2') return false;

        const myGame = this.getMyGame();
        return myGame && !myGame.game_over;
    }
}

export default TetrisGame;
