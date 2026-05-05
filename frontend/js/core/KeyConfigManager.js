/**
 * 按键配置管理器
 * 统一管理按键配置的加载、保存和UI交互
 */

import { KEY_NAME_MAP, ACTION_NAMES } from '../config/key-bindings.config.js';

export class KeyConfigManager {
    /**
     * @param {string} storageKey - localStorage 键名
     * @param {Object} defaultConfig - 默认按键配置
     * @param {Object} options - 可选配置
     */
    constructor(storageKey, defaultConfig, options = {}) {
        this.storageKey = storageKey;
        this.defaultConfig = { ...defaultConfig };
        this.config = this.load();
        
        // UI 相关状态
        this.isBindingKey = false;
        this.currentBindingAction = null;
        this.modalElement = null;
        
        // 配置选项
        this.options = {
            onConfigChange: null,  // 配置变更回调
            onBindingStart: null,  // 开始绑定回调
            onBindingEnd: null,    // 结束绑定回调
            ...options
        };
    }

    /**
     * 从 localStorage 加载配置
     */
    load() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved) {
                const config = JSON.parse(saved);
                // 合并保存的配置和默认配置，确保所有按键都有值
                return { ...this.defaultConfig, ...config };
            }
        } catch (e) {
            console.error('加载按键配置失败:', e);
        }
        return { ...this.defaultConfig };
    }

    /**
     * 保存配置到 localStorage
     */
    save() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.config));
            if (this.options.onConfigChange) {
                this.options.onConfigChange(this.config);
            }
        } catch (e) {
            console.error('保存按键配置失败:', e);
        }
    }

    /**
     * 重置为默认配置
     */
    reset() {
        this.config = { ...this.defaultConfig };
        this.save();
        this.updateUI();
        return this.config;
    }

    /**
     * 获取按键显示名称
     */
    getKeyDisplayName(key) {
        return KEY_NAME_MAP[key] || key.toUpperCase();
    }

    /**
     * 获取操作显示名称
     */
    getActionDisplayName(action) {
        return ACTION_NAMES[action] || action;
    }

    /**
     * 绑定按键
     */
    bindKey(action, key) {
        // 检查是否与其他按键冲突
        const existingAction = Object.entries(this.config).find(
            ([k, v]) => v === key && k !== action
        );

        if (existingAction) {
            // 交换按键
            this.config[existingAction[0]] = this.config[action];
        }

        this.config[action] = key;
        this.save();
        this.updateUI();
        return this.config;
    }

    /**
     * 获取当前配置
     */
    getConfig() {
        return { ...this.config };
    }

    // ========== UI 相关方法 ==========

    /**
     * 创建按键设置弹窗
     */
    createModal(container = document.body) {
        if (this.modalElement) return this.modalElement;

        const modal = document.createElement('div');
        modal.id = `key-config-modal-${this.storageKey}`;
        modal.className = 'key-config-modal hidden';

        // 构建配置项 HTML
        const configItems = Object.keys(this.defaultConfig).map(action => `
            <div class="key-config-item" data-action="${action}">
                <span class="key-label">${this.getActionDisplayName(action)}</span>
                <button class="key-value" data-action="${action}"></button>
            </div>
        `).join('');

        modal.innerHTML = `
            <div class="key-config-content">
                <h3>🎮 按键设置</h3>
                <div class="key-config-list">
                    ${configItems}
                </div>
                <div class="key-config-status hidden" id="key-binding-status">
                    请按下一个键...
                </div>
                <div class="key-config-buttons">
                    <button class="btn btn-secondary btn-reset-keys">恢复默认</button>
                    <button class="btn btn-primary btn-close-keys">关闭</button>
                </div>
            </div>
        `;

        container.appendChild(modal);
        this.modalElement = modal;

        // 绑定事件
        this.bindModalEvents();
        this.updateUI();

        return modal;
    }

    /**
     * 绑定弹窗事件
     */
    bindModalEvents() {
        if (!this.modalElement) return;

        // 按键设置按钮点击事件
        this.modalElement.querySelectorAll('.key-value').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                this.startBinding(action);
            });
        });

        // 恢复默认按钮
        this.modalElement.querySelector('.btn-reset-keys').addEventListener('click', () => {
            if (confirm('确定要恢复默认按键设置吗？')) {
                this.reset();
            }
        });

        // 关闭按钮
        this.modalElement.querySelector('.btn-close-keys').addEventListener('click', () => {
            this.hideModal();
        });

        // 点击遮罩关闭
        this.modalElement.addEventListener('click', (e) => {
            if (e.target === this.modalElement) {
                this.hideModal();
            }
        });
    }

    /**
     * 更新 UI 显示
     */
    updateUI() {
        if (!this.modalElement) return;

        this.modalElement.querySelectorAll('.key-value').forEach(btn => {
            const action = btn.dataset.action;
            btn.textContent = this.getKeyDisplayName(this.config[action]);
        });
    }

    /**
     * 显示弹窗
     */
    showModal() {
        if (!this.modalElement) {
            this.createModal();
        }
        this.updateUI();
        this.modalElement.classList.remove('hidden');
    }

    /**
     * 隐藏弹窗
     */
    hideModal() {
        if (this.modalElement) {
            this.modalElement.classList.add('hidden');
        }
        this.cancelBinding();
    }

    /**
     * 开始按键绑定
     */
    startBinding(action) {
        this.isBindingKey = true;
        this.currentBindingAction = action;

        const status = this.modalElement?.querySelector('#key-binding-status');
        if (status) {
            status.textContent = `正在设置 "${this.getActionDisplayName(action)}"，请按下一个键...`;
            status.classList.remove('hidden');
        }

        // 高亮当前按钮
        const btn = this.modalElement?.querySelector(`.key-value[data-action="${action}"]`);
        if (btn) btn.classList.add('binding');

        if (this.options.onBindingStart) {
            this.options.onBindingStart(action);
        }
    }

    /**
     * 处理按键绑定
     */
    handleBinding(key) {
        if (!this.currentBindingAction) return false;

        this.bindKey(this.currentBindingAction, key);
        this.cancelBinding();
        return true;
    }

    /**
     * 取消按键绑定
     */
    cancelBinding() {
        this.isBindingKey = false;
        this.currentBindingAction = null;

        const status = this.modalElement?.querySelector('#key-binding-status');
        if (status) status.classList.add('hidden');

        this.modalElement?.querySelectorAll('.key-value.binding').forEach(btn => {
            btn.classList.remove('binding');
        });

        if (this.options.onBindingEnd) {
            this.options.onBindingEnd();
        }
    }

    /**
     * 检查是否正在绑定按键
     */
    isBinding() {
        return this.isBindingKey;
    }

    /**
     * 销毁管理器
     */
    destroy() {
        if (this.modalElement && this.modalElement.parentNode) {
            this.modalElement.parentNode.removeChild(this.modalElement);
        }
        this.modalElement = null;
    }
}

export default KeyConfigManager;
