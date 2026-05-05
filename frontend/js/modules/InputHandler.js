/**
 * 输入处理模块
 * 管理键盘输入和游戏控制
 */

import { TIMING_CONFIG } from './Config.js';

export class InputHandler {
    constructor() {
        this.keysPressed = new Set();
        this.lastMoveTime = 0;
        this.lastHardDropTime = 0;
        this.lastPauseTime = 0;
        this.moveDelay = TIMING_CONFIG.MOVE_DELAY;
        this.hardDropDelay = TIMING_CONFIG.HARD_DROP_DELAY;
        this.pauseDelay = TIMING_CONFIG.PAUSE_DELAY;

        this.keyBindings = {
            moveLeft: 'ArrowLeft',
            moveRight: 'ArrowRight',
            moveDown: 'ArrowDown',
            rotate: 'ArrowUp',
            hardDrop: ' ',
            pause: 'p',
            item1: '1',
            item2: '2',
            item3: '3'
        };

        this.handlers = new Map();
        this.isBinding = false;
        this.bindingCallback = null;

        this.setupEventListeners();
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));

        window.addEventListener('blur', () => {
            this.keysPressed.clear();
        });
    }

    /**
     * 处理按键按下
     * @param {KeyboardEvent} e
     */
    handleKeyDown(e) {
        // 如果正在绑定按键
        if (this.isBinding) {
            e.preventDefault();
            if (this.bindingCallback) {
                this.bindingCallback(e.key);
            }
            return;
        }

        // 忽略浏览器自动重复的键盘事件
        if (e.repeat) return;

        if (this.keysPressed.has(e.key)) return;
        this.keysPressed.add(e.key);

        const now = Date.now();
        if (now - this.lastMoveTime < this.moveDelay) return;
        this.lastMoveTime = now;

        const key = e.key;
        const keyLower = key.toLowerCase();

        if (key === this.keyBindings.moveLeft) {
            e.preventDefault();
            this.emit('move', 'left');
        } else if (key === this.keyBindings.moveRight) {
            e.preventDefault();
            this.emit('move', 'right');
        } else if (key === this.keyBindings.moveDown) {
            e.preventDefault();
            this.emit('move', 'down');
        } else if (key === this.keyBindings.rotate) {
            e.preventDefault();
            this.emit('rotate');
        } else if (key === this.keyBindings.hardDrop) {
            e.preventDefault();
            const nowDrop = Date.now();
            if (nowDrop - this.lastHardDropTime >= this.hardDropDelay) {
                this.lastHardDropTime = nowDrop;
                this.emit('hardDrop');
            }
        } else if (keyLower === this.keyBindings.pause.toLowerCase()) {
            e.preventDefault();
            const nowPause = Date.now();
            if (nowPause - this.lastPauseTime >= this.pauseDelay) {
                this.lastPauseTime = nowPause;
                this.emit('pause');
            }
        } else if (key === this.keyBindings.item1) {
            e.preventDefault();
            this.emit('useItem', 0);
        } else if (key === this.keyBindings.item2) {
            e.preventDefault();
            this.emit('useItem', 1);
        } else if (key === this.keyBindings.item3) {
            e.preventDefault();
            this.emit('useItem', 2);
        }
    }

    /**
     * 处理按键释放
     * @param {KeyboardEvent} e
     */
    handleKeyUp(e) {
        this.keysPressed.delete(e.key);
    }

    /**
     * 注册事件处理器
     * @param {string} event
     * @param {function} handler
     */
    on(event, handler) {
        if (!this.handlers.has(event)) {
            this.handlers.set(event, []);
        }
        this.handlers.get(event).push(handler);
    }

    /**
     * 触发事件
     * @param {string} event
     * @param {*} data
     */
    emit(event, data) {
        const handlers = this.handlers.get(event);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
    }

    /**
     * 开始绑定按键
     * @param {function} callback
     */
    startBinding(callback) {
        this.isBinding = true;
        this.bindingCallback = (key) => {
            this.isBinding = false;
            this.bindingCallback = null;
            callback(key);
        };
    }

    /**
     * 更新按键绑定
     * @param {object} bindings
     */
    updateBindings(bindings) {
        Object.assign(this.keyBindings, bindings);
    }

    /**
     * 获取按键的显示名称
     * @param {string} key
     * @returns {string}
     */
    getKeyDisplayName(key) {
        const displayMap = {
            'ArrowLeft': '←',
            'ArrowRight': '→',
            'ArrowUp': '↑',
            'ArrowDown': '↓',
            ' ': '空格'
        };
        return displayMap[key] || key.toUpperCase();
    }
}

export default InputHandler;
