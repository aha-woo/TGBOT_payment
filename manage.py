"""
数据库管理工具
用于查看统计、备份数据等
"""
import sys
import os
from datetime import datetime, timedelta
import shutil
from database import Database
from config import DATABASE_PATH, MEMBERSHIP_PLANS

db = Database(DATABASE_PATH)


def show_statistics():
    """显示统计信息"""
    stats = db.get_statistics()
    
    print("\n" + "="*50)
    print("📊 系统统计信息")
    print("="*50)
    print(f"\n👥 用户统计:")
    print(f"  总用户数: {stats['total_users']}")
    print(f"  活跃会员: {stats['active_members']}")
    
    print(f"\n📋 订单统计:")
    print(f"  总订单数: {stats['total_orders']}")
    print(f"  已支付: {stats['paid_orders']}")
    print(f"  待处理: {stats['pending_orders']}")
    
    print(f"\n💰 收入统计:")
    print(f"  USDT: {stats['total_usdt']:.2f}")
    print(f"  人民币: ¥{stats['total_cny']:.2f}")
    
    print(f"\n📅 今日数据:")
    print(f"  新订单: {stats['today_orders']}")
    print(f"  已支付: {stats['today_paid']}")
    print("="*50 + "\n")


def show_recent_orders(limit=10):
    """显示最近订单"""
    orders = db.get_all_orders(limit=limit)
    
    print("\n" + "="*80)
    print(f"📋 最近 {limit} 个订单")
    print("="*80)
    print(f"{'订单号':<30} {'用户ID':<12} {'金额':<10} {'状态':<10} {'时间'}")
    print("-"*80)
    
    for order in orders:
        order_id = order['order_id'][:28] + '..'
        user_id = str(order['user_id'])
        amount = f"{order['amount']} {order['currency']}"
        status = order['status']
        created = order['created_at'][:16]
        
        print(f"{order_id:<30} {user_id:<12} {amount:<10} {status:<10} {created}")
    
    print("="*80 + "\n")


def show_pending_xianyu():
    """显示待审核的闲鱼订单"""
    orders = db.get_pending_xianyu_orders()
    
    if not orders:
        print("\n✅ 暂无待审核的闲鱼订单\n")
        return
    
    print("\n" + "="*80)
    print(f"🛒 待审核的闲鱼订单 ({len(orders)} 个)")
    print("="*80)
    
    for order in orders:
        user = db.get_user(order['user_id'])
        plan_info = MEMBERSHIP_PLANS.get(order['plan_type'], {})
        
        print(f"\n订单号: {order['order_id']}")
        print(f"用户: @{user['username'] or 'N/A'} (ID: {order['user_id']})")
        print(f"套餐: {plan_info.get('name', 'N/A')}")
        print(f"金额: ¥{order['amount']}")
        print(f"闲鱼订单号: {order['xianyu_order_number'] or '未提交'}")
        print(f"创建时间: {order['created_at']}")
        print("-"*80)
    
    print("="*80 + "\n")


def show_members(limit=20):
    """显示会员列表"""
    members = db.get_all_users(is_member=True, limit=limit)
    
    print("\n" + "="*80)
    print(f"✨ 活跃会员列表 (最近 {limit} 个)")
    print("="*80)
    print(f"{'用户ID':<12} {'用户名':<20} {'到期时间':<20} {'剩余天数'}")
    print("-"*80)
    
    for member in members:
        user_id = str(member['user_id'])
        username = f"@{member['username']}" if member['username'] else 'N/A'
        member_until = datetime.fromisoformat(member['member_until'])
        days_left = (member_until - datetime.now()).days
        
        print(f"{user_id:<12} {username:<20} {member_until.strftime('%Y-%m-%d %H:%M'):<20} {days_left} 天")
    
    print("="*80 + "\n")


def check_expired():
    """检查并更新过期会员"""
    expired_users = db.check_expired_members()
    
    if expired_users:
        print(f"\n⏰ 发现 {len(expired_users)} 个过期会员，已自动更新状态")
        for user_id in expired_users:
            user = db.get_user(user_id)
            print(f"  - {user_id} (@{user['username'] or 'N/A'})")
    else:
        print("\n✅ 暂无过期会员")
    
    print()


def backup_database():
    """备份数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 备份主数据库
    if os.path.exists(DATABASE_PATH):
        backup_path = os.path.join(backup_dir, f'payment_bot_backup_{timestamp}.db')
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"✅ 主数据库已备份: {backup_path}")
    
    # 备份 TRON 订单数据库
    tron_db_path = 'tron_orders.db'
    if os.path.exists(tron_db_path):
        backup_path = os.path.join(backup_dir, f'tron_orders_backup_{timestamp}.db')
        shutil.copy2(tron_db_path, backup_path)
        print(f"✅ TRON 数据库已备份: {backup_path}")
    
    print(f"\n📁 备份目录: {os.path.abspath(backup_dir)}\n")


def export_orders():
    """导出订单到 JSON"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_dir = 'exports'
    
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    filepath = os.path.join(export_dir, f'orders_export_{timestamp}.json')
    
    orders = db.get_all_orders(limit=10000)
    
    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ 订单已导出: {filepath}")
    print(f"   共 {len(orders)} 条记录\n")


def cleanup_old_data():
    """清理旧数据"""
    print("\n🧹 清理旧数据...")
    
    # 清理 90 天前的已取消/超时订单
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=90)
    cursor.execute("""
        SELECT COUNT(*) FROM orders 
        WHERE created_at < ? AND status IN ('cancelled', 'expired')
    """, (cutoff_date,))
    
    count = cursor.fetchone()[0]
    
    if count > 0:
        confirm = input(f"将删除 {count} 条旧订单记录，确认吗? (yes/no): ")
        if confirm.lower() == 'yes':
            cursor.execute("""
                DELETE FROM orders 
                WHERE created_at < ? AND status IN ('cancelled', 'expired')
            """, (cutoff_date,))
            conn.commit()
            print(f"✅ 已删除 {count} 条旧记录")
        else:
            print("❌ 已取消")
    else:
        print("✅ 没有需要清理的数据")
    
    conn.close()
    print()


def show_menu():
    """显示菜单"""
    print("\n" + "="*50)
    print("🛠️  数据库管理工具")
    print("="*50)
    print("1. 查看统计信息")
    print("2. 查看最近订单")
    print("3. 查看待审核订单")
    print("4. 查看会员列表")
    print("5. 检查过期会员")
    print("6. 备份数据库")
    print("7. 导出订单")
    print("8. 清理旧数据")
    print("0. 退出")
    print("="*50)


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'stats':
            show_statistics()
        elif command == 'orders':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_recent_orders(limit)
        elif command == 'pending':
            show_pending_xianyu()
        elif command == 'members':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            show_members(limit)
        elif command == 'expired':
            check_expired()
        elif command == 'backup':
            backup_database()
        elif command == 'export':
            export_orders()
        elif command == 'cleanup':
            cleanup_old_data()
        else:
            print(f"未知命令: {command}")
            print("\n可用命令:")
            print("  python manage.py stats          - 查看统计")
            print("  python manage.py orders [N]     - 查看最近N个订单")
            print("  python manage.py pending        - 查看待审核订单")
            print("  python manage.py members [N]    - 查看会员列表")
            print("  python manage.py expired        - 检查过期会员")
            print("  python manage.py backup         - 备份数据库")
            print("  python manage.py export         - 导出订单")
            print("  python manage.py cleanup        - 清理旧数据")
        return
    
    # 交互式菜单
    while True:
        show_menu()
        choice = input("\n请选择操作 (0-8): ").strip()
        
        if choice == '1':
            show_statistics()
        elif choice == '2':
            try:
                limit = int(input("显示多少条? (默认10): ") or "10")
                show_recent_orders(limit)
            except ValueError:
                print("❌ 无效输入")
        elif choice == '3':
            show_pending_xianyu()
        elif choice == '4':
            try:
                limit = int(input("显示多少个会员? (默认20): ") or "20")
                show_members(limit)
            except ValueError:
                print("❌ 无效输入")
        elif choice == '5':
            check_expired()
        elif choice == '6':
            backup_database()
        elif choice == '7':
            export_orders()
        elif choice == '8':
            cleanup_old_data()
        elif choice == '0':
            print("\n👋 再见！\n")
            break
        else:
            print("❌ 无效选择")
        
        input("\n按 Enter 继续...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见！\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")




