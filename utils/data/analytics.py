from .core import connect_db

def ensure_analytics_indexes(_ignored=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute('CREATE INDEX IF NOT EXISTS idx_payments_paid_at ON payments(paid_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_payments_refund_of ON payments(refund_of)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_payments_session_id ON payments(session_id)')
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_payments_paid_at_nonref "
            "ON payments(paid_at) WHERE is_refund IS NOT TRUE AND is_dp IS NOT TRUE"
        )
        c.execute('CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(method)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_order_items_ts ON order_items("timestamp")')
        c.execute('CREATE INDEX IF NOT EXISTS idx_order_items_session_id ON order_items(session_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_order_items_created_by ON order_items(created_by_user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_order_items_status ON order_items(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_order_items_item ON order_items(item_name)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sessions_closed_at ON sessions(closed_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_reservations_date_time ON reservations(date, time)')
