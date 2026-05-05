/**
 * WebSocket 客户端模块
 * 管理与服务器的 WebSocket 连接
 */

import { WS_CONFIG } from './Config.js';

export class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 2000;
        this.messageHandlers = new Map();
        this.isConnected = false;
    }

    /**
     * 连接到房间
     * @param {string} roomId - 房间ID
     * @param {string} nickname - 玩家昵称
     * @param {boolean} isAI - 是否是AI房间
     * @returns {Promise<boolean>}
     */
    connect(roomId, nickname, isAI = false) {
        return new Promise((resolve, reject) => {
            const wsUrl = isAI ? WS_CONFIG.AI_ROOM(roomId) : WS_CONFIG.ROOM(roomId);
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const fullUrl = `${protocol}//${window.location.host}${wsUrl}`;

            try {
                this.ws = new WebSocket(fullUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;

                    // 发送昵称
                    this.send({ nickname });
                    resolve(true);
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (e) {
                        console.error('Failed to parse message:', e);
                    }
                };

                this.ws.onclose = () => {
                    console.log('WebSocket closed');
                    this.isConnected = false;
                    this.emit('disconnected', {});
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };
            } catch (e) {
                reject(e);
            }
        });
    }

    /**
     * 处理收到的消息
     * @param {object} message
     */
    handleMessage(message) {
        const { type, data, message: msgText } = message;

        switch (type) {
            case 'joined':
                this.emit('joined', data);
                break;
            case 'room_update':
                this.emit('roomUpdate', data);
                break;
            case 'chat':
                this.emit('chat', data);
                break;
            case 'item_effect':
                this.emit('itemEffect', data);
                break;
            case 'error':
                console.error('Server error:', msgText);
                this.emit('error', { message: msgText });
                break;
            default:
                console.warn('Unknown message type:', type);
        }
    }

    /**
     * 发送消息
     * @param {object} data
     * @returns {boolean}
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
            return true;
        }
        return false;
    }

    /**
     * 发送游戏动作
     * @param {string} action
     */
    sendAction(action, extraData = {}) {
        return this.send({ type: 'action', action, ...extraData });
    }

    /**
     * 发送开始游戏请求
     */
    sendStartGame() {
        return this.send({ type: 'start_game' });
    }

    /**
     * 发送重置游戏请求
     */
    sendResetGame() {
        return this.send({ type: 'reset_game' });
    }

    /**
     * 发送暂停请求
     * @param {string} intent - 'pause', 'resume', 或 'toggle'
     */
    sendPause(intent = 'toggle') {
        return this.sendAction('pause', { intent });
    }

    /**
     * 发送聊天消息
     * @param {string} message
     */
    sendChat(message) {
        return this.send({ type: 'chat', message });
    }

    /**
     * 发送使用道具请求
     * @param {number} itemIndex
     * @param {string} target
     */
    sendUseItem(itemIndex, target) {
        return this.send({ type: 'use_item', item_index: itemIndex, target });
    }

    /**
     * 注册消息处理器
     * @param {string} event
     * @param {function} handler
     */
    on(event, handler) {
        if (!this.messageHandlers.has(event)) {
            this.messageHandlers.set(event, []);
        }
        this.messageHandlers.get(event).push(handler);
    }

    /**
     * 触发事件
     * @param {string} event
     * @param {object} data
     */
    emit(event, data) {
        const handlers = this.messageHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
    }

    /**
     * 断开连接
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.isConnected = false;
        }
    }
}

export default WebSocketClient;
