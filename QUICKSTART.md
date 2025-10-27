# 快速开始指南

本指南将帮助您在 5-10 分钟内完成 Bot 的部署和配置。

---

## 📋 前置要求

- Python 3.8 或更高版本
- Telegram 账号
- TRON 钱包（用于接收 USDT）
- 闲鱼账号（可选）

---

## 🚀 部署步骤

### 步骤 1: 下载代码

```bash
git clone https://github.com/your-repo/TGBOT_payment.git
cd TGBOT_payment
```

### 步骤 2: 安装依赖

**方式 1: 直接安装**（适用于大多数系统）

```bash
pip install -r requirements.txt
```

**方式 2: 使用虚拟环境**（推荐 Ubuntu 24.04）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3: 创建 Bot

1. 在 Telegram 中找到 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示设置 Bot 名称和用户名
4. 复制获得的 **Bot Token**（类似：`123456:ABC-DEF...`）

### 步骤 4: 获取 User ID

1. 在 Telegram 中找到 `@userinfobot`
2. 点击开始或发送任意消息
3. 复制你的 **User ID**（纯数字）

### 步骤 5: 创建私有频道

1. 在 Telegram 中创建一个新频道
2. 设置为**私有频道**
3. 将你的 Bot 添加为频道管理员
4. 转发频道中的任意消息给 `@userinfobot`
5. 复制 **Channel ID**（以 `-100` 开头）

### 步骤 6: 准备 TRON 钱包

1. 使用支持 TRC20 的钱包（如 TronLink、imToken）
2. 复制你的 **TRON 地址**（以 `T` 开头）
3. 确保该地址可以接收 USDT (TRC20)

### 步骤 7: 获取 TronScan API Key

1. 访问 https://tronscan.org
2. 注册/登录账号
3. 进入 "API Keys" 页面
4. 创建新的 API Key
5. 复制 **API Key**

### 步骤 8: 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# ========== 必填配置 ==========

# Bot Token (从 @BotFather 获取)
BOT_TOKEN=你的Bot Token

# 管理员 User ID (多个用逗号分隔)
ADMIN_USER_IDS=你的User ID

# VIP 频道 ID (从 @userinfobot 获取)
PRIVATE_CHANNEL_ID=-1001234567890

# TRON 收款地址
TRON_WALLET_ADDRESS=你的TRON地址

# TronScan API Key
TRONSCAN_API_KEY=你的API Key

# 闲鱼商品链接 (发布一个商品后获取分享链接)
XIANYU_PRODUCT_URL=https://你的闲鱼商品链接


# ========== 可选配置 ==========

# 套餐模式 (true=多套餐, false=单套餐直接支付)
ENABLE_MULTIPLE_PLANS=false

# 客服链接
CUSTOMER_SERVICE_URL=https://t.me/your_service

# 欢迎图片 (留空则不显示图片)
WELCOME_IMAGE=

# 欢迎消息
WELCOME_MESSAGE="🎉 欢迎来到我们的服务！\n\n✨ 立即购买会员享受专属内容\n💎 快速开通，秒级到账\n\n👇 请选择支付方式"
```

### 步骤 9: 配置套餐和价格

编辑 `config.py` 文件：

#### 如果使用单套餐模式 (ENABLE_MULTIPLE_PLANS=false)

```python
# 修改这里的配置
DEFAULT_PLAN = {
    'name': '会员',           # 套餐名称
    'days': 30,               # 会员天数
    'price_usdt': 10.0,       # USDT 价格
    'price_cny': 68.0         # 人民币价格
}
```

#### 如果使用多套餐模式 (ENABLE_MULTIPLE_PLANS=true)

```python
# 修改这里的配置
MEMBERSHIP_PLANS = {
    'month': {
        'name': '月度会员',
        'days': 30,
        'price_usdt': 10.0,
        'price_cny': 68.0
    },
    'quarter': {
        'name': '季度会员',
        'days': 90,
        'price_usdt': 25.0,
        'price_cny': 178.0
    },
    'year': {
        'name': '年度会员',
        'days': 365,
        'price_usdt': 88.0,
        'price_cny': 588.0
    }
}
```

### 步骤 10: 启动 Bot

#### 开发/测试环境

```bash
python bot.py
```

看到以下输出表示成功：

```
Bot started successfully!
```

#### 生产环境 (使用 PM2)

**安装 PM2**：

```bash
npm install -g pm2
```

**配置 PM2**：

如果使用了虚拟环境，需要修改 `ecosystem.config.js`：

```javascript
module.exports = {
  apps: [{
    name: "payment-bot",
    script: "bot.py",
    interpreter: "/path/to/your/venv/bin/python",  // 修改为你的虚拟环境路径
    cwd: "/root/TGBOT_payment",
    watch: false,
    env: {
      PYTHONPATH: "/root/TGBOT_payment"
    }
  }]
}
```

**启动**：

```bash
pm2 start ecosystem.config.js
```

**常用命令**：

```bash
# 查看状态
pm2 status

# 查看日志
pm2 logs payment-bot

# 重启
pm2 restart payment-bot

# 停止
pm2 stop payment-bot

# 开机自启
pm2 startup
pm2 save
```

---

## ✅ 测试

### 1. 测试 Bot 启动

向你的 Bot 发送 `/start`，应该看到欢迎消息和按钮。

### 2. 测试 USDT 支付

1. 点击 "💎 USDT 支付" 按钮
2. 如果是单套餐模式，会直接显示支付二维码
3. 如果是多套餐模式，先选择套餐，再显示二维码

### 3. 测试闲鱼支付

1. 点击 "🏪 闲鱼支付" 按钮
2. 查看是否显示购买指南
3. 点击 "打开闲鱼商品" 测试跳转

### 4. 测试管理员功能

发送 `/admin` 命令，应该看到管理员面板。

---

## 🎨 自定义配置

### 修改欢迎图片

#### 方法 1: 使用图片 URL

```env
WELCOME_IMAGE=https://your-domain.com/welcome.jpg
```

#### 方法 2: 使用 Telegram file_id（推荐）

1. 向 Bot 发送一张图片
2. 在 Bot 日志中查找 `file_id`（或使用广告功能上传图片时会显示）
3. 复制 file_id 到配置：

```env
WELCOME_IMAGE=AgACAgIAAxkDAAIBY2Z...
```

### 修改欢迎文案

编辑 `.env` 文件：

```env
WELCOME_MESSAGE="🎉 欢迎来到 [你的品牌]！\n\n✨ 专属内容等你探索\n💎 立即加入会员\n\n👇 选择支付方式开始"
```

**提示**：使用 `\n` 表示换行

### 切换套餐模式

在 `.env` 中修改：

```env
# 单套餐模式（推荐只有一个套餐时使用）
ENABLE_MULTIPLE_PLANS=false

# 多套餐模式（有多个套餐选择时使用）
ENABLE_MULTIPLE_PLANS=true
```

**修改后需要重启 Bot**：

```bash
pm2 restart payment-bot
```

---

## 🔧 故障排查

### 问题 1: ModuleNotFoundError

**错误信息**：

```
ModuleNotFoundError: No module named 'telegram'
```

**解决方法**：

```bash
pip install -r requirements.txt
```

如果使用虚拟环境，确保已激活：

```bash
source venv/bin/activate  # Linux/Mac
```

### 问题 2: Bot Token 无效

**错误信息**：

```
telegram.error.InvalidToken
```

**解决方法**：

1. 检查 `.env` 中的 `BOT_TOKEN` 是否正确
2. 确保 Token 没有多余的空格或换行
3. 重新从 @BotFather 获取 Token

### 问题 3: 无法连接 TRON 网络

**错误信息**：

```
Failed to connect to TRON network
```

**解决方法**：

1. 检查网络连接
2. 验证 `TRONSCAN_API_KEY` 是否正确
3. 检查 TRON 地址格式（必须以 `T` 开头）

### 问题 4: Ubuntu 24.04 安装依赖失败

**错误信息**：

```
error: externally-managed-environment
```

**解决方法**：

使用虚拟环境（见步骤 2 的方式 2）

### 问题 5: Bot 无法邀请用户到频道

**可能原因**：

1. Bot 不是频道管理员
2. 频道不是私有频道
3. Channel ID 错误

**解决方法**：

1. 确保 Bot 是频道管理员
2. 确保频道设置为私有
3. 重新获取 Channel ID

---

## 📊 数据备份

定期备份数据库文件：

```bash
cp payment_bot.db payment_bot.db.backup
```

或设置自动备份：

```bash
# 添加到 crontab
0 2 * * * cp /path/to/payment_bot.db /path/to/backup/payment_bot_$(date +\%Y\%m\%d).db
```

---

## 🔄 更新 Bot

```bash
# 停止 Bot
pm2 stop payment-bot

# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt

# 重启 Bot
pm2 restart payment-bot
```

---

## 📚 下一步

- [完整功能说明](README.md)
- [套餐模式配置指南](CONFIG_GUIDE.md) - 单套餐 vs 多套餐配置
- [广告功能详细指南](PROMO_GUIDE.md)

---

## 💡 提示

1. **安全性**：
   - 不要泄露 `.env` 文件
   - 定期更换 API Key
   - 定期备份数据库

2. **性能优化**：
   - 生产环境使用 PM2
   - 定期清理过期订单
   - 监控日志文件大小

3. **用户体验**：
   - 单套餐时使用 `ENABLE_MULTIPLE_PLANS=false`
   - 定期更新欢迎文案
   - 及时审核闲鱼订单

---

**祝您部署成功！** 🎉
