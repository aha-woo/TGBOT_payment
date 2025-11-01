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
XIANYU_PRODUCT_URL = os.getenv('XIANYU_PRODUCT_URL', 'https://m.tb.cn/h.SOQ16rD?tk=77IJf4SF7On CZ321')  # 闲鱼商品链接

# ========== 客服配置 ==========
CUSTOMER_SERVICE_URL = os.getenv('CUSTOMER_SERVICE_URL', 'https://t.me/youryhc')  # 客服链接（可以是 Telegram 个人/群组链接）

# ========== 欢迎页面配置 ==========
# 欢迎图片 - 可以是图片 URL 或 Telegram file_id（留空则不显示图片）
WELCOME_IMAGE = os.getenv('WELCOME_IMAGE', '')

# 欢迎消息 - 在下方"频道配置"部分统一配置（第82行）

# ========== 会员配置 ==========

# 是否启用多套餐模式（True=显示套餐选择, False=固定价格直接支付）
ENABLE_MULTIPLE_PLANS = os.getenv('ENABLE_MULTIPLE_PLANS', 'true').lower() == 'true'

# 默认套餐配置（当 ENABLE_MULTIPLE_PLANS=False 时使用）
DEFAULT_PLAN = {
    'name': '会员',
    'days': 30,
    'price_usdt': 10.0,
    'price_cny': 68.0
}

# 多套餐配置（当 ENABLE_MULTIPLE_PLANS=True 时使用）
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
ORDER_TIMEOUT_MINUTES = int(os.getenv('ORDER_TIMEOUT_MINUTES', '30'))  # USDT订单超时时间（分钟）
XIANYU_ORDER_TIMEOUT_MINUTES = int(os.getenv('XIANYU_ORDER_TIMEOUT_MINUTES', '30'))  # 闲鱼订单超时时间（分钟）
POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', '15'))  # TRON 轮询间隔（秒）
ORDER_CLEANUP_INTERVAL_MINUTES = int(os.getenv('ORDER_CLEANUP_INTERVAL_MINUTES', '5'))  # 订单清理任务运行间隔（分钟）

# ========== 日志配置 ==========
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

# ========== 防刷配置 ==========
MAX_PENDING_ORDERS_PER_USER = int(os.getenv('MAX_PENDING_ORDERS_PER_USER', '3'))  # 每个用户最多同时 3 个待支付订单
MIN_ORDER_INTERVAL_SECONDS = int(os.getenv('MIN_ORDER_INTERVAL_SECONDS', '60'))  # 下单最小间隔（秒）

# ========== 欢迎消息配置（在这里统一修改欢迎文案）==========
WELCOME_MESSAGE = """🎉 商品名：白嫩大奶美女俱乐部内部-永久 🎊

💰 限时特惠价格
🔥 现价：98元（永久）
❌ 原价：198元、⚡️ 立省100元！即将恢复原价！

✅ 包含群数：1个永久群、更新频率：每日更新 资源、数量：已更新几千部
【白嫩大奶美女俱乐部内部群】专注做好白嫩大奶美女内容
❶ 主打内容：
   • 约炮、PUA、情侣自拍、偷拍
   • 高颜值学生、良家、白嫩大奶肉体
   • 反差合集资源（非零散内容）
❷ 涵盖类型：
   • 学生、情侣、人妻、网红
   • 福利姬、大学生原创、反差女友
   • 飞机上未流出的纯极品资源
❸ 资源优势：
   ⚡️ 可保存、可下载、可收藏
   ⚡️ 持续更新中

💳  支持 USDT 支付（自动发送邀请链接）
💳  支持 闲鱼链接支付（人工审核后发送邀请链接）
⚠️ 具体支付方式请在支付页面仔细阅读
"""

# ========== 消息模板 ==========
HELP_MESSAGE = """
🤖 使用指南

✨ 傻瓜式操作，全程按钮！

📱 如何使用：
1️⃣ 点击「立即购买会员」选择套餐
2️⃣ 选择支付方式（USDT 或闲鱼）
3️⃣ 完成支付
4️⃣ 自动获得频道邀请链接

💳 支持的支付方式：
• USDT (TRC20) - 自动到账，秒级确认
• 闲鱼支付 - 人工审核，24小时内处理

📋 查看订单：
点击「我的订单」查看支付状态

👤 会员状态：
点击「会员状态」查看到期时间

💡 提示：所有操作都通过按钮完成，无需输入命令！

有问题请联系管理员
"""

ADMIN_HELP_MESSAGE = """
👑 管理员命令：

/admin - 管理员面板
/pending - 待审核订单
/promo - 广告管理
/users - 用户列表
/stats - 统计数据
/broadcast - 广播消息

订单管理：
- 点击订单可查看详情和操作

广告管理：
- 创建和管理广告模板
- 设置定时发送任务
- 立即发送广告
- 查看发送记录
"""


