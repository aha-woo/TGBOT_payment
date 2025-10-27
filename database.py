"""
数据库模型和操作
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = Lock()
        self.init_db()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def init_db(self):
        """初始化数据库表"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_member BOOLEAN DEFAULT 0,
                    member_since TIMESTAMP,
                    member_until TIMESTAMP,
                    total_spent_usdt REAL DEFAULT 0,
                    total_spent_cny REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            ''')
            
            # 订单表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    payment_method TEXT NOT NULL,
                    plan_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    paid_at TIMESTAMP,
                    expired_at TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    
                    -- TRON 相关
                    tron_tx_hash TEXT,
                    tron_order_id TEXT,
                    
                    -- 闲鱼相关
                    xianyu_order_number TEXT,
                    xianyu_screenshot TEXT,
                    
                    -- 其他
                    membership_days INTEGER,
                    admin_notes TEXT,
                    user_notes TEXT,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # 邀请记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS channel_invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    order_id TEXT NOT NULL,
                    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    invite_status TEXT DEFAULT 'success',
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            ''')
            
            # 系统日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_type TEXT NOT NULL,
                    user_id INTEGER,
                    order_id TEXT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_payment_method ON orders(payment_method)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_is_member ON users(is_member)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_member_until ON users(member_until)')
            
            conn.commit()
            conn.close()
            
        logger.info(f"Database initialized: {self.db_path}")
    
    # ========== 用户操作 ==========
    
    def get_or_create_user(self, user_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """获取或创建用户"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                # 更新最后活跃时间和用户信息
                cursor.execute("""
                    UPDATE users SET last_active=?, username=?, first_name=?, last_name=?
                    WHERE user_id=?
                """, (datetime.now(), username, first_name, last_name, user_id))
                conn.commit()
            else:
                # 创建新用户
                cursor.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, last_active)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, datetime.now()))
                conn.commit()
            
            # 返回用户信息
            cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            return dict(zip(columns, row))
    
    def update_user_membership(self, user_id: int, days: int, order_id: str) -> bool:
        """更新用户会员状态"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT member_until FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            
            if row and row[0]:
                # 已有会员，延期
                current_until = datetime.fromisoformat(row[0])
                if current_until > datetime.now():
                    new_until = current_until + timedelta(days=days)
                else:
                    new_until = datetime.now() + timedelta(days=days)
            else:
                # 新会员
                new_until = datetime.now() + timedelta(days=days)
            
            cursor.execute("""
                UPDATE users 
                SET is_member=1, member_since=COALESCE(member_since, ?), member_until=?
                WHERE user_id=?
            """, (datetime.now(), new_until, user_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            if success:
                self.add_log('membership_updated', user_id, order_id, 
                           f"Membership extended to {new_until}")
            
            return success
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_all_users(self, is_member: Optional[bool] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有用户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if is_member is not None:
            cursor.execute("""
                SELECT * FROM users WHERE is_member=? 
                ORDER BY last_active DESC LIMIT ?
            """, (int(is_member), limit))
        else:
            cursor.execute("SELECT * FROM users ORDER BY last_active DESC LIMIT ?", (limit,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def check_expired_members(self) -> List[int]:
        """检查过期会员"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE is_member=1 AND member_until < ?
        """, (datetime.now(),))
        
        expired_users = [row[0] for row in cursor.fetchall()]
        
        if expired_users:
            cursor.execute("""
                UPDATE users SET is_member=0 
                WHERE user_id IN ({})
            """.format(','.join('?' * len(expired_users))), expired_users)
            conn.commit()
        
        conn.close()
        return expired_users
    
    # ========== 订单操作 ==========
    
    def create_order(self, order_data: Dict[str, Any]) -> bool:
        """创建订单"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO orders 
                    (order_id, user_id, payment_method, plan_type, amount, currency, 
                     status, created_at, membership_days, user_notes, tron_order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_data['order_id'],
                    order_data['user_id'],
                    order_data['payment_method'],
                    order_data['plan_type'],
                    order_data['amount'],
                    order_data['currency'],
                    order_data.get('status', 'pending'),
                    order_data.get('created_at', datetime.now()),
                    order_data['membership_days'],
                    order_data.get('user_notes', ''),
                    order_data.get('tron_order_id', '')
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to create order: {e}")
                return False
            finally:
                conn.close()
    
    def update_order_status(self, order_id: str, status: str, **kwargs) -> bool:
        """更新订单状态"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            update_fields = ['status=?']
            params = [status]
            
            if status == 'paid':
                update_fields.append('paid_at=?')
                params.append(datetime.now())
            elif status == 'cancelled':
                update_fields.append('cancelled_at=?')
                params.append(datetime.now())
            elif status == 'expired':
                update_fields.append('expired_at=?')
                params.append(datetime.now())
            
            # 额外字段
            for key, value in kwargs.items():
                update_fields.append(f'{key}=?')
                params.append(value)
            
            params.append(order_id)
            
            cursor.execute(f"""
                UPDATE orders SET {', '.join(update_fields)}
                WHERE order_id=?
            """, params)
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id=?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_user_orders(self, user_id: int, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户订单"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM orders 
                WHERE user_id=? AND status=? 
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, status, limit))
        else:
            cursor.execute("""
                SELECT * FROM orders 
                WHERE user_id=? 
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_pending_xianyu_orders(self) -> List[Dict[str, Any]]:
        """获取待审核的闲鱼订单"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM orders 
            WHERE payment_method='xianyu' AND status='pending'
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_order_by_xianyu_number(self, xianyu_number: str) -> Optional[Dict[str, Any]]:
        """根据闲鱼订单号查询"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM orders WHERE xianyu_order_number=?
        """, (xianyu_number,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def count_user_pending_orders(self, user_id: int) -> int:
        """统计用户待支付订单数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE user_id=? AND status='pending'
        """, (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_user_last_order_time(self, user_id: int) -> Optional[datetime]:
        """获取用户最后下单时间"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(created_at) FROM orders WHERE user_id=?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return datetime.fromisoformat(row[0])
        return None
    
    # ========== 邀请记录 ==========
    
    def add_channel_invite(self, user_id: int, order_id: str, status: str = 'success'):
        """记录频道邀请"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO channel_invites (user_id, order_id, invite_status)
                VALUES (?, ?, ?)
            """, (user_id, order_id, status))
            conn.commit()
            conn.close()
    
    # ========== 统计 ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 用户统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN is_member=1 THEN 1 ELSE 0 END) as active_members
            FROM users
        """)
        user_stats = cursor.fetchone()
        
        # 订单统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as paid_orders,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending_orders,
                SUM(CASE WHEN status='paid' AND currency='USDT' THEN amount ELSE 0 END) as total_usdt,
                SUM(CASE WHEN status='paid' AND currency='CNY' THEN amount ELSE 0 END) as total_cny
            FROM orders
        """)
        order_stats = cursor.fetchone()
        
        # 今日统计
        cursor.execute("""
            SELECT 
                COUNT(*) as today_orders,
                SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as today_paid
            FROM orders
            WHERE DATE(created_at) = DATE('now')
        """)
        today_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_users': user_stats[0],
            'active_members': user_stats[1],
            'total_orders': order_stats[0],
            'paid_orders': order_stats[1],
            'pending_orders': order_stats[2],
            'total_usdt': order_stats[3] or 0,
            'total_cny': order_stats[4] or 0,
            'today_orders': today_stats[0],
            'today_paid': today_stats[1]
        }
    
    # ========== 日志 ==========
    
    def add_log(self, log_type: str, user_id: Optional[int], order_id: Optional[str], message: str):
        """添加系统日志"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs (log_type, user_id, order_id, message)
                VALUES (?, ?, ?, ?)
            """, (log_type, user_id, order_id, message))
            conn.commit()
            conn.close()


