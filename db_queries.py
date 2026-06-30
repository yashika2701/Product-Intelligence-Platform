import os
import sqlite3
import pandas as pd

def get_db_connection():
    """
    Establishes a connection to either MySQL (if environment variables exist)
    or the default local SQLite database.
    """
    db_host = os.environ.get("DB_HOST")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")
    db_port = os.environ.get("DB_PORT")

    if db_host and db_user and db_name:
        try:
            import pymysql
            port = int(db_port) if db_port else 3306
            conn = pymysql.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                port=port
            )
            return conn, "mysql"
        except Exception as e:
            print(f"Could not connect to MySQL ({e}). Falling back to SQLite...")
            
    # Default SQLite
    conn = sqlite3.connect("marketplace.db")
    return conn, "sqlite"

def fetch_business_kpis(city=None, channel=None):
    """
    Calculates executive-level e-commerce KPIs with dynamic filtering.
    """
    conn, db_type = get_db_connection()
    
    # We join with the users table to allow filtering on city and acquisition_channel
    orders_query = """
        SELECT 
            COALESCE(SUM(o.amount), 0) as total_revenue,
            COALESCE(AVG(o.amount), 0) as avg_order_value,
            COUNT(DISTINCT o.session_id) as total_orders
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        WHERE (u.city = ? OR ? IS NULL)
          AND (u.acquisition_channel = ? OR ? IS NULL)
    """ if db_type == "sqlite" else """
        SELECT 
            COALESCE(SUM(o.amount), 0) as total_revenue,
            COALESCE(AVG(o.amount), 0) as avg_order_value,
            COUNT(DISTINCT o.session_id) as total_orders
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        WHERE (u.city = %s OR %s IS NULL)
          AND (u.acquisition_channel = %s OR %s IS NULL)
    """
    
    sessions_query = """
        SELECT COUNT(DISTINCT s.session_id) as total_sessions
        FROM sessions s
        JOIN users u ON s.user_id = u.user_id
        WHERE (u.city = ? OR ? IS NULL)
          AND (u.acquisition_channel = ? OR ? IS NULL)
    """ if db_type == "sqlite" else """
        SELECT COUNT(DISTINCT s.session_id) as total_sessions
        FROM sessions s
        JOIN users u ON s.user_id = u.user_id
        WHERE (u.city = %s OR %s IS NULL)
          AND (u.acquisition_channel = %s OR %s IS NULL)
    """
    
    funnel_query = """
        SELECT 
            COUNT(DISTINCT CASE WHEN e.event_type = 'Add To Cart' THEN s.session_id END) as cart_sessions,
            COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.session_id END) as purchase_sessions
        FROM sessions s
        JOIN events e ON s.session_id = e.session_id
        JOIN users u ON s.user_id = u.user_id
        WHERE (u.city = ? OR ? IS NULL)
          AND (u.acquisition_channel = ? OR ? IS NULL)
    """ if db_type == "sqlite" else """
        SELECT 
            COUNT(DISTINCT CASE WHEN e.event_type = 'Add To Cart' THEN s.session_id END) as cart_sessions,
            COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.session_id END) as purchase_sessions
        FROM sessions s
        JOIN events e ON s.session_id = e.session_id
        JOIN users u ON s.user_id = u.user_id
        WHERE (u.city = %s OR %s IS NULL)
          AND (u.acquisition_channel = %s OR %s IS NULL)
    """

    try:
        # Run queries
        df_orders = pd.read_sql_query(orders_query, conn, params=[city, city, channel, channel])
        df_sessions = pd.read_sql_query(sessions_query, conn, params=[city, city, channel, channel])
        df_funnel = pd.read_sql_query(funnel_query, conn, params=[city, city, channel, channel])
        
        # Calculate derived metrics
        rev = float(df_orders['total_revenue'].iloc[0])
        aov = float(df_orders['avg_order_value'].iloc[0])
        orders_cnt = int(df_orders['total_orders'].iloc[0])
        sessions_cnt = max(1, int(df_sessions['total_sessions'].iloc[0]))
        cart_sess = int(df_funnel['cart_sessions'].iloc[0])
        purch_sess = int(df_funnel['purchase_sessions'].iloc[0])
        
        conv_rate = (orders_cnt / sessions_cnt) * 100.0
        abandon_rate = (1.0 - (purch_sess / max(1, cart_sess))) * 100.0
        
        # Format results as a dict
        return {
            'total_revenue': round(rev, 2),
            'avg_order_value': round(aov, 2),
            'conversion_rate': round(conv_rate, 2),
            'abandonment_rate': round(abandon_rate, 2),
            'total_orders': orders_cnt,
            'total_sessions': sessions_cnt
        }
    finally:
        conn.close()

def fetch_funnel_data(device_type=None, channel=None):
    """
    Fetches the stage-by-stage session funnel, with optional device and channel filters.
    """
    conn, db_type = get_db_connection()
    
    query = """
        SELECT 
            COUNT(DISTINCT CASE WHEN e.event_type = 'App Open' THEN s.session_id END) as "App Open",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Search' THEN s.session_id END) as "Search",
            COUNT(DISTINCT CASE WHEN e.event_type = 'View Product' THEN s.session_id END) as "View Product",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Add To Cart' THEN s.session_id END) as "Add To Cart",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.session_id END) as "Checkout",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.session_id END) as "Purchase"
        FROM sessions s
        LEFT JOIN events e ON s.session_id = e.session_id
        JOIN users u ON s.user_id = u.user_id
        WHERE (s.device_type = ? OR ? IS NULL)
          AND (u.acquisition_channel = ? OR ? IS NULL)
    """ if db_type == "sqlite" else """
        SELECT 
            COUNT(DISTINCT CASE WHEN e.event_type = 'App Open' THEN s.session_id END) as "App Open",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Search' THEN s.session_id END) as "Search",
            COUNT(DISTINCT CASE WHEN e.event_type = 'View Product' THEN s.session_id END) as "View Product",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Add To Cart' THEN s.session_id END) as "Add To Cart",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.session_id END) as "Checkout",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.session_id END) as "Purchase"
        FROM sessions s
        LEFT JOIN events e ON s.session_id = e.session_id
        JOIN users u ON s.user_id = u.user_id
        WHERE (s.device_type = %s OR %s IS NULL)
          AND (u.acquisition_channel = %s OR %s IS NULL)
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=[device_type, device_type, channel, channel])
        # Transpose to get rows as steps
        df_transposed = df.T.reset_index()
        df_transposed.columns = ['Funnel Stage', 'Session Volume']
        
        # Calculate completion rates
        volumes = df_transposed['Session Volume'].tolist()
        step_conv = [100.0]
        drop_off = [0.0]
        
        for i in range(1, len(volumes)):
            prev = volumes[i-1]
            curr = volumes[i]
            conv = (curr / prev * 100.0) if prev > 0 else 0
            step_conv.append(round(conv, 2))
            drop_off.append(round(100.0 - conv, 2))
            
        df_transposed['Step Conversion %'] = step_conv
        df_transposed['Step Drop-off %'] = drop_off
        
        # Overall completion relative to App Open
        base_vol = max(1, volumes[0])
        df_transposed['Overall Completion %'] = [round((v / base_vol) * 100.0, 2) for v in volumes]
        
        return df_transposed
    finally:
        conn.close()

def fetch_retention_data():
    """
    Fetches Day 1 and Day 7 user retention, grouped by acquisition channel.
    """
    conn, db_type = get_db_connection()
    
    query = """
        WITH user_signups AS (
            SELECT user_id, signup_date, acquisition_channel FROM users
        ),
        user_sessions AS (
            SELECT DISTINCT user_id, session_date FROM sessions
        ),
        user_retention AS (
            SELECT 
                u.user_id,
                u.acquisition_channel,
                MAX(CASE WHEN s.session_date = u.signup_date THEN 1 ELSE 0 END) as d0_active,
                MAX(CASE WHEN s.session_date = DATE(u.signup_date, '+1 day') THEN 1 ELSE 0 END) as d1_active,
                MAX(CASE WHEN s.session_date = DATE(u.signup_date, '+7 day') THEN 1 ELSE 0 END) as d7_active
            FROM user_signups u
            LEFT JOIN user_sessions s ON u.user_id = s.user_id
            GROUP BY u.user_id, u.acquisition_channel, u.signup_date
        )
        SELECT 
            acquisition_channel as "Acquisition Channel",
            COUNT(user_id) as "Cohort Size",
            SUM(d1_active) as "Day 1 Active Users",
            ROUND(100.0 * SUM(d1_active) / NULLIF(COUNT(user_id), 0), 2) as "Day 1 Retention %",
            SUM(d7_active) as "Day 7 Active Users",
            ROUND(100.0 * SUM(d7_active) / NULLIF(COUNT(user_id), 0), 2) as "Day 7 Retention %"
        FROM user_retention
        GROUP BY acquisition_channel
    """ if db_type == "sqlite" else """
        WITH user_signups AS (
            SELECT user_id, signup_date, acquisition_channel FROM users
        ),
        user_sessions AS (
            SELECT DISTINCT user_id, session_date FROM sessions
        ),
        user_retention AS (
            SELECT 
                u.user_id,
                u.acquisition_channel,
                MAX(CASE WHEN s.session_date = u.signup_date THEN 1 ELSE 0 END) as d0_active,
                MAX(CASE WHEN s.session_date = DATE_ADD(u.signup_date, INTERVAL 1 DAY) THEN 1 ELSE 0 END) as d1_active,
                MAX(CASE WHEN s.session_date = DATE_ADD(u.signup_date, INTERVAL 7 DAY) THEN 1 ELSE 0 END) as d7_active
            FROM user_signups u
            LEFT JOIN user_sessions s ON u.user_id = s.user_id
            GROUP BY u.user_id, u.acquisition_channel, u.signup_date
        )
        SELECT 
            acquisition_channel as "Acquisition Channel",
            COUNT(user_id) as "Cohort Size",
            SUM(d1_active) as "Day 1 Active Users",
            ROUND(100.0 * SUM(d1_active) / NULLIF(COUNT(user_id), 0), 2) as "Day 1 Retention %",
            SUM(d7_active) as "Day 7 Active Users",
            ROUND(100.0 * SUM(d7_active) / NULLIF(COUNT(user_id), 0), 2) as "Day 7 Retention %"
        FROM user_retention
        GROUP BY acquisition_channel
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def fetch_user_segmentation():
    """
    Fetches performance metrics by user segment (New, Repeat, Dormant).
    """
    conn, db_type = get_db_connection()
    
    # Repeat vs Dormant vs New statistics
    query = """
        SELECT 
            u.user_segment as "User Segment",
            COUNT(DISTINCT u.user_id) as "User Count",
            COUNT(DISTINCT s.session_id) as "Total Sessions",
            ROUND(1.0 * COUNT(DISTINCT s.session_id) / NULLIF(COUNT(DISTINCT u.user_id), 0), 2) as "Avg Sessions per User",
            COALESCE(SUM(o.amount), 0) as "Total Spend USD",
            ROUND(COALESCE(SUM(o.amount), 0) / NULLIF(COUNT(DISTINCT u.user_id), 0), 2) as "Average Revenue per User (ARPU)"
        FROM users u
        LEFT JOIN sessions s ON u.user_id = s.user_id
        LEFT JOIN orders o ON s.session_id = o.session_id
        GROUP BY u.user_segment
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def fetch_ab_test_results():
    """
    Fetches A/B test results comparing Group A and Group B conversions.
    """
    conn, db_type = get_db_connection()
    
    query = """
        SELECT 
            ex.experiment_group as "Experiment Group",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.session_id END) as "Checkout Sessions",
            COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.session_id END) as "Purchase Sessions",
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.session_id END) / 
                  NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.session_id END), 0), 2) as "Conversion Rate %"
        FROM sessions s
        JOIN events e ON s.session_id = e.session_id
        JOIN experiments ex ON s.user_id = ex.user_id
        GROUP BY ex.experiment_group
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def fetch_filter_options():
    """
    Fetches dynamic lists of cities and channels for filter drop-downs.
    """
    conn, db_type = get_db_connection()
    try:
        cities = pd.read_sql_query("SELECT DISTINCT city FROM users ORDER BY city", conn)['city'].tolist()
        channels = pd.read_sql_query("SELECT DISTINCT acquisition_channel FROM users ORDER BY acquisition_channel", conn)['acquisition_channel'].tolist()
        return cities, channels
    finally:
        conn.close()
