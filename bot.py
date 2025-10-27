"""
Telegram Bot 主程序
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
from telegram.error import TelegramError
from datetime import datetime, timedelta
import time

from config import *
from database import Database
from tron_payment import TronPayment

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化数据库
db = Database(DATABASE_PATH)

# 初始化 TRON 支付
tron_payment = None
try:
    tron_payment = TronPayment(
        wallet_address=TRON_WALLET_ADDRESS,
        tronscan_api_key=TRONSCAN_API_KEY,
        db_path='tron_orders.db',
        poll_interval=POLL_INTERVAL_SECONDS,
        default_timeout=ORDER_TIMEOUT_MINUTES
    )
    logger.info("TRON Payment initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize TRON Payment: {e}")

# 用户状态管理（用于多步骤对话）
user_states = {}


# ========== 工具函数 ==========

def is_admin(user_id: int) -> bool:
    """检查是否是管理员"""
    return user_id in ADMIN_USER_IDS


async def invite_user_to_channel(app: Application, user_id: int, order_id: str) -> bool:
    """邀请用户到私有频道"""
    try:
        # 创建邀请链接（需要 Bot 是频道管理员）
        invite_link = await app.bot.create_chat_invite_link(
            chat_id=PRIVATE_CHANNEL_ID,
            member_limit=1,
            expire_date=int(time.time()) + 3600  # 1小时过期
        )
        
        # 发送邀请链接给用户
        await app.bot.send_message(
            chat_id=user_id,
            text=f"🎉 您的订单已确认！\n\n请点击下方链接加入专属频道：\n{invite_link.invite_link}\n\n⚠️ 此链接1小时内有效"
        )
        
        db.add_channel_invite(user_id, order_id, 'success')
        logger.info(f"Invited user {user_id} to channel for order {order_id}")
        return True
        
    except TelegramError as e:
        logger.error(f"Failed to invite user {user_id}: {e}")
        db.add_channel_invite(user_id, order_id, f'failed: {e}')
        
        # 通知管理员手动处理
        for admin_id in ADMIN_USER_IDS:
            try:
                await app.bot.send_message(
                    chat_id=admin_id,
                    text=f"⚠️ 无法自动邀请用户\n\n用户ID: {user_id}\n订单: {order_id}\n错误: {e}\n\n请手动邀请用户加入频道"
                )
            except:
                pass
        
        return False


def format_order_info(order: dict) -> str:
    """格式化订单信息"""
    status_emoji = {
        'pending': '⏳',
        'paid': '✅',
        'cancelled': '❌',
        'expired': '⏰'
    }
    
    method_name = {
        'tron': 'TRON USDT',
        'xianyu': '闲鱼支付'
    }
    
    text = f"""
{status_emoji.get(order['status'], '❓')} 订单详情

订单号: `{order['order_id']}`
套餐: {MEMBERSHIP_PLANS.get(order['plan_type'], {}).get('name', order['plan_type'])}
金额: {order['amount']} {order['currency']}
支付方式: {method_name.get(order['payment_method'], order['payment_method'])}
状态: {order['status']}
创建时间: {order['created_at']}
"""
    
    if order['paid_at']:
        text += f"支付时间: {order['paid_at']}\n"
    
    if order['payment_method'] == 'tron' and order['tron_tx_hash']:
        text += f"交易哈希: `{order['tron_tx_hash']}`\n"
    
    if order['payment_method'] == 'xianyu' and order['xianyu_order_number']:
        text += f"闲鱼订单号: {order['xianyu_order_number']}\n"
    
    return text


# ========== 用户命令 ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始命令"""
    user = update.effective_user
    db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    keyboard = [
        [InlineKeyboardButton("💳 购买会员", callback_data="buy_membership")],
        [InlineKeyboardButton("📋 我的订单", callback_data="my_orders")],
        [InlineKeyboardButton("👤 会员状态", callback_data="my_status")],
        [InlineKeyboardButton("❓ 帮助", callback_data="help")]
    ]
    
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("👑 管理员面板", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 你好 {user.first_name}！\n\n"
        "欢迎使用我们的会员服务系统\n\n"
        "请选择您需要的功能：",
        reply_markup=reply_markup
    )


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """购买会员"""
    await show_membership_plans(update, context)


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看订单"""
    user_id = update.effective_user.id
    orders = db.get_user_orders(user_id, limit=10)
    
    if not orders:
        await update.message.reply_text("您还没有任何订单")
        return
    
    text = "📋 您的订单列表：\n\n"
    keyboard = []
    
    for order in orders:
        status_emoji = {'pending': '⏳', 'paid': '✅', 'cancelled': '❌', 'expired': '⏰'}
        text += f"{status_emoji.get(order['status'], '❓')} {order['order_id'][:20]}... - {order['amount']} {order['currency']} - {order['status']}\n"
        keyboard.append([InlineKeyboardButton(
            f"查看 {order['order_id'][:15]}...",
            callback_data=f"view_order_{order['order_id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看会员状态"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("未找到用户信息")
        return
    
    if user['is_member']:
        member_until = datetime.fromisoformat(user['member_until'])
        days_left = (member_until - datetime.now()).days
        
        text = f"""
✨ 会员信息

状态: ✅ 已激活
到期时间: {member_until.strftime('%Y-%m-%d %H:%M')}
剩余天数: {days_left} 天

总消费: {user['total_spent_usdt']} USDT / {user['total_spent_cny']} CNY
加入时间: {user['member_since']}
"""
    else:
        text = """
❌ 您还不是会员

点击下方按钮购买会员：
"""
    
    keyboard = [[InlineKeyboardButton("💳 购买会员", callback_data="buy_membership")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """帮助信息"""
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        await update.message.reply_text(HELP_MESSAGE + "\n\n" + ADMIN_HELP_MESSAGE)
    else:
        await update.message.reply_text(HELP_MESSAGE)


# ========== 管理员命令 ==========

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员面板"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ 您没有权限")
        return
    
    stats = db.get_statistics()
    
    text = f"""
👑 管理员面板

📊 系统统计：
总用户数: {stats['total_users']}
活跃会员: {stats['active_members']}
总订单数: {stats['total_orders']}
已支付: {stats['paid_orders']}
待处理: {stats['pending_orders']}

💰 收入统计：
USDT: {stats['total_usdt']:.2f}
人民币: {stats['total_cny']:.2f}

📅 今日数据：
新订单: {stats['today_orders']}
已支付: {stats['today_paid']}
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 待审核订单", callback_data="admin_pending_orders")],
        [InlineKeyboardButton("👥 用户列表", callback_data="admin_users")],
        [InlineKeyboardButton("📊 详细统计", callback_data="admin_stats")],
        [InlineKeyboardButton("🔄 刷新", callback_data="admin_panel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """待审核订单"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ 您没有权限")
        return
    
    await show_pending_orders(update, context)


# ========== 回调处理 ==========

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理按钮回调"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    # 购买会员流程
    if data == "buy_membership":
        await show_membership_plans(update, context, query=query)
    
    elif data.startswith("plan_"):
        plan_type = data.split("_")[1]
        await show_payment_methods(update, context, plan_type, query=query)
    
    elif data.startswith("pay_"):
        parts = data.split("_")
        method = parts[1]
        plan_type = parts[2]
        await process_payment_selection(update, context, method, plan_type, query=query)
    
    # 订单查看
    elif data == "my_orders":
        orders = db.get_user_orders(user_id, limit=10)
        if not orders:
            await query.edit_message_text("您还没有任何订单")
            return
        
        text = "📋 您的订单列表：\n\n"
        keyboard = []
        
        for order in orders:
            status_emoji = {'pending': '⏳', 'paid': '✅', 'cancelled': '❌', 'expired': '⏰'}
            text += f"{status_emoji.get(order['status'], '❓')} {order['order_id'][:30]}... - {order['status']}\n"
            keyboard.append([InlineKeyboardButton(
                f"查看详情",
                callback_data=f"view_order_{order['order_id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("« 返回", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif data.startswith("view_order_"):
        order_id = data.replace("view_order_", "")
        order = db.get_order(order_id)
        
        if not order:
            await query.edit_message_text("订单不存在")
            return
        
        text = format_order_info(order)
        keyboard = [[InlineKeyboardButton("« 返回订单列表", callback_data="my_orders")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # 会员状态
    elif data == "my_status":
        user = db.get_user(user_id)
        
        if user['is_member']:
            member_until = datetime.fromisoformat(user['member_until'])
            days_left = (member_until - datetime.now()).days
            
            text = f"""
✨ 会员信息

状态: ✅ 已激活
到期时间: {member_until.strftime('%Y-%m-%d %H:%M')}
剩余天数: {days_left} 天

总消费: {user['total_spent_usdt']} USDT / {user['total_spent_cny']} CNY
"""
        else:
            text = "❌ 您还不是会员"
        
        keyboard = [
            [InlineKeyboardButton("💳 购买/续费", callback_data="buy_membership")],
            [InlineKeyboardButton("« 返回", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    # 帮助
    elif data == "help":
        keyboard = [[InlineKeyboardButton("« 返回", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(HELP_MESSAGE, reply_markup=reply_markup)
    
    # 管理员功能
    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        stats = db.get_statistics()
        
        text = f"""
👑 管理员面板

📊 系统统计：
总用户数: {stats['total_users']}
活跃会员: {stats['active_members']}
总订单数: {stats['total_orders']}
已支付: {stats['paid_orders']}
待处理: {stats['pending_orders']}

💰 收入统计：
USDT: {stats['total_usdt']:.2f}
人民币: {stats['total_cny']:.2f}
"""
        
        keyboard = [
            [InlineKeyboardButton("📋 待审核订单", callback_data="admin_pending_orders")],
            [InlineKeyboardButton("👥 用户列表", callback_data="admin_users")],
            [InlineKeyboardButton("🔄 刷新", callback_data="admin_panel")],
            [InlineKeyboardButton("« 返回", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif data == "admin_pending_orders":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        await show_pending_orders(update, context, query=query)
    
    elif data.startswith("admin_approve_"):
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        order_id = data.replace("admin_approve_", "")
        await approve_order(update, context, order_id, query=query)
    
    elif data.startswith("admin_reject_"):
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        order_id = data.replace("admin_reject_", "")
        await reject_order(update, context, order_id, query=query)
    
    elif data == "admin_users":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        users = db.get_all_users(limit=20)
        text = f"👥 用户列表 (最近20个)：\n\n"
        
        for user in users:
            member_emoji = "✅" if user['is_member'] else "❌"
            text += f"{member_emoji} {user['user_id']} - @{user['username'] or 'N/A'} - {user['first_name']}\n"
        
        keyboard = [[InlineKeyboardButton("« 返回", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    # 返回主菜单
    elif data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton("💳 购买会员", callback_data="buy_membership")],
            [InlineKeyboardButton("📋 我的订单", callback_data="my_orders")],
            [InlineKeyboardButton("👤 会员状态", callback_data="my_status")],
            [InlineKeyboardButton("❓ 帮助", callback_data="help")]
        ]
        
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("👑 管理员面板", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("请选择您需要的功能：", reply_markup=reply_markup)


# ========== 业务逻辑函数 ==========

async def show_membership_plans(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """显示会员套餐"""
    text = "💎 选择会员套餐：\n\n"
    keyboard = []
    
    for plan_key, plan_info in MEMBERSHIP_PLANS.items():
        text += f"🔹 {plan_info['name']}\n"
        text += f"   时长: {plan_info['days']} 天\n"
        text += f"   USDT: {plan_info['price_usdt']} | 人民币: ¥{plan_info['price_cny']}\n\n"
        
        keyboard.append([InlineKeyboardButton(
            f"{plan_info['name']} - {plan_info['days']}天",
            callback_data=f"plan_{plan_key}"
        )])
    
    keyboard.append([InlineKeyboardButton("« 返回", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_payment_methods(update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type: str, query=None):
    """显示支付方式"""
    plan_info = MEMBERSHIP_PLANS.get(plan_type)
    
    if not plan_info:
        await query.edit_message_text("套餐不存在")
        return
    
    text = f"""
您选择的套餐：{plan_info['name']}

请选择支付方式：
"""
    
    keyboard = [
        [InlineKeyboardButton(
            f"💎 USDT (TRC20) - {plan_info['price_usdt']} USDT",
            callback_data=f"pay_tron_{plan_type}"
        )],
        [InlineKeyboardButton(
            f"🛒 闲鱼支付 - ¥{plan_info['price_cny']}",
            callback_data=f"pay_xianyu_{plan_type}"
        )],
        [InlineKeyboardButton("« 返回套餐选择", callback_data="buy_membership")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


async def process_payment_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   method: str, plan_type: str, query=None):
    """处理支付方式选择"""
    user_id = update.effective_user.id
    plan_info = MEMBERSHIP_PLANS.get(plan_type)
    
    if not plan_info:
        await query.edit_message_text("套餐不存在")
        return
    
    # 检查防刷限制
    pending_count = db.count_user_pending_orders(user_id)
    if pending_count >= MAX_PENDING_ORDERS_PER_USER:
        await query.answer(f"您有 {pending_count} 个待支付订单，请先完成支付", show_alert=True)
        return
    
    last_order_time = db.get_user_last_order_time(user_id)
    if last_order_time:
        time_since_last = (datetime.now() - last_order_time).total_seconds()
        if time_since_last < MIN_ORDER_INTERVAL_SECONDS:
            wait_time = int(MIN_ORDER_INTERVAL_SECONDS - time_since_last)
            await query.answer(f"请等待 {wait_time} 秒后再下单", show_alert=True)
            return
    
    if method == 'tron':
        await process_tron_payment(update, context, plan_type, plan_info, query)
    elif method == 'xianyu':
        await process_xianyu_payment(update, context, plan_type, plan_info, query)


async def process_tron_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               plan_type: str, plan_info: dict, query):
    """处理 TRON 支付"""
    user_id = update.effective_user.id
    user = update.effective_user
    
    if not tron_payment:
        await query.edit_message_text("❌ TRON 支付暂时不可用，请联系管理员")
        return
    
    try:
        # 创建 TRON 订单
        tron_order = tron_payment.create_order(
            user_id=str(user_id),
            amount_usdt=plan_info['price_usdt'],
            timeout_minutes=ORDER_TIMEOUT_MINUTES,
            notes=f"{plan_info['name']} - @{user.username}"
        )
        
        # 保存到数据库
        order_id = f"TG_{user_id}_{int(time.time())}"
        db.create_order({
            'order_id': order_id,
            'user_id': user_id,
            'payment_method': 'tron',
            'plan_type': plan_type,
            'amount': plan_info['price_usdt'],
            'currency': 'USDT',
            'status': 'pending',
            'membership_days': plan_info['days'],
            'tron_order_id': tron_order['order_id']
        })
        
        # 发送支付信息
        text = f"""
💳 USDT (TRC20) 支付

套餐: {plan_info['name']}
金额: {plan_info['price_usdt']} USDT
订单号: `{order_id}`

🔹 收款地址:
`{tron_order['wallet_address']}`

🔹 合约地址:
`{tron_order['usdt_contract']}`

⏰ 请在 {ORDER_TIMEOUT_MINUTES} 分钟内完成支付

💡 支付后系统会自动确认（约1-3分钟）
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ 我已支付", callback_data=f"check_payment_{order_id}")],
            [InlineKeyboardButton("📋 查看订单", callback_data=f"view_order_{order_id}")],
            [InlineKeyboardButton("« 返回", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 发送二维码
        await context.bot.send_photo(
            chat_id=user_id,
            photo=tron_order['qr_code'],
            caption=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        await query.edit_message_text("✅ 订单已创建，请查看上方支付信息")
        
        db.add_log('order_created', user_id, order_id, f'TRON order created: {plan_type}')
        
    except Exception as e:
        logger.error(f"Failed to create TRON order: {e}")
        await query.edit_message_text(f"❌ 创建订单失败: {e}")


async def process_xianyu_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                plan_type: str, plan_info: dict, query):
    """处理闲鱼支付"""
    user_id = update.effective_user.id
    user = update.effective_user
    
    # 创建订单
    order_id = f"XY_{user_id}_{int(time.time())}"
    db.create_order({
        'order_id': order_id,
        'user_id': user_id,
        'payment_method': 'xianyu',
        'plan_type': plan_type,
        'amount': plan_info['price_cny'],
        'currency': 'CNY',
        'status': 'pending',
        'membership_days': plan_info['days']
    })
    
    # 保存用户状态，等待订单号
    user_states[user_id] = {
        'action': 'waiting_xianyu_order',
        'order_id': order_id
    }
    
    text = f"""
🛒 闲鱼支付

套餐: {plan_info['name']}
金额: ¥{plan_info['price_cny']}
订单号: `{order_id}`

📱 支付步骤：
1. 点击下方按钮跳转到闲鱼商品页
2. 在闲鱼完成支付
3. 复制闲鱼订单编号
4. 回到这里发送订单编号给我

示例：20231024123456789

⚠️ 请在完成支付后24小时内提交订单编号
"""
    
    keyboard = [
        [InlineKeyboardButton("🛒 前往闲鱼支付", url=XIANYU_PRODUCT_URL)],
        [InlineKeyboardButton("❌ 取消订单", callback_data=f"cancel_order_{order_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # 提示输入订单号
    await context.bot.send_message(
        chat_id=user_id,
        text="📝 完成支付后，请直接发送闲鱼订单编号给我"
    )
    
    db.add_log('order_created', user_id, order_id, f'Xianyu order created: {plan_type}')


async def show_pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """显示待审核订单"""
    orders = db.get_pending_xianyu_orders()
    
    if not orders:
        text = "✅ 暂无待审核订单"
        keyboard = [[InlineKeyboardButton("« 返回", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        return
    
    for order in orders[:5]:  # 每次显示5个
        user = db.get_user(order['user_id'])
        plan_info = MEMBERSHIP_PLANS.get(order['plan_type'], {})
        
        text = f"""
📋 待审核订单

订单号: `{order['order_id']}`
用户: @{user['username'] or 'N/A'} (ID: {order['user_id']})
套餐: {plan_info.get('name', 'N/A')}
金额: ¥{order['amount']}
闲鱼订单号: {order['xianyu_order_number'] or '未提交'}
创建时间: {order['created_at']}
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ 通过", callback_data=f"admin_approve_{order['order_id']}")],
            [InlineKeyboardButton("❌ 拒绝", callback_data=f"admin_reject_{order['order_id']}")],
            [InlineKeyboardButton("« 返回", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str, query):
    """批准订单"""
    order = db.get_order(order_id)
    
    if not order:
        await query.answer("订单不存在", show_alert=True)
        return
    
    if order['status'] != 'pending':
        await query.answer("订单状态不正确", show_alert=True)
        return
    
    # 更新订单状态
    db.update_order_status(order_id, 'paid')
    
    # 更新用户会员状态
    db.update_user_membership(order['user_id'], order['membership_days'], order_id)
    
    # 更新用户消费统计
    user = db.get_user(order['user_id'])
    if order['currency'] == 'USDT':
        new_usdt = (user['total_spent_usdt'] or 0) + order['amount']
        db.get_connection().execute(
            "UPDATE users SET total_spent_usdt=? WHERE user_id=?",
            (new_usdt, order['user_id'])
        )
    else:
        new_cny = (user['total_spent_cny'] or 0) + order['amount']
        db.get_connection().execute(
            "UPDATE users SET total_spent_cny=? WHERE user_id=?",
            (new_cny, order['user_id'])
        )
    
    # 邀请用户加入频道
    await invite_user_to_channel(context.application, order['user_id'], order_id)
    
    # 通知用户
    plan_info = MEMBERSHIP_PLANS.get(order['plan_type'], {})
    await context.bot.send_message(
        chat_id=order['user_id'],
        text=f"✅ 您的订单已确认！\n\n套餐: {plan_info.get('name', 'N/A')}\n订单号: {order_id}\n\n会员已激活，请查看邀请链接"
    )
    
    await query.answer("✅ 订单已批准", show_alert=True)
    await query.edit_message_text(f"✅ 订单 {order_id} 已批准并激活会员")
    
    db.add_log('order_approved', order['user_id'], order_id, 'Order approved by admin')


async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str, query):
    """拒绝订单"""
    order = db.get_order(order_id)
    
    if not order:
        await query.answer("订单不存在", show_alert=True)
        return
    
    # 更新订单状态
    db.update_order_status(order_id, 'cancelled', admin_notes='Rejected by admin')
    
    # 通知用户
    await context.bot.send_message(
        chat_id=order['user_id'],
        text=f"❌ 您的订单已被拒绝\n\n订单号: {order_id}\n\n如有疑问，请联系管理员"
    )
    
    await query.answer("❌ 订单已拒绝", show_alert=True)
    await query.edit_message_text(f"❌ 订单 {order_id} 已拒绝")
    
    db.add_log('order_rejected', order['user_id'], order_id, 'Order rejected by admin')


# ========== 消息处理 ==========

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通消息"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # 检查用户状态
    if user_id in user_states:
        state = user_states[user_id]
        
        if state['action'] == 'waiting_xianyu_order':
            # 处理闲鱼订单号
            order_id = state['order_id']
            xianyu_order = text.strip()
            
            # 更新订单
            db.update_order_status(order_id, 'pending', xianyu_order_number=xianyu_order)
            
            await update.message.reply_text(
                f"✅ 已收到您的订单编号：{xianyu_order}\n\n"
                f"订单号：{order_id}\n\n"
                "管理员将在24小时内审核，请耐心等待"
            )
            
            # 通知管理员
            for admin_id in ADMIN_USER_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🔔 新的闲鱼订单待审核\n\n"
                             f"订单号: {order_id}\n"
                             f"用户: {user_id}\n"
                             f"闲鱼订单号: {xianyu_order}\n\n"
                             f"使用 /pending 查看详情"
                    )
                except:
                    pass
            
            # 清除状态
            del user_states[user_id]
            
            db.add_log('xianyu_order_submitted', user_id, order_id, f'Xianyu order number: {xianyu_order}')
            return
    
    # 默认回复
    await update.message.reply_text(
        "请使用菜单或命令与我交互\n\n"
        "输入 /help 查看帮助"
    )


# ========== TRON 支付回调 ==========

def setup_tron_callbacks():
    """设置 TRON 支付回调"""
    if not tron_payment:
        return
    
    def on_payment_received(tron_order_id, order_info):
        """TRON 支付成功回调"""
        logger.info(f"TRON payment received: {tron_order_id}")
        
        # 查找对应的订单
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM orders WHERE tron_order_id=? AND status='pending'",
            (tron_order_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            logger.warning(f"No order found for TRON order {tron_order_id}")
            return
        
        columns = ['order_id', 'user_id', 'payment_method', 'plan_type', 'amount', 
                  'currency', 'status', 'created_at', 'paid_at', 'expired_at', 
                  'cancelled_at', 'tron_tx_hash', 'tron_order_id', 'xianyu_order_number',
                  'xianyu_screenshot', 'membership_days', 'admin_notes', 'user_notes']
        order = dict(zip(columns, row))
        
        # 更新订单状态
        db.update_order_status(
            order['order_id'], 
            'paid', 
            tron_tx_hash=order_info.get('tx_hash')
        )
        
        # 更新用户会员
        db.update_user_membership(order['user_id'], order['membership_days'], order['order_id'])
        
        # 异步邀请到频道（需要在事件循环中）
        import asyncio
        from telegram.ext import Application
        
        async def invite_async():
            app = Application.builder().token(BOT_TOKEN).build()
            await app.initialize()
            await invite_user_to_channel(app, order['user_id'], order['order_id'])
            
            # 通知用户
            plan_info = MEMBERSHIP_PLANS.get(order['plan_type'], {})
            await app.bot.send_message(
                chat_id=order['user_id'],
                text=f"✅ 支付成功！\n\n"
                     f"套餐: {plan_info.get('name', 'N/A')}\n"
                     f"订单号: {order['order_id']}\n"
                     f"交易哈希: {order_info.get('tx_hash')}\n\n"
                     f"会员已激活，请查看邀请链接"
            )
            await app.shutdown()
        
        # 在新的事件循环中运行
        try:
            asyncio.run(invite_async())
        except Exception as e:
            logger.error(f"Failed to process payment callback: {e}")
        
        db.add_log('payment_received', order['user_id'], order['order_id'], 
                  f"TRON payment received: {order_info.get('tx_hash')}")
    
    tron_payment.set_callback('payment_received', on_payment_received)


# ========== 主函数 ==========

def main():
    """启动 Bot"""
    logger.info("Starting bot...")
    
    # 设置 TRON 回调
    setup_tron_callbacks()
    
    # 创建 Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 注册命令处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("orders", orders_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("pending", pending_command))
    
    # 注册回调处理器
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # 注册消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 启动 Bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()


