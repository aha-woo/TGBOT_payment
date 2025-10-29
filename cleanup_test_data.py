#!/usr/bin/env python3
"""
测试数据清理脚本

使用方法：
    python3 cleanup_test_data.py

功能：
    1. 清除所有订单
    2. 清除所有用户（保留管理员）
    3. 清除所有日志
    4. 清除所有广告模板和任务
    5. 完全重置数据库（保留管理员）
    6. 备份数据库
"""

import sys
import os
from datetime import datetime
from database import Database
import shutil

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_section(text):
    """打印小节"""
    print("\n" + "-" * 60)
    print(f"  {text}")
    print("-" * 60)

def backup_database(db_path='payment_bot.db'):
    """备份数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def get_database_stats(db):
    """获取数据库统计信息"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # 订单统计
    cursor.execute("SELECT COUNT(*), payment_method, status FROM orders GROUP BY payment_method, status")
    orders = cursor.fetchall()
    stats['orders'] = orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    stats['total_orders'] = cursor.fetchone()[0]
    
    # 用户统计
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = cursor.fetchone()[0]
    
    # 日志统计
    cursor.execute("SELECT COUNT(*) FROM system_logs")
    stats['total_logs'] = cursor.fetchone()[0]
    
    # 邀请统计
    cursor.execute("SELECT COUNT(*) FROM channel_invites")
    stats['total_invites'] = cursor.fetchone()[0]
    
    # 广告统计
    cursor.execute("SELECT COUNT(*) FROM promo_templates")
    stats['total_promos'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scheduled_tasks")
    stats['total_tasks'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM promo_logs")
    stats['total_promo_logs'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def show_database_stats(db):
    """显示数据库统计信息"""
    print_section("📊 当前数据库统计")
    stats = get_database_stats(db)
    
    print(f"\n📦 订单: {stats['total_orders']} 个")
    if stats['orders']:
        for count, method, status in stats['orders']:
            emoji = {'tron': '💎', 'xianyu': '🏪'}.get(method, '❓')
            status_emoji = {'pending': '⏳', 'paid': '✅', 'cancelled': '❌', 'expired': '⏰', 'timeout': '⏰'}.get(status, '❓')
            print(f"   {emoji} {method:8s} {status_emoji} {status:10s}: {count} 个")
    
    print(f"\n👥 用户: {stats['total_users']} 个")
    print(f"📝 日志: {stats['total_logs']} 条")
    print(f"📨 邀请记录: {stats['total_invites']} 条")
    print(f"📢 广告模板: {stats['total_promos']} 个")
    print(f"⏰ 定时任务: {stats['total_tasks']} 个")
    print(f"📊 广告日志: {stats['total_promo_logs']} 条")

def clear_orders(db):
    """清除所有订单"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("ℹ️  没有订单需要清除")
        conn.close()
        return
    
    cursor.execute("DELETE FROM orders")
    conn.commit()
    conn.close()
    
    print(f"✅ 已清除 {count} 个订单")

def clear_users_except_admins(db):
    """清除所有用户（保留管理员）"""
    from config import ADMIN_USER_IDS
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    
    if total == 0:
        print("ℹ️  没有用户需要清除")
        conn.close()
        return
    
    # 删除非管理员用户
    placeholders = ','.join('?' * len(ADMIN_USER_IDS))
    cursor.execute(f"DELETE FROM users WHERE user_id NOT IN ({placeholders})", ADMIN_USER_IDS)
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"✅ 已清除 {deleted} 个用户（保留 {len(ADMIN_USER_IDS)} 个管理员）")

def clear_logs(db):
    """清除所有日志"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM system_logs")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("ℹ️  没有日志需要清除")
        conn.close()
        return
    
    cursor.execute("DELETE FROM system_logs")
    conn.commit()
    conn.close()
    
    print(f"✅ 已清除 {count} 条日志")

def clear_invites(db):
    """清除所有邀请记录"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM channel_invites")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("ℹ️  没有邀请记录需要清除")
        conn.close()
        return
    
    cursor.execute("DELETE FROM channel_invites")
    conn.commit()
    conn.close()
    
    print(f"✅ 已清除 {count} 条邀请记录")

def clear_promos(db):
    """清除所有广告相关数据"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM promo_templates")
    templates = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scheduled_tasks")
    tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM promo_logs")
    logs = cursor.fetchone()[0]
    
    if templates == 0 and tasks == 0 and logs == 0:
        print("ℹ️  没有广告数据需要清除")
        conn.close()
        return
    
    cursor.execute("DELETE FROM promo_templates")
    cursor.execute("DELETE FROM scheduled_tasks")
    cursor.execute("DELETE FROM promo_logs")
    
    conn.commit()
    conn.close()
    
    print(f"✅ 已清除:")
    print(f"   - {templates} 个广告模板")
    print(f"   - {tasks} 个定时任务")
    print(f"   - {logs} 条广告日志")

def clear_all_except_admins(db):
    """清除所有数据（保留管理员）"""
    print_section("🧹 开始清除所有数据...")
    
    print("\n1️⃣ 清除订单...")
    clear_orders(db)
    
    print("\n2️⃣ 清除用户（保留管理员）...")
    clear_users_except_admins(db)
    
    print("\n3️⃣ 清除邀请记录...")
    clear_invites(db)
    
    print("\n4️⃣ 清除日志...")
    clear_logs(db)
    
    print("\n5️⃣ 清除广告数据...")
    clear_promos(db)
    
    print("\n✅ 所有数据已清除！")

def main_menu():
    """主菜单"""
    print_header("🧹 测试数据清理工具")
    
    db = Database('payment_bot.db')
    
    while True:
        show_database_stats(db)
        
        print_section("📋 选择操作")
        print("\n1. 清除所有订单")
        print("2. 清除所有用户（保留管理员）")
        print("3. 清除所有日志")
        print("4. 清除所有邀请记录")
        print("5. 清除所有广告数据")
        print("6. 🔥 清除所有数据（保留管理员）")
        print("7. 💾 备份数据库")
        print("0. 退出")
        
        try:
            choice = input("\n请选择 (0-7): ").strip()
            
            if choice == '0':
                print("\n👋 再见！")
                break
            
            elif choice == '1':
                confirm = input("\n⚠️  确认清除所有订单？(yes/no): ").strip().lower()
                if confirm == 'yes':
                    clear_orders(db)
                else:
                    print("❌ 已取消")
            
            elif choice == '2':
                confirm = input("\n⚠️  确认清除所有用户（保留管理员）？(yes/no): ").strip().lower()
                if confirm == 'yes':
                    clear_users_except_admins(db)
                else:
                    print("❌ 已取消")
            
            elif choice == '3':
                confirm = input("\n⚠️  确认清除所有日志？(yes/no): ").strip().lower()
                if confirm == 'yes':
                    clear_logs(db)
                else:
                    print("❌ 已取消")
            
            elif choice == '4':
                confirm = input("\n⚠️  确认清除所有邀请记录？(yes/no): ").strip().lower()
                if confirm == 'yes':
                    clear_invites(db)
                else:
                    print("❌ 已取消")
            
            elif choice == '5':
                confirm = input("\n⚠️  确认清除所有广告数据？(yes/no): ").strip().lower()
                if confirm == 'yes':
                    clear_promos(db)
                else:
                    print("❌ 已取消")
            
            elif choice == '6':
                print("\n⚠️  ⚠️  ⚠️  警告 ⚠️  ⚠️  ⚠️")
                print("即将清除所有数据（保留管理员账户）！")
                print("建议先备份数据库（选项 7）！")
                confirm = input("\n确认清除所有数据？请输入 'DELETE ALL' 确认: ").strip()
                if confirm == 'DELETE ALL':
                    clear_all_except_admins(db)
                else:
                    print("❌ 已取消")
            
            elif choice == '7':
                backup_database()
            
            else:
                print("❌ 无效选择")
            
            input("\n按 Enter 继续...")
        
        except KeyboardInterrupt:
            print("\n\n👋 已中断")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            input("\n按 Enter 继续...")

if __name__ == '__main__':
    try:
        main_menu()
    except Exception as e:
        print(f"\n❌ 严重错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

