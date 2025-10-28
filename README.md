# Telegram 会员收款 Bot

一个功能完整的 Telegram Bot 会员支付系统，支持 TRON USDT 自动收款和闲鱼手动审核支付。

## ✨ 核心功能

### 1. 双支付通道
- **TRON USDT (TRC20)**: 自动监控链上支付，无需人工干预，秒级到账
- **闲鱼支付**: 用户提交订单号，管理员手动审核

### 2. 自动会员管理
- ✅ 支付成功后自动激活会员
- ✅ 自动邀请用户加入私有频道
- ✅ 会员到期自动检测
- ✅ 支持续费延期

### 3. 智能订单管理
- ⏰ 闲鱼订单自动超时清理（默认30分钟）
- 🧹 USDT订单自动监控和过期处理
- 🛡️ 防刷单机制（限制待支付订单数量）
- 📊 订单状态自动同步
- 🔄 后台定时任务自动清理过期订单

### 4. 灵活的套餐配置
- **多套餐模式**: 支持配置多个会员套餐（月/季/年）
- **单套餐模式**: 固定价格，点击直接支付，流程更简洁
- 📝 配置方式：在 `.env` 中设置 `ENABLE_MULTIPLE_PLANS=true/false`

### 5. 自定义欢迎页面
- 🖼️ 支持自定义欢迎图片（Logo/海报）
- ✏️ 自定义欢迎文案
- 👨‍💼 联系客服按钮
- 🎯 全程按钮化操作，无需输入命令

### 6. 广告发送系统
- 📢 创建和管理广告模板
- 📸 支持图片 + 文字 + 按钮组合
- 📤 批量发送到多个频道/群组
- ⏰ 定时发送功能
- 📊 完整的发送记录

### 7. 管理员面板
- 👑 待审核订单管理
- 👥 用户列表和会员状态查询
- 📊 收入统计和数据分析
- 🔔 实时通知

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# ========== 必填配置 ==========

# Telegram Bot Token (从 @BotFather 获取)
BOT_TOKEN=your_bot_token_here

# 管理员 User ID (多个用逗号分隔)
ADMIN_USER_IDS=123456789

# VIP 频道 ID (-100 开头)
PRIVATE_CHANNEL_ID=-1001234567890

# TRON 收款地址 (T 开头)
TRON_WALLET_ADDRESS=TYourWalletAddress

# TronScan API Key (从 tronscan.org 获取)
TRONSCAN_API_KEY=your-api-key

# 闲鱼商品链接
XIANYU_PRODUCT_URL=https://your-xianyu-link


# ========== 可选配置 ==========

# 套餐模式 (true=多套餐选择, false=固定价格直接支付)
ENABLE_MULTIPLE_PLANS=false

# 客服链接
CUSTOMER_SERVICE_URL=https://t.me/your_service

# 欢迎图片 (留空则纯文字)
WELCOME_IMAGE=

# 欢迎消息
WELCOME_MESSAGE="🎉 欢迎！立即购买会员享受专属服务"

# 订单超时设置
ORDER_TIMEOUT_MINUTES=30              # USDT订单超时时间（分钟）
XIANYU_ORDER_TIMEOUT_MINUTES=30       # 闲鱼订单超时时间（分钟）
ORDER_CLEANUP_INTERVAL_MINUTES=5      # 订单清理任务运行间隔（分钟）

# 防刷配置
MAX_PENDING_ORDERS_PER_USER=3         # 每个用户最多同时待支付订单数
MIN_ORDER_INTERVAL_SECONDS=60         # 下单最小间隔（秒）
```

### 3. 配置套餐和价格

编辑 `config.py`：

```python
# 单套餐模式配置 (ENABLE_MULTIPLE_PLANS=false 时使用)
DEFAULT_PLAN = {
    'name': '会员',
    'days': 30,
    'price_usdt': 10.0,
    'price_cny': 68.0
}

# 多套餐模式配置 (ENABLE_MULTIPLE_PLANS=true 时使用)
MEMBERSHIP_PLANS = {
    'month': {
        'name': '月度会员',
        'days': 30,
        'price_usdt': 10.0,
        'price_cny': 68.0
    },
    # ... 更多套餐
}
```

### 4. 启动 Bot

```bash
# 直接运行
python bot.py

# 或使用 PM2 (推荐生产环境)
pm2 start ecosystem.config.js
```

---

## 📱 使用指南

### 用户操作流程

#### 单套餐模式 (ENABLE_MULTIPLE_PLANS=false)

```
/start
  ↓
欢迎页面
  ├─ [💎 USDT 支付 - 10 USDT]  → 显示支付二维码 → 自动到账
  └─ [🏪 闲鱼支付 - ¥68]       → 打开闲鱼 → 输入订单号 → 等待审核
```

#### 多套餐模式 (ENABLE_MULTIPLE_PLANS=true)

```
/start
  ↓
欢迎页面
  ├─ [💎 USDT 支付]  → 选择套餐 → 显示支付二维码
  └─ [🏪 闲鱼支付]   → 选择套餐 → 打开闲鱼 → 输入订单号
```

### 管理员操作

| 命令 | 功能 |
|------|------|
| `/admin` | 打开管理员面板 |
| `/pending` | 查看待审核订单 |
| `/promo` | 广告管理面板 |
| `/stats` | 查看统计数据 |

---

## 🛠️ 配置说明

### 获取必要的 ID

#### 1. Bot Token
1. 在 Telegram 中找到 `@BotFather`
2. 发送 `/newbot` 创建新 Bot
3. 复制获得的 Token

#### 2. User ID
1. 在 Telegram 中找到 `@userinfobot`
2. 发送任意消息
3. 复制你的 User ID

#### 3. 频道 ID
1. 创建一个私有频道
2. 将 Bot 添加为频道管理员
3. 转发频道消息给 `@userinfobot`
4. 复制 Channel ID（以 -100 开头）

#### 4. TRON 地址
- 使用支持 TRC20 的钱包（如 TronLink）
- 复制你的 TRON 地址（T 开头）

#### 5. TronScan API Key
1. 访问 https://tronscan.org
2. 注册账号
3. 在 API 页面创建 API Key

---

## 📸 广告系统使用

### 创建广告模板

```
/promo
  ↓
[创建广告模板]
  ↓
输入模板名称 → 输入广告内容 → (可选)发送图片 → 添加按钮
```

### 发送广告

```
[广告管理] → [批量发送] → 选择模板 → 选择目标(用户/频道)
```

### 定时发送

```
[广告管理] → [定时发送] → 选择模板 → 设置时间 → 选择目标
```

---

## 🔧 高级配置

### 套餐模式选择建议

| 场景 | 推荐模式 | 原因 |
|-----|---------|------|
| 只有一个会员套餐 | 单套餐 (false) | 流程最简洁，用户体验最好 |
| 有多个套餐选择 | 多套餐 (true) | 灵活选择，满足不同需求 |
| 频繁调整价格 | 单套餐 (false) | 配置简单，只需修改一处 |

### Ubuntu 24.04 部署

Ubuntu 24.04 需要使用虚拟环境：

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置 PM2 使用虚拟环境
# 编辑 ecosystem.config.js
{
  "interpreter": "/path/to/your/venv/bin/python"
}

# 启动
pm2 start ecosystem.config.js
```

---

## 📊 数据库

Bot 使用 SQLite 数据库，文件名：`payment_bot.db`

**无需手动创建**，Bot 会在首次运行时自动创建所有必要的表。

---

## 🆘 常见问题

### Q: 闲鱼支付能自动登录吗？

A: **不能**。Bot 无法自动帮用户登录闲鱼。用户需要在浏览器中手动登录。如果用户已在浏览器登录过闲鱼，通常会保持登录状态。

### Q: USDT 支付多久到账？

A: 通常 1-5 分钟。Bot 每 15 秒检查一次链上交易。

### Q: 如何修改会员价格？

**单套餐模式**：修改 `config.py` 中的 `DEFAULT_PLAN`

**多套餐模式**：修改 `config.py` 中的 `MEMBERSHIP_PLANS`

### Q: 如何更换欢迎图片？

1. 向 Bot 发送图片
2. 在日志中获取 `file_id`
3. 将 `file_id` 填入 `.env` 的 `WELCOME_IMAGE`
4. 重启 Bot

### Q: 数据库在哪里？

默认在项目根目录：`payment_bot.db`

可在 `.env` 中修改：`DATABASE_PATH=/path/to/your.db`

---

## 📁 文件说明

```
TGBOT_payment/
├── bot.py                 # 主程序
├── config.py              # 配置文件
├── database.py            # 数据库操作
├── tron_payment.py        # TRON 支付处理
├── requirements.txt       # 依赖列表
├── .env                   # 环境变量 (需自己创建)
├── payment_bot.db         # 数据库 (自动生成)
├── ecosystem.config.js    # PM2 配置
├── README.md              # 本文件
├── QUICKSTART.md          # 快速开始详细版
└── PROMO_GUIDE.md         # 广告功能详细指南
```

---

## 🔗 相关链接

- [详细快速开始指南](QUICKSTART.md) - 更详细的部署步骤
- [广告功能完整指南](PROMO_GUIDE.md) - 广告系统的详细使用方法
- [python-telegram-bot 文档](https://python-telegram-bot.org/)
- [TRON 网络文档](https://developers.tron.network/)

---

## 📄 开源协议

MIT License

---

## 💡 技术支持

如有问题，请提 Issue 或查看文档。

**祝您使用愉快！** 🚀
