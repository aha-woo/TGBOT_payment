"""
配置文件 - 请根据实际情况修改
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ========== Telegram Bot 配置 ==========
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_USER_IDS = [int(x.strip()) for x in os.getenv('ADMIN_USER_IDS', '').split(',') if x.strip()]  # 管理员 Telegram User ID 列表
PRIVATE_CHANNEL_ID = os.getenv('PRIVATE_CHANNEL_ID', '-1001234567890')  # 私有频道 ID（以 -100 开头）

# ========== TRON 支付配置 ==========
TRON_WALLET_ADDRESS = os.getenv('TRON_WALLET_ADDRESS', 'TYourWalletAddress')  # 你的 TRON 收款地址
TRONSCAN_API_KEY = os.getenv('TRONSCAN_API_KEY', 'your-tronscan-api-key')  # TronScan API Key

# ========== 闲鱼配置 ==========
XIANYU_PRODUCT_URL = os.getenv('XIANYU_PRODUCT_URL', 'https://your-xianyu-product-link')  # 闲鱼商品链接

# ========== 会员配置 ==========
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

# ========== 系统配置 ==========
DATABASE_PATH = os.getenv('DATABASE_PATH', 'payment_bot.db')  # 数据库路径
ORDER_TIMEOUT_MINUTES = int(os.getenv('ORDER_TIMEOUT_MINUTES', '30'))  # 订单超时时间（分钟）
POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', '15'))  # TRON 轮询间隔（秒）

# ========== 日志配置 ==========
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

# ========== 防刷配置 ==========
MAX_PENDING_ORDERS_PER_USER = int(os.getenv('MAX_PENDING_ORDERS_PER_USER', '3'))  # 每个用户最多同时 3 个待支付订单
MIN_ORDER_INTERVAL_SECONDS = int(os.getenv('MIN_ORDER_INTERVAL_SECONDS', '60'))  # 下单最小间隔（秒）

# ========== 频道配置 ==========
WELCOME_MESSAGE = """
🎉 欢迎加入我们的专属频道！

您的会员已激活，享有以下权益：
✨ 专属内容访问
✨ 优先客服支持
✨ 会员专属福利

到期时间：{expiry_date}

感谢您的支持！
"""

# ========== 消息模板 ==========
HELP_MESSAGE = """
🤖 欢迎使用支付 Bot

📌 可用命令：
/start - 开始使用
/buy - 购买会员
/orders - 查看我的订单
/status - 查看会员状态
/help - 帮助信息

💳 支持的支付方式：
1️⃣ USDT (TRC20) - 自动到账
2️⃣ 闲鱼支付 - 人工审核

有问题请联系管理员 @admin
"""

ADMIN_HELP_MESSAGE = """
👑 管理员命令：

/admin - 管理员面板
/pending - 待审核订单
/users - 用户列表
/stats - 统计数据
/broadcast - 广播消息

订单管理：
- 点击订单可查看详情和操作
"""


