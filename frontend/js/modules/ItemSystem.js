/**
 * 道具系统模块
 * 管理道具的显示和使用
 */

import { ITEM_CONFIG } from "./Config.js";

export class ItemSystem {
  constructor() {
    this.selectedItemIndex = -1;
    this.pendingItemType = null;
    this.itemTriggerLines = ITEM_CONFIG.TRIGGER_LINES;
  }

  /**
   * 获取道具信息
   * @param {string} itemType
   * @returns {object}
   */
  getItemInfo(itemType) {
    return (
      ITEM_CONFIG.TYPES[itemType.toUpperCase()] || {
        name: "未知",
        icon: "❓",
        desc: "",
      }
    );
  }

  /**
   * 更新道具 UI
   * @param {object} myGame
   * @param {HTMLElement} itemsListEl
   * @param {HTMLElement} progressEl
   * @param {HTMLElement} linesProgressEl
   * @param {HTMLElement} linesTotalEl
   */
  updateItemsUI(
    myGame,
    itemsListEl,
    progressEl,
    linesProgressEl,
    linesTotalEl,
  ) {
    if (!myGame) return;

    // 更新进度条
    const linesForItem = myGame.lines_for_item || 0;
    const progressPercent = (linesForItem / this.itemTriggerLines) * 100;

    if (progressEl) {
      progressEl.style.width = `${progressPercent}%`;
    }
    if (linesProgressEl) {
      linesProgressEl.textContent = linesForItem;
    }
    if (linesTotalEl) {
      linesTotalEl.textContent = this.itemTriggerLines;
    }

    // 更新道具列表
    if (!itemsListEl) return;

    const items = myGame.items || [];

    if (items.length === 0) {
      itemsListEl.innerHTML = `<p class="empty-items">消除${this.itemTriggerLines}行获得道具</p>`;
      return;
    }

    itemsListEl.innerHTML = items
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
    itemsListEl.querySelectorAll(".item-badge").forEach((badge) => {
      badge.addEventListener("click", (e) => {
        const index = parseInt(e.currentTarget.dataset.index);
        this.onItemClick(index, items[index]);
      });
    });
  }

  /**
   * 处理道具点击
   * @param {number} index
   * @param {string} itemType
   */
  onItemClick(index, itemType) {
    if (this.selectedItemIndex === index) {
      this.selectedItemIndex = -1;
      return;
    }

    this.selectedItemIndex = index;
    this.pendingItemType = itemType;

    // 根据道具类型自动选择目标
    const target = itemType === "add_garbage" ? "opponent" : "self";
    return { index, itemType, target };
  }

  /**
   * 清除选择
   */
  clearSelection() {
    this.selectedItemIndex = -1;
    this.pendingItemType = null;
  }

  /**
   * 显示道具效果通知
   * @param {string} message
   * @param {HTMLElement} container
   */
  showNotification(message, container = document.body) {
    const notification = document.createElement("div");
    notification.className = "item-notification";
    notification.textContent = message;
    container.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  /**
   * 处理道具效果消息
   * @param {object} data
   * @param {string} myPlayerType
   * @returns {string|null}
   */
  handleItemEffect(data, myPlayerType) {
    const { result, from_nickname: fromNickname } = data;
    const effect = result.effect || {};
    let message = "";

    if (effect.type === "add_garbage") {
      const linesAdded = result.lines_added || 1;
      if (result.to_player && result.to_player.includes(myPlayerType)) {
        message = `${fromNickname} 给你添加了 ${linesAdded} 行垃圾行！`;
      } else {
        message = `${fromNickname} 给对手添加了 ${linesAdded} 行垃圾行！`;
      }
    } else if (effect.type === "clear_line") {
      const linesCleared = result.lines_cleared || 1;
      message = `${fromNickname} 清除了 ${linesCleared} 行！`;
    }

    return message || null;
  }
}

export default ItemSystem;
