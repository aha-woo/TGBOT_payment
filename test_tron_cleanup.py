#!/usr/bin/env python3
"""
测试 TRON 订单自动清理功能

使用方法：
    python3 test_tron_cleanup.py [超时分钟数]
    
示例：
    python3 test_tron_cleanup.py 1    # 清理 1 分钟前的订单
    python3 test_tron_cleanup.py      # 使用默认配置
"""

import sys
from datetime import datetime, timedelta
from database import Database
from config import ORDER_TIMEOUT_MINUTES

def show_pending_orders(db):
    """显示所有待支付订单"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT order_id, user_id, payment_method, amount, currency, created_at 
        FROM orders
        WHERE status='pending'
        ORDER BY created_at DESC
    """)
    
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        print("   ✅ 没有待支付订单")
        return []
    
    for order in orders:
        order_id, user_id, method, amount, currency, created_at = order
        created_time = datetime.fromisoformat(created_at)
        age_minutes = (datetime.now() - created_time).total_seconds() / 60
        
        emoji = "💎" if method == "tron" else "🏪"
        print(f"   {emoji} {order_id[:25]}...")
        print(f"      用户: {user_id} | 金额: {amount} {currency}")
        print(f"      创建于: {created_at} ({age_minutes:.1f} 分钟前)")
        print()
    
    return orders

def test_cleanup(timeout_minutes=None):
    """测试订单清理"""
    
    if timeout_minutes is None:
        timeout_minutes = ORDER_TIMEOUT_MINUTES
    
    print("=" * 70)
    print("🧪 TRON 订单自动清理功能测试")
    print("=" * 70)
    print(f"⏰ 超时时间: {timeout_minutes} 分钟")
    print()
    
    db = Database('payment_bot.db')
    
    # 1. 显示当前待支付订单
    print("📋 当前所有待支付订单：")
    print("-" * 70)
    pending_orders = show_pending_orders(db)
    print()
    
    # 2. 显示将要清理的订单
    print(f"🔍 将要清理的订单（创建于 {timeout_minutes} 分钟前）：")
    print("-" * 70)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    timeout_time = datetime.now() - timedelta(minutes=timeout_minutes)
    
    # TRON 订单
    cursor.execute("""
        SELECT COUNT(*), payment_method
        FROM orders
        WHERE status='pending' AND created_at < ?
        GROUP BY payment_method
    """, (timeout_time,))
    
    to_clean = cursor.fetchall()
    
    tron_count = 0
    xianyu_count = 0
    
    for count, method in to_clean:
        if method == 'tron':
            tron_count = count
            print(f"   💎 TRON 订单: {count} 个")
        elif method == 'xianyu':
            xianyu_count = count
            print(f"   🏪 闲鱼订单: {count} 个")
    
    if tron_count == 0 and xianyu_count == 0:
        print(f"   ✅ 没有超过 {timeout_minutes} 分钟的待支付订单")
    
    conn.close()
    print()
    
    # 3. 询问是否执行清理
    try:
        response = input("是否执行清理？(y/n): ").strip().lower()
        
        if response == 'y':
            print()
            print("🧹 开始清理...")
            print("-" * 70)
            
            # 清理 TRON 订单
            tron_cleaned = db.cleanup_expired_tron_orders(timeout_minutes)
            print(f"   💎 TRON: 清理了 {tron_cleaned} 个订单")
            
            # 清理闲鱼订单
            xianyu_cleaned = db.cleanup_expired_xianyu_orders(timeout_minutes)
            print(f"   🏪 闲鱼: 清理了 {xianyu_cleaned} 个订单")
            
            total = tron_cleaned + xianyu_cleaned
            print()
            print(f"   ✅ 总计清理: {total} 个订单")
            print()
            
            # 4. 显示清理后的订单统计
            print("📊 清理后的订单统计：")
            print("-" * 70)
            
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT payment_method, status, COUNT(*) as count
                FROM orders
                GROUP BY payment_method, status
                ORDER BY payment_method, status
            """)
            
            stats = cursor.fetchall()
            
            current_method = None
            for method, status, count in stats:
                if method != current_method:
                    if current_method is not None:
                        print()
                    emoji = "💎" if method == "tron" else "🏪"
                    print(f"   {emoji} {method.upper()}:")
                    current_method = method
                
                status_emoji = {
                    'pending': '⏳',
                    'paid': '✅',
                    'cancelled': '❌',
                    'expired': '⏰',
                    'timeout': '⏰'
                }.get(status, '❓')
                
                print(f"      {status_emoji} {status:10s}: {count} 个")
            
            conn.close()
        else:
            print("\n⏭️  跳过清理")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  测试中断")
        sys.exit(0)
    
    print()
    print("=" * 70)
    print("✅ 测试完成！")
    print()
    print("💡 提示：")
    print("   - Bot 运行时会自动执行清理（每 5 分钟一次）")
    print("   - TRON 订单超时后状态变为 'timeout'")
    print("   - 闲鱼订单超时后状态变为 'expired'")
    print("   - 查看日志: pm2 logs payment-bot")
    print("=" * 70)

if __name__ == '__main__':
    try:
        timeout = int(sys.argv[1]) if len(sys.argv) > 1 else None
        test_cleanup(timeout)
    except ValueError:
        print("❌ 错误: 超时时间必须是数字")
        print("用法: python3 test_tron_cleanup.py [超时分钟数]")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

