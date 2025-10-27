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
    """开始命令 - 自定义欢迎界面"""
    user = update.effective_user
    db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    # 使用自定义欢迎消息（从 config.py）
    welcome_text = WELCOME_MESSAGE
    
    # 构建按钮布局
    keyboard = []
    
    # 第一行：支付方式（并排显示）
    # 根据配置决定按钮文字
    if ENABLE_MULTIPLE_PLANS:
        # 多套餐模式：显示简单的支付方式
        usdt_btn_text = "💎 USDT 支付"
        xianyu_btn_text = "🏪 闲鱼支付"
    else:
        # 单套餐模式：直接显示价格
        usdt_btn_text = f"💎 USDT 支付 - {DEFAULT_PLAN['price_usdt']} USDT"
        xianyu_btn_text = f"🏪 闲鱼支付 - ¥{DEFAULT_PLAN['price_cny']}"
    
    keyboard.append([
        InlineKeyboardButton(usdt_btn_text, callback_data="direct_usdt_payment"),
        InlineKeyboardButton(xianyu_btn_text, callback_data="direct_xianyu_payment")
    ])
    
    # 第二行：查询功能（并排显示）
    keyboard.append([
        InlineKeyboardButton("📋 我的订单", callback_data="my_orders"),
        InlineKeyboardButton("👤 会员状态", callback_data="my_status")
    ])
    
    # 第三行：客服和帮助（并排显示）
    keyboard.append([
        InlineKeyboardButton("👨‍💼 联系客服", url=CUSTOMER_SERVICE_URL),
        InlineKeyboardButton("❓ 使用帮助", callback_data="help")
    ])
    
    # 管理员功能（单独一行）
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("👑 管理员面板", callback_data="admin_panel")])
    
    # 隐藏的购买按钮（保留代码，但不显示）
    # if not is_member:
    #     keyboard.append([InlineKeyboardButton("🎉 立即购买会员", callback_data="buy_membership")])
    # else:
    #     keyboard.append([InlineKeyboardButton("🔄 续费会员", callback_data="buy_membership")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 如果配置了欢迎图片，发送图片+文字；否则只发送文字
    if WELCOME_IMAGE:
        try:
            await update.message.reply_photo(
                photo=WELCOME_IMAGE,
                caption=welcome_text,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to send welcome image: {e}")
            # 图片发送失败，降级为纯文字
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup
            )
    else:
        # 没有配置图片，只发送文字
        await update.message.reply_text(
            welcome_text,
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
        [InlineKeyboardButton("📢 广告管理", callback_data="promo_manage")],
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


async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """广告管理命令"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ 您没有权限")
        return
    
    await show_promo_menu(update, context)


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
    
    # 直接支付方式（从欢迎页面）
    elif data == "direct_usdt_payment":
        if ENABLE_MULTIPLE_PLANS:
            # 多套餐模式：显示套餐选择
            user_states[user_id] = {'selected_payment': 'usdt'}
            await show_membership_plans(update, context, query=query, payment_method='usdt')
        else:
            # 单套餐模式：直接进入支付
            await process_tron_payment(update, context, 'default', DEFAULT_PLAN, query)
    
    elif data == "direct_xianyu_payment":
        if ENABLE_MULTIPLE_PLANS:
            # 多套餐模式：显示购买指南和套餐选择
            await show_xianyu_guide(update, context, query=query)
        else:
            # 单套餐模式：直接创建订单并等待订单号
            await create_xianyu_order_direct(update, context, 'default', DEFAULT_PLAN, query)
    
    elif data.startswith("plan_"):
        plan_type = data.split("_")[1]
        await show_payment_methods(update, context, plan_type, query=query)
    
    # 闲鱼支付 - 选择套餐后直接进入订单号输入流程
    elif data.startswith("xianyu_plan_"):
        plan_type = data.replace("xianyu_plan_", "")
        plan_info = MEMBERSHIP_PLANS.get(plan_type)
        
        if not plan_info:
            await query.answer("套餐不存在", show_alert=True)
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
        
        # 设置用户状态，等待输入订单号
        user_states[user_id] = {
            'action': 'waiting_xianyu_order',
            'order_id': order_id
        }
        
        # 提示用户输入订单号
        text = f"""
✅ 订单已创建

🛒 套餐：{plan_info['name']}
💰 价格：¥{plan_info['price_cny']}
⏰ 时长：{plan_info['days']} 天
📋 订单号：`{order_id}`

📝 请输入您的闲鱼订单号

⚠️ 重要提示：
• 确保已在闲鱼完成付款
• 订单号通常为 10-20 位数字
• 提交后等待管理员审核（24小时内）

💡 如还未购买，请点击下方按钮前往闲鱼
"""
        
        keyboard = [
            [InlineKeyboardButton("🛒 打开闲鱼商品", url=XIANYU_PRODUCT_URL)],
            [
                InlineKeyboardButton("« 返回", callback_data="back_to_main"),
                InlineKeyboardButton("❌ 取消订单", callback_data=f"cancel_order_{order_id}")
            ]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
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
    
    # 广告管理功能
    elif data == "promo_manage":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        await show_promo_menu(update, context, query=query)
    
    elif data == "promo_list_templates":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        await show_promo_templates(update, context, query=query)
    
    elif data == "promo_list_tasks":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        await show_scheduled_tasks(update, context, query=query)
    
    elif data == "promo_logs":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        await show_promo_logs(update, context, query=query)
    
    elif data == "promo_create_template":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        user_states[user_id] = {'action': 'create_promo_template', 'step': 'name'}
        await query.edit_message_text(
            "📝 创建广告模板\n\n"
            "步骤 1/4: 请输入模板名称（用于识别）：\n\n"
            "发送 /cancel 取消创建"
        )
    
    elif data == "promo_create_task":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        templates = db.get_all_promo_templates(active_only=True)
        if not templates:
            await query.answer("❌ 请先创建广告模板", show_alert=True)
            await show_promo_menu(update, context, query=query)
            return
        
        keyboard = []
        for tmpl in templates:
            keyboard.append([InlineKeyboardButton(
                tmpl['name'],
                callback_data=f"promo_task_select_template_{tmpl['id']}"
            )])
        keyboard.append([InlineKeyboardButton("« 返回", callback_data="promo_manage")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⏰ 选择要使用的广告模板：", reply_markup=reply_markup)
    
    elif data.startswith("promo_task_select_template_"):
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        template_id = int(data.replace("promo_task_select_template_", ""))
        user_states[user_id] = {
            'action': 'create_scheduled_task',
            'template_id': template_id,
            'step': 'target_chats'
        }
        await query.edit_message_text(
            "⏰ 创建定时任务\n\n"
            "步骤 1/2: 请输入目标频道/群组 ID\n\n"
            "格式：\n"
            "• 单个: @channel 或 -1001234567890\n"
            "• 多个: @channel1,@channel2,-1001234567890\n\n"
            "发送 /cancel 取消创建"
        )
    
    elif data.startswith("promo_use_template_"):
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        template_id = int(data.replace("promo_use_template_", ""))
        user_states[user_id] = {
            'action': 'send_promo_now',
            'template_id': template_id
        }
        await query.edit_message_text(
            "📤 立即发送广告\n\n"
            "请输入目标频道/群组 ID\n\n"
            "格式：\n"
            "• 单个: @channel 或 -1001234567890\n"
            "• 多个: @channel1,@channel2,-1001234567890\n\n"
            "发送 /cancel 取消发送"
        )
    
    elif data.startswith("promo_delete_template_"):
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        template_id = int(data.replace("promo_delete_template_", ""))
        db.delete_promo_template(template_id)
        await query.answer("✅ 模板已删除", show_alert=True)
        await show_promo_templates(update, context, query=query)
    
    elif data.startswith("promo_cancel_task_"):
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        task_id = int(data.replace("promo_cancel_task_", ""))
        db.cancel_scheduled_task(task_id)
        await query.answer("✅ 任务已取消", show_alert=True)
        await show_scheduled_tasks(update, context, query=query)
    
    elif data == "promo_send_now":
        if not is_admin(user_id):
            await query.answer("⛔ 您没有权限", show_alert=True)
            return
        
        templates = db.get_all_promo_templates(active_only=True)
        if not templates:
            await query.answer("❌ 请先创建广告模板", show_alert=True)
            await show_promo_menu(update, context, query=query)
            return
        
        keyboard = []
        for tmpl in templates:
            keyboard.append([InlineKeyboardButton(
                tmpl['name'],
                callback_data=f"promo_use_template_{tmpl['id']}"
            )])
        keyboard.append([InlineKeyboardButton("« 返回", callback_data="promo_manage")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📤 选择要发送的广告模板：", reply_markup=reply_markup)
    
    # 取消订单
    elif data.startswith("cancel_order_"):
        order_id = data.replace("cancel_order_", "")
        order = db.get_order(order_id)
        
        if not order:
            await query.answer("❌ 订单不存在", show_alert=True)
            return
        
        if order['user_id'] != user_id:
            await query.answer("❌ 这不是您的订单", show_alert=True)
            return
        
        if order['status'] != 'pending':
            await query.answer("❌ 该订单无法取消", show_alert=True)
            return
        
        # 更新订单状态为已取消
        db.update_order_status(order_id, 'cancelled')
        
        # 清除用户状态
        if user_id in user_states:
            del user_states[user_id]
        
        await query.answer("✅ 订单已取消", show_alert=True)
        
        # 返回主菜单
        welcome_text = WELCOME_MESSAGE
        keyboard = []
        
        if ENABLE_MULTIPLE_PLANS:
            usdt_btn_text = "💎 USDT 支付"
            xianyu_btn_text = "🏪 闲鱼支付"
        else:
            usdt_btn_text = f"💎 USDT 支付 - {DEFAULT_PLAN['price_usdt']} USDT"
            xianyu_btn_text = f"🏪 闲鱼支付 - ¥{DEFAULT_PLAN['price_cny']}"
        
        keyboard.append([
            InlineKeyboardButton(usdt_btn_text, callback_data="direct_usdt_payment"),
            InlineKeyboardButton(xianyu_btn_text, callback_data="direct_xianyu_payment")
        ])
        keyboard.append([
            InlineKeyboardButton("📋 我的订单", callback_data="my_orders"),
            InlineKeyboardButton("👤 会员状态", callback_data="my_status")
        ])
        keyboard.append([
            InlineKeyboardButton("👨‍💼 联系客服", url=CUSTOMER_SERVICE_URL),
            InlineKeyboardButton("❓ 使用帮助", callback_data="help")
        ])
        
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("👑 管理员面板", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(welcome_text, reply_markup=reply_markup)
    
    # 返回主菜单
    elif data == "back_to_main":
        # 清除用户状态
        if user_id in user_states:
            del user_states[user_id]
        
        # 使用自定义欢迎消息
        welcome_text = WELCOME_MESSAGE
        
        # 构建按钮布局（与 start_command 相同）
        keyboard = []
        
        # 第一行：支付方式
        # 根据配置决定按钮文字
        if ENABLE_MULTIPLE_PLANS:
            usdt_btn_text = "💎 USDT 支付"
            xianyu_btn_text = "🏪 闲鱼支付"
        else:
            usdt_btn_text = f"💎 USDT 支付 - {DEFAULT_PLAN['price_usdt']} USDT"
            xianyu_btn_text = f"🏪 闲鱼支付 - ¥{DEFAULT_PLAN['price_cny']}"
        
        keyboard.append([
            InlineKeyboardButton(usdt_btn_text, callback_data="direct_usdt_payment"),
            InlineKeyboardButton(xianyu_btn_text, callback_data="direct_xianyu_payment")
        ])
        
        # 第二行：查询功能
        keyboard.append([
            InlineKeyboardButton("📋 我的订单", callback_data="my_orders"),
            InlineKeyboardButton("👤 会员状态", callback_data="my_status")
        ])
        
        # 第三行：客服和帮助
        keyboard.append([
            InlineKeyboardButton("👨‍💼 联系客服", url=CUSTOMER_SERVICE_URL),
            InlineKeyboardButton("❓ 使用帮助", callback_data="help")
        ])
        
        # 管理员功能
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("👑 管理员面板", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 判断当前消息是否有照片（如USDT支付页面）
        try:
            if query.message.photo:
                # 如果是图片消息，发送新消息并删除旧消息
                await context.bot.send_message(
                    chat_id=user_id,
                    text=welcome_text,
                    reply_markup=reply_markup
                )
                await query.message.delete()
            else:
                # 普通文本消息，直接编辑
                await query.edit_message_text(welcome_text, reply_markup=reply_markup)
        except Exception as e:
            # 如果编辑失败（如消息太旧），发送新消息
            await context.bot.send_message(
                chat_id=user_id,
                text=welcome_text,
                reply_markup=reply_markup
            )


# ========== 业务逻辑函数 ==========

async def show_xianyu_guide(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """显示闲鱼购买指南页面"""
    text = """
🏪 闲鱼支付购买指南

📱 购买步骤：
1️⃣ 点击下方「打开闲鱼商品」按钮
2️⃣ 在闲鱼完成购买（需要登录闲鱼账号）
3️⃣ 获得订单号后，返回这里
4️⃣ 选择您购买的套餐
5️⃣ 输入订单号提交审核

⚠️ 重要提示：
• 闲鱼需要您手动登录（Bot 无法自动登录）
• 如已登录浏览器，通常会保持登录状态
• 订单审核时间：24 小时内

💎 会员套餐：
"""
    
    keyboard = []
    
    # 添加套餐信息到文字
    for plan_key, plan_info in MEMBERSHIP_PLANS.items():
        text += f"• {plan_info['name']}：¥{plan_info['price_cny']} / {plan_info['days']}天\n"
    
    text += "\n👇 请先完成购买，再选择套餐提交订单号"
    
    # 第一个按钮：打开闲鱼商品（URL 按钮）
    keyboard.append([InlineKeyboardButton("🛒 打开闲鱼商品", url=XIANYU_PRODUCT_URL)])
    
    # 添加套餐选择按钮（每个套餐一行）
    for plan_key, plan_info in MEMBERSHIP_PLANS.items():
        keyboard.append([InlineKeyboardButton(
            f"📝 {plan_info['name']} - ¥{plan_info['price_cny']}",
            callback_data=f"xianyu_plan_{plan_key}"
        )])
    
    # 返回按钮
    keyboard.append([InlineKeyboardButton("« 返回主菜单", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_membership_plans(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None, payment_method=None):
    """显示会员套餐
    
    Args:
        payment_method: 如果提供，选择套餐后直接跳转到该支付方式（'usdt' 或 'xianyu'）
    """
    if payment_method == 'usdt':
        text = "💎 USDT 支付 - 选择会员套餐：\n\n"
    elif payment_method == 'xianyu':
        text = "🏪 闲鱼支付 - 选择会员套餐：\n\n"
    else:
        text = "💎 选择会员套餐：\n\n"
    
    keyboard = []
    
    for plan_key, plan_info in MEMBERSHIP_PLANS.items():
        text += f"🔹 {plan_info['name']}\n"
        text += f"   时长: {plan_info['days']} 天\n"
        text += f"   USDT: {plan_info['price_usdt']} | 人民币: ¥{plan_info['price_cny']}\n\n"
        
        # 如果已选择支付方式，直接跳转到支付处理
        if payment_method == 'usdt':
            callback_data = f"pay_tron_{plan_key}"
        elif payment_method == 'xianyu':
            callback_data = f"pay_xianyu_{plan_key}"
        else:
            callback_data = f"plan_{plan_key}"
        
        keyboard.append([InlineKeyboardButton(
            f"{plan_info['name']} - {plan_info['days']}天",
            callback_data=callback_data
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


async def create_xianyu_order_direct(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     plan_type: str, plan_info: dict, query):
    """单套餐模式：直接创建闲鱼订单"""
    user_id = update.effective_user.id
    
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
    
    # 设置用户状态，等待输入订单号
    user_states[user_id] = {
        'action': 'waiting_xianyu_order',
        'order_id': order_id
    }
    
    # 显示订单信息和操作指南
    text = f"""
✅ 订单已创建

🛒 套餐：{plan_info['name']}
💰 价格：¥{plan_info['price_cny']}
⏰ 时长：{plan_info['days']} 天
📋 订单号：`{order_id}`

📱 支付步骤：
1️⃣ 点击下方「打开闲鱼商品」按钮
2️⃣ 在闲鱼完成购买（需要登录闲鱼账号）
3️⃣ 复制闲鱼订单号
4️⃣ 回到这里发送订单号给我

⚠️ 重要提示：
• 确保已在闲鱼完成付款
• 订单号通常为 10-20 位数字
• 提交后等待管理员审核（24小时内）
"""
    
    keyboard = [
        [InlineKeyboardButton("🛒 打开闲鱼商品", url=XIANYU_PRODUCT_URL)],
        [
            InlineKeyboardButton("« 返回", callback_data="back_to_main"),
            InlineKeyboardButton("❌ 取消订单", callback_data=f"cancel_order_{order_id}")
        ]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


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
            [
                InlineKeyboardButton("« 返回主菜单", callback_data="back_to_main"),
                InlineKeyboardButton("❌ 取消订单", callback_data=f"cancel_order_{order_id}")
            ]
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
        [
            InlineKeyboardButton("« 返回", callback_data="back_to_main"),
            InlineKeyboardButton("❌ 取消订单", callback_data=f"cancel_order_{order_id}")
        ]
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


# ========== 广告管理功能 ==========

async def show_promo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """显示广告管理菜单"""
    templates = db.get_all_promo_templates(active_only=True)
    tasks = db.get_all_scheduled_tasks(status='pending')
    
    text = f"""📢 广告管理

📝 广告模板: {len(templates)} 个
⏰ 待发送任务: {len(tasks)} 个

选择操作："""
    
    keyboard = [
        [InlineKeyboardButton("➕ 创建广告模板", callback_data="promo_create_template")],
        [InlineKeyboardButton("📝 查看模板列表", callback_data="promo_list_templates")],
        [InlineKeyboardButton("⏰ 创建定时任务", callback_data="promo_create_task")],
        [InlineKeyboardButton("📋 查看任务列表", callback_data="promo_list_tasks")],
        [InlineKeyboardButton("📤 立即发送广告", callback_data="promo_send_now")],
        [InlineKeyboardButton("📊 发送记录", callback_data="promo_logs")],
        [InlineKeyboardButton("🔙 返回管理面板", callback_data="admin_panel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_promo_templates(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """显示广告模板列表"""
    templates = db.get_all_promo_templates(active_only=True)
    
    if not templates:
        text = "📝 还没有创建任何广告模板\n\n点击下方按钮创建第一个模板："
        keyboard = [
            [InlineKeyboardButton("➕ 创建模板", callback_data="promo_create_template")],
            [InlineKeyboardButton("🔙 返回", callback_data="promo_manage")]
        ]
    else:
        text = "📝 广告模板列表：\n\n"
        keyboard = []
        
        for tmpl in templates:
            text += f"🔹 {tmpl['name']}\n"
            text += f"   ID: {tmpl['id']} | 创建时间: {tmpl['created_at']}\n\n"
            keyboard.append([
                InlineKeyboardButton(f"📤 {tmpl['name']}", callback_data=f"promo_use_template_{tmpl['id']}"),
                InlineKeyboardButton("✏️", callback_data=f"promo_edit_template_{tmpl['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"promo_delete_template_{tmpl['id']}")
            ])
        
        keyboard.append([InlineKeyboardButton("➕ 创建新模板", callback_data="promo_create_template")])
        keyboard.append([InlineKeyboardButton("🔙 返回", callback_data="promo_manage")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_scheduled_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """显示定时任务列表"""
    tasks = db.get_all_scheduled_tasks()
    
    if not tasks:
        text = "⏰ 还没有创建任何定时任务\n\n点击下方按钮创建任务："
        keyboard = [
            [InlineKeyboardButton("➕ 创建任务", callback_data="promo_create_task")],
            [InlineKeyboardButton("🔙 返回", callback_data="promo_manage")]
        ]
    else:
        text = "⏰ 定时任务列表：\n\n"
        keyboard = []
        
        for task in tasks[:10]:  # 只显示前10个
            template = db.get_promo_template(task['template_id'])
            template_name = template['name'] if template else '未知模板'
            
            status_emoji = {
                'pending': '⏳',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(task['status'], '❓')
            
            text += f"{status_emoji} {template_name}\n"
            text += f"   发送时间: {task['scheduled_time']}\n"
            text += f"   状态: {task['status']}\n\n"
            
            if task['status'] == 'pending':
                keyboard.append([
                    InlineKeyboardButton(f"查看 #{task['id']}", callback_data=f"promo_view_task_{task['id']}"),
                    InlineKeyboardButton("🚫 取消", callback_data=f"promo_cancel_task_{task['id']}")
                ])
        
        keyboard.append([InlineKeyboardButton("➕ 创建新任务", callback_data="promo_create_task")])
        keyboard.append([InlineKeyboardButton("🔙 返回", callback_data="promo_manage")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_promo_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """显示广告发送记录"""
    logs = db.get_promo_logs(limit=20)
    
    if not logs:
        text = "📊 还没有发送记录"
    else:
        text = "📊 最近发送记录：\n\n"
        
        for log in logs:
            status_emoji = '✅' if log['status'] == 'success' else '❌'
            text += f"{status_emoji} {log['template_name']}\n"
            text += f"   目标: {log['target_chat']}\n"
            text += f"   时间: {log['sent_at']}\n"
            if log['error_message']:
                text += f"   错误: {log['error_message']}\n"
            text += "\n"
    
    keyboard = [[InlineKeyboardButton("🔙 返回", callback_data="promo_manage")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def send_promo_message(app: Application, template_id: int, target_chat: str, task_id: int = None) -> bool:
    """发送广告消息到指定频道/群组"""
    try:
        template = db.get_promo_template(template_id)
        if not template:
            db.add_promo_log(template_id, target_chat, 'failed', task_id, error_message='Template not found')
            return False
        
        # 创建按钮
        keyboard = None
        if template['button_text'] and template['button_url']:
            keyboard = [[InlineKeyboardButton(template['button_text'], url=template['button_url'])]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reply_markup = None
        
        # 判断是否有图片
        if template.get('image_file_id'):
            # 有图片：发送图片消息
            caption = template['message'] if template['message'] else None
            sent_message = await app.bot.send_photo(
                chat_id=target_chat,
                photo=template['image_file_id'],
                caption=caption,
                reply_markup=reply_markup
            )
        else:
            # 无图片：发送纯文字消息
            sent_message = await app.bot.send_message(
                chat_id=target_chat,
                text=template['message'],
                reply_markup=reply_markup
            )
        
        # 记录成功
        db.add_promo_log(template_id, target_chat, 'success', task_id, message_id=sent_message.message_id)
        logger.info(f"Promo message sent to {target_chat}: template {template_id}")
        return True
        
    except TelegramError as e:
        # 记录失败
        db.add_promo_log(template_id, target_chat, 'failed', task_id, error_message=str(e))
        logger.error(f"Failed to send promo to {target_chat}: {e}")
        return False


# ========== 消息处理 ==========

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理图片消息"""
    user_id = update.effective_user.id
    
    # 检查用户状态
    if user_id in user_states:
        state = user_states[user_id]
        
        # 只在创建模板的图片步骤接受图片
        if state.get('action') == 'create_promo_template' and state.get('step') == 'image':
            # 获取最大尺寸的图片
            photo = update.message.photo[-1]
            state['image_file_id'] = photo.file_id
            state['step'] = 'message'
            
            await update.message.reply_text(
                "✅ 图片已保存\n\n"
                "步骤 3/5: 请输入广告文字内容（可选）：\n\n"
                "（可以包含 emoji、换行等）\n\n"
                "发送 - 跳过（仅图片）\n"
                "发送 /cancel 取消创建"
            )
            return
    
    # 其他情况提示
    await update.message.reply_text("❓ 当前不需要图片，请使用命令与我交互")


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
        
        elif state['action'] == 'create_promo_template':
            # 处理创建广告模板
            if text and text.strip() == '/cancel':
                del user_states[user_id]
                await update.message.reply_text("❌ 已取消创建")
                return
            
            if state['step'] == 'name':
                state['name'] = text.strip()
                state['step'] = 'image'
                await update.message.reply_text(
                    f"✅ 模板名称：{state['name']}\n\n"
                    "步骤 2/5: 请发送一张图片（可选）\n\n"
                    "📸 发送图片 - 添加宣传图\n"
                    "📝 发送 - 跳过（无图片）\n"
                    "🚫 发送 /cancel 取消创建"
                )
                return
            
            elif state['step'] == 'image':
                # 检查是否跳过图片
                if text and text.strip() == '-':
                    state['image_file_id'] = None
                    state['step'] = 'message'
                    await update.message.reply_text(
                        "✅ 跳过图片\n\n"
                        "步骤 3/5: 请输入广告文字内容：\n\n"
                        "（可以包含 emoji、换行等）\n\n"
                        "发送 /cancel 取消创建"
                    )
                else:
                    await update.message.reply_text(
                        "❓ 请发送图片或发送 - 跳过"
                    )
                return
            
            elif state['step'] == 'message':
                if text.strip() == '-' and state.get('image_file_id'):
                    # 有图片，可以跳过文字
                    state['message'] = ''
                else:
                    state['message'] = text.strip()
                
                state['step'] = 'button_text'
                has_content = "图片" if state.get('image_file_id') else ""
                if state['message']:
                    has_content += ("+" if has_content else "") + "文字"
                
                await update.message.reply_text(
                    f"✅ 内容已保存（{has_content}）\n\n"
                    "步骤 4/5: 请输入按钮文字\n\n"
                    "（如：💳 立即购买）\n\n"
                    "发送 - 跳过（无按钮）\n"
                    "发送 /cancel 取消创建"
                )
                return
            
            elif state['step'] == 'button_text':
                if text.strip() == '-':
                    # 无按钮，直接创建
                    template_id = db.create_promo_template(
                        name=state['name'],
                        message=state['message'],
                        image_file_id=state.get('image_file_id'),
                        created_by=user_id
                    )
                    del user_states[user_id]
                    
                    has_image = "✅" if state.get('image_file_id') else "❌"
                    has_text = "✅" if state['message'] else "❌"
                    
                    await update.message.reply_text(
                        f"✅ 广告模板创建成功！\n\n"
                        f"模板ID: {template_id}\n"
                        f"模板名称: {state['name']}\n"
                        f"图片: {has_image}\n"
                        f"文字: {has_text}\n"
                        f"按钮: ❌\n\n"
                        "使用 /promo 管理广告"
                    )
                else:
                    state['button_text'] = text.strip()
                    state['step'] = 'button_url'
                    await update.message.reply_text(
                        f"✅ 按钮文字：{state['button_text']}\n\n"
                        f"步骤 5/5: 请输入按钮链接\n\n"
                        f"（如：https://t.me/YourBot）\n\n"
                        f"发送 /cancel 取消创建"
                    )
                return
            
            elif state['step'] == 'button_url':
                state['button_url'] = text.strip()
                
                # 创建模板
                template_id = db.create_promo_template(
                    name=state['name'],
                    message=state['message'],
                    image_file_id=state.get('image_file_id'),
                    button_text=state['button_text'],
                    button_url=state['button_url'],
                    created_by=user_id
                )
                
                del user_states[user_id]
                
                has_image = "✅" if state.get('image_file_id') else "❌"
                has_text = "✅" if state['message'] else "❌"
                
                await update.message.reply_text(
                    f"✅ 广告模板创建成功！\n\n"
                    f"模板ID: {template_id}\n"
                    f"模板名称: {state['name']}\n"
                    f"图片: {has_image}\n"
                    f"文字: {has_text}\n"
                    f"按钮: {state['button_text']} → {state['button_url']}\n\n"
                    "使用 /promo 管理广告"
                )
                return
        
        elif state['action'] == 'create_scheduled_task':
            # 处理创建定时任务
            if text.strip() == '/cancel':
                del user_states[user_id]
                await update.message.reply_text("❌ 已取消创建")
                return
            
            if state['step'] == 'target_chats':
                state['target_chats'] = text.strip()
                state['step'] = 'scheduled_time'
                await update.message.reply_text(
                    f"✅ 目标频道：{state['target_chats']}\n\n"
                    "步骤 2/2: 请输入发送时间\n\n"
                    "格式：YYYY-MM-DD HH:MM\n"
                    "例如：2025-10-28 14:30\n\n"
                    "发送 /cancel 取消创建"
                )
                return
            
            elif state['step'] == 'scheduled_time':
                try:
                    from datetime import datetime
                    scheduled_time = datetime.strptime(text.strip(), '%Y-%m-%d %H:%M')
                    
                    # 创建定时任务
                    task_id = db.create_scheduled_task(
                        template_id=state['template_id'],
                        target_chats=state['target_chats'],
                        scheduled_time=scheduled_time,
                        created_by=user_id
                    )
                    
                    del user_states[user_id]
                    await update.message.reply_text(
                        f"✅ 定时任务创建成功！\n\n"
                        f"任务ID: {task_id}\n"
                        f"发送时间: {scheduled_time.strftime('%Y-%m-%d %H:%M')}\n"
                        f"目标: {state['target_chats']}\n\n"
                        "任务将在指定时间自动发送"
                    )
                except ValueError:
                    await update.message.reply_text(
                        "❌ 时间格式错误！\n\n"
                        "请使用格式：YYYY-MM-DD HH:MM\n"
                        "例如：2025-10-28 14:30\n\n"
                        "发送 /cancel 取消创建"
                    )
                return
        
        elif state['action'] == 'send_promo_now':
            # 处理立即发送
            if text.strip() == '/cancel':
                del user_states[user_id]
                await update.message.reply_text("❌ 已取消发送")
                return
            
            target_chats = [chat.strip() for chat in text.strip().split(',')]
            template_id = state['template_id']
            
            await update.message.reply_text(f"📤 开始发送广告到 {len(target_chats)} 个目标...")
            
            success_count = 0
            failed_count = 0
            
            for chat in target_chats:
                result = await send_promo_message(context.application, template_id, chat)
                if result:
                    success_count += 1
                else:
                    failed_count += 1
                
                # 避免发送过快
                import asyncio
                await asyncio.sleep(1)
            
            del user_states[user_id]
            await update.message.reply_text(
                f"✅ 发送完成！\n\n"
                f"成功: {success_count}\n"
                f"失败: {failed_count}\n\n"
                "使用 /promo 查看详细记录"
            )
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


# ========== 定时任务执行器 ==========

async def check_and_execute_scheduled_tasks(context: ContextTypes.DEFAULT_TYPE):
    """检查并执行待发送的定时任务"""
    try:
        pending_tasks = db.get_pending_tasks()
        
        if not pending_tasks:
            return
        
        logger.info(f"Found {len(pending_tasks)} pending promo tasks to execute")
        
        for task in pending_tasks:
            try:
                # 更新任务状态为执行中
                db.update_task_status(task['id'], 'executing')
                
                # 解析目标频道列表
                target_chats = [chat.strip() for chat in task['target_chats'].split(',')]
                
                success_count = 0
                failed_count = 0
                error_messages = []
                
                # 发送到每个目标
                for chat in target_chats:
                    result = await send_promo_message(
                        context.application,
                        task['template_id'],
                        chat,
                        task['id']
                    )
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                        error_messages.append(f"Failed: {chat}")
                    
                    # 避免发送过快
                    await asyncio.sleep(1)
                
                # 更新任务状态
                result_message = f"Success: {success_count}, Failed: {failed_count}"
                if error_messages:
                    result_message += f"\nErrors: {', '.join(error_messages[:5])}"
                
                if failed_count == 0:
                    db.update_task_status(task['id'], 'completed', result_message)
                else:
                    db.update_task_status(task['id'], 'failed', result_message)
                
                # 通知管理员
                for admin_id in ADMIN_USER_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=f"📢 定时广告任务完成\n\n"
                                 f"任务ID: {task['id']}\n"
                                 f"成功: {success_count}\n"
                                 f"失败: {failed_count}\n"
                        )
                    except:
                        pass
                
                logger.info(f"Task {task['id']} executed: {result_message}")
                
            except Exception as e:
                logger.error(f"Error executing task {task['id']}: {e}")
                db.update_task_status(task['id'], 'failed', str(e))
                
    except Exception as e:
        logger.error(f"Error in check_and_execute_scheduled_tasks: {e}")


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
    application.add_handler(CommandHandler("promo", promo_command))
    
    # 注册回调处理器
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # 注册消息处理器
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))  # 图片消息
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # 文字消息
    
    # 添加定时任务检查器（每分钟检查一次）
    application.job_queue.run_repeating(
        check_and_execute_scheduled_tasks,
        interval=60,  # 每60秒检查一次
        first=10  # 启动后10秒开始
    )
    logger.info("Scheduled task checker started (running every 60 seconds)")
    
    # 启动 Bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()


