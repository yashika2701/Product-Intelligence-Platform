import os
import re
import random
import datetime
import sqlite3

# Load local .env file manually to avoid dependency on python-dotenv
def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key, val = parts[0].strip(), parts[1].strip()
                        # Remove quotes if present
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        os.environ[key] = val
        print(".env configuration loaded.")
    else:
        print("No .env file found. Proceeding with system environment variables.")

# Translate MySQL DDL commands to SQLite syntax
def translate_mysql_to_sqlite(mysql_sql):
    cleaned_lines = []
    for line in mysql_sql.split('\n'):
        # Strip comments
        line_clean = line.split('--')[0].strip()
        if not line_clean:
            continue
        # Skip MySQL environment SET statements
        if line_clean.upper().startswith("SET "):
            continue
        # SQLite create table statements do not need separate INDEX specifications inside table definitions
        if 'INDEX `' in line_clean or 'KEY `' in line_clean:
            if 'FOREIGN KEY' in line_clean:
                cleaned_lines.append(line_clean)
            else:
                continue
        else:
            cleaned_lines.append(line_clean)
            
    sql = '\n'.join(cleaned_lines)
    if not sql.strip():
        return ""
        
    # Replace AUTO_INCREMENT PRIMARY KEY with INTEGER PRIMARY KEY AUTOINCREMENT
    sql = re.sub(r'INT\s+AUTO_INCREMENT\s+PRIMARY\s+KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'INT\s+AUTO_INCREMENT', 'INTEGER', sql, flags=re.IGNORECASE)
    
    # Replace COMMENT specifications
    sql = re.sub(r"COMMENT\s+'[^']*'", "", sql, flags=re.IGNORECASE)
    
    # Clean up trailing commas before closing parenthesis
    sql = re.sub(r',\s*\)', '\n)', sql)
    sql = re.sub(r',\s*\n\s*\)', '\n)', sql)
    
    # Remove ENGINE / CHARSET / COLLATE specifications
    sql = re.sub(r'ENGINE\s*=\s*\w+', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'DEFAULT\s+CHARSET\s*=\s*[\w\d]+', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'COLLATE\s*=\s*[\w_]+', '', sql, flags=re.IGNORECASE)
    
    return sql

# Initialize Database connection
def get_db_connection():
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
                port=port,
                autocommit=False
            )
            print(f"Connected successfully to MySQL database: {db_name}")
            return conn, "mysql"
        except Exception as e:
            print(f"Could not connect to MySQL database ({e}). Falling back to local SQLite...")
            
    # Default SQLite Engine
    conn = sqlite3.connect("marketplace.db")
    print("Using local SQLite database: marketplace.db")
    return conn, "sqlite"

# Read schema.sql and create tables
def init_db(conn, db_type):
    if not os.path.exists('schema.sql'):
        raise FileNotFoundError("schema.sql file is missing from the directory.")
        
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()

    cursor = conn.cursor()
    if db_type == "mysql":
        statements = schema_sql.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
        print("MySQL database schema initialized successfully.")
    else:
        # SQLite setup using executescript
        sqlite_schema = translate_mysql_to_sqlite(schema_sql)
        cursor.executescript(sqlite_schema)
        conn.commit()
        print("SQLite database schema initialized successfully.")

# Generate synthetic high-fidelity records
def generate_synthetic_data(num_users=1500, days_window=90):
    random.seed(42)

    # Date configurations (Ending June 25, 2026)
    end_date = datetime.date(2026, 6, 25)
    start_date = end_date - datetime.timedelta(days=days_window - 1)
    print(f"Generating synthetic traffic from {start_date} to {end_date} ({days_window} days)...")

    # Dimensions
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Ahmedabad', 'Chennai', 'Kolkata', 'Pune']
    city_weights = [0.25, 0.20, 0.20, 0.12, 0.10, 0.05, 0.05, 0.03]
    
    channels = ['Meta_Ads', 'Google_Ads', 'Organic', 'Referral']
    channel_weights = [0.30, 0.30, 0.25, 0.15]

    users = []
    experiments = []

    # Assign experiments and metadata upfront
    for user_id in range(1, num_users + 1):
        city = random.choices(cities, weights=city_weights)[0]
        channel = random.choices(channels, weights=channel_weights)[0]
        
        # User signups spread across first 80 days to allow cohort tracking
        signup_offset = random.randint(0, days_window - 11)
        signup_date = start_date + datetime.timedelta(days=signup_offset)
        
        # Split A/B Test Group (50/50 split)
        exp_group = 'Group B (New Checkout)' if user_id % 2 == 0 else 'Group A (Old Checkout)'
        experiments.append({
            'experiment_id': user_id,
            'user_id': user_id,
            'experiment_group': exp_group,
            'feature_name': 'Checkout Optimization',
            'launch_date': start_date
        })

        users.append({
            'user_id': user_id,
            'signup_date': signup_date,
            'city': city,
            'acquisition_channel': channel,
            'user_segment': 'Dormant User', # Recalculated dynamically later
            'exp_group': exp_group
        })

    # Device preference assignments per user
    user_devices = {}
    for u in users:
        pref_device = random.choices(['iOS', 'Android', 'Web'], weights=[0.35, 0.45, 0.20])[0]
        user_devices[u['user_id']] = pref_device

    # Fact & Dimension Lists
    sessions = []
    events = []
    orders = []
    
    session_id_counter = 1
    event_id_counter = 1
    order_id_counter = 1

    # Track distinct session days per user to assign segments
    user_active_days = {u['user_id']: set() for u in users}
    user_orders_count = {u['user_id']: 0 for u in users}

    # Product taxonomy
    product_categories = ['Electronics', 'Fashion', 'Home & Kitchen', 'Beauty & Personal Care', 'Sports & Outdoors']
    product_names = {
        'Electronics': ['Wireless Earbuds', 'Smartphone Case', 'Smart Watch', 'Bluetooth Speaker', 'Charging Cable'],
        'Fashion': ['Running Shoes', 'Denim Jacket', 'Cotton T-Shirt', 'Leather Wallet', 'Sunglasses'],
        'Home & Kitchen': ['Coffee Maker', 'Air Fryer', 'Non-stick Fry Pan', 'Water Bottle', 'Storage Organizer'],
        'Beauty & Personal Care': ['Sunscreen SPF 50', 'Moisturizer', 'Hair Dryer', 'Face Wash', 'Lip Balm'],
        'Sports & Outdoors': ['Yoga Mat', 'Dumbbell Set', 'Backpack', 'Waterproof Tent', 'Resistance Bands']
    }

    for u in users:
        uid = u['user_id']
        signup_dt = u['signup_date']
        channel = u['acquisition_channel']
        exp_group = u['exp_group']
        pref_device = user_devices[uid]

        # Day 0 session is guaranteed
        session_dates = [signup_dt]

        # Anomaly 2: Channel Retention Decay for Meta Ads
        if channel == 'Meta_Ads':
            # Day 1: ~10% conversion, Day 7: ~3% conversion, other days: ~1.5% conversion
            d1_date = signup_dt + datetime.timedelta(days=1)
            if d1_date <= end_date and random.random() < 0.10:
                session_dates.append(d1_date)
            d7_date = signup_dt + datetime.timedelta(days=7)
            if d7_date <= end_date and random.random() < 0.03:
                session_dates.append(d7_date)
            # Other days
            current_dt = signup_dt + datetime.timedelta(days=2)
            while current_dt <= end_date:
                diff_days = (current_dt - signup_dt).days
                if diff_days != 7 and random.random() < 0.015:
                    session_dates.append(current_dt)
                current_dt += datetime.timedelta(days=1)
        else:
            # Standard channels: Day 1: ~40% conversion, Day 7: ~25% conversion, other days: ~5% conversion
            d1_date = signup_dt + datetime.timedelta(days=1)
            if d1_date <= end_date and random.random() < 0.40:
                session_dates.append(d1_date)
            d7_date = signup_dt + datetime.timedelta(days=7)
            if d7_date <= end_date and random.random() < 0.25:
                session_dates.append(d7_date)
            # Other days
            current_dt = signup_dt + datetime.timedelta(days=2)
            while current_dt <= end_date:
                diff_days = (current_dt - signup_dt).days
                if diff_days != 7 and random.random() < 0.05:
                    session_dates.append(current_dt)
                current_dt += datetime.timedelta(days=1)

        # Remove duplicate dates and sort
        session_dates = sorted(list(set(session_dates)))
        
        # Populate session info and events
        for s_date in session_dates:
            user_active_days[uid].add(s_date)

            # Session device: 90% preferred, 10% alternative
            if random.random() < 0.90:
                s_device = pref_device
            else:
                s_device = random.choice([d for d in ['iOS', 'Android', 'Web'] if d != pref_device])

            # Session Start time configuration
            start_hour = random.randint(7, 23)
            start_minute = random.randint(0, 59)
            start_second = random.randint(0, 59)
            session_time = datetime.datetime.combine(
                s_date, 
                datetime.time(start_hour, start_minute, start_second)
            )

            # Coupon application feature (20% chance)
            coupon_applied = 1 if random.random() < 0.20 else 0

            session_dict = {
                'session_id': session_id_counter,
                'user_id': uid,
                'session_duration': 0, # computed from events
                'device_type': s_device,
                'session_date': s_date,
                'discount_coupon_applied': coupon_applied
            }
            sessions.append(session_dict)

            # Events generation flow
            curr_time = session_time
            session_events = []

            # 1. App Open (Always)
            session_events.append({
                'event_id': event_id_counter,
                'user_id': uid,
                'session_id': session_id_counter,
                'event_type': 'App Open',
                'feature_name': 'Homepage',
                'timestamp': curr_time
            })
            event_id_counter += 1

            # 2. Search (90% transition)
            searched = random.random() < 0.90
            category = random.choice(product_categories)
            if searched:
                curr_time += datetime.timedelta(seconds=random.randint(15, 60))
                session_events.append({
                    'event_id': event_id_counter,
                    'user_id': uid,
                    'session_id': session_id_counter,
                    'event_type': 'Search',
                    'feature_name': f"Search Category: {category}",
                    'timestamp': curr_time
                })
                event_id_counter += 1
                
                # 3. View Product (85% transition)
                viewed = random.random() < 0.85
                if viewed:
                    num_views = random.randint(1, 4)
                    for _ in range(num_views):
                        curr_time += datetime.timedelta(seconds=random.randint(20, 90))
                        p_name = random.choice(product_names[category])
                        session_events.append({
                            'event_id': event_id_counter,
                            'user_id': uid,
                            'session_id': session_id_counter,
                            'event_type': 'View Product',
                            'feature_name': p_name,
                            'timestamp': curr_time
                        })
                        event_id_counter += 1

                    # 4. Add To Cart (60% transition)
                    added = random.random() < 0.60
                    if added:
                        num_adds = random.randint(1, min(num_views, 3))
                        added_products = random.sample(product_names[category], min(num_adds, len(product_names[category])))
                        for p_name in added_products:
                            curr_time += datetime.timedelta(seconds=random.randint(15, 60))
                            session_events.append({
                                'event_id': event_id_counter,
                                'user_id': uid,
                                'session_id': session_id_counter,
                                'event_type': 'Add To Cart',
                                'feature_name': p_name,
                                'timestamp': curr_time
                            })
                            event_id_counter += 1

                        # 5. Checkout
                        # Anomaly 1: iOS device layout leakage (45% vs 70%)
                        past_purchases = user_orders_count[uid]
                        
                        # Deterministic score based on features (coupon, views, past purchases)
                        feat_score = (0.6 * coupon_applied) + (0.4 * min(2, past_purchases)) + (0.2 * min(4, num_views))
                        
                        # iOS threshold is 0.8, Android/Web is 0.3
                        checkout_threshold = 0.8 if s_device == 'iOS' else 0.3
                        # Add a small random noise to simulate marginal users
                        checkout_success = (feat_score + random.uniform(-0.15, 0.15)) >= checkout_threshold
                        
                        if checkout_success:
                            curr_time += datetime.timedelta(seconds=random.randint(30, 120))
                            session_events.append({
                                'event_id': event_id_counter,
                                'user_id': uid,
                                'session_id': session_id_counter,
                                'event_type': 'Checkout',
                                'feature_name': 'Checkout Page',
                                'timestamp': curr_time
                            })
                            event_id_counter += 1

                            # 6. Purchase
                            # Anomaly 3: Experiment group checkout lift (Group B conversion lift)
                            purchase_threshold = 0.35 if exp_group == 'Group B (New Checkout)' else 0.45
                            purchased = (feat_score + random.uniform(-0.15, 0.15)) >= purchase_threshold
                            
                            if purchased:
                                curr_time += datetime.timedelta(seconds=random.randint(15, 60))
                                session_events.append({
                                    'event_id': event_id_counter,
                                    'user_id': uid,
                                    'session_id': session_id_counter,
                                    'event_type': 'Purchase',
                                    'feature_name': 'Order Confirmation',
                                    'timestamp': curr_time
                                })
                                event_id_counter += 1
                                
                                # Order creation
                                order_amount = round(random.uniform(20.0, 450.0), 2)
                                orders.append({
                                    'order_id': order_id_counter,
                                    'user_id': uid,
                                    'session_id': session_id_counter,
                                    'amount': order_amount,
                                    'category': category,
                                    'order_date': s_date
                                })
                                order_id_counter += 1
                                
                                # Update dynamic order count for future sessions
                                user_orders_count[uid] += 1

            events.extend(session_events)

            # Set the exact duration of the session
            if len(session_events) > 1:
                duration_sec = int((session_events[-1]['timestamp'] - session_events[0]['timestamp']).total_seconds())
            else:
                duration_sec = random.randint(5, 30)
            session_dict['session_duration'] = duration_sec
            
            session_id_counter += 1

    # Segment users dynamically based on signup and activity days
    new_user_cutoff = end_date - datetime.timedelta(days=14)
    for u in users:
        uid = u['user_id']
        signup_dt = u['signup_date']
        active_days_count = len(user_active_days[uid])
        
        if signup_dt >= new_user_cutoff:
            u['user_segment'] = 'New User'
        elif active_days_count >= 3:
            u['user_segment'] = 'Repeat User'
        else:
            u['user_segment'] = 'Dormant User'

        # Remove helper exp_group key
        u.pop('exp_group', None)

    return users, experiments, sessions, events, orders

# Write to Database using standard SQL executemany (dependency-free)
def save_data_to_db(conn, db_type, users, experiments, sessions, events, orders):
    print(f"Writing generated arrays to database: {len(users)} users, {len(sessions)} sessions, {len(events)} events, {len(orders)} orders.")
    
    cursor = conn.cursor()
    place_holder = "?" if db_type == "sqlite" else "%s"

    # 1. Users
    cursor.executemany(f"""
        INSERT INTO users (user_id, signup_date, city, acquisition_channel, user_segment)
        VALUES ({place_holder}, {place_holder}, {place_holder}, {place_holder}, {place_holder})
    """, [
        (u['user_id'], u['signup_date'].isoformat(), u['city'], u['acquisition_channel'], u['user_segment'])
        for u in users
    ])

    # 2. Experiments
    cursor.executemany(f"""
        INSERT INTO experiments (experiment_id, user_id, experiment_group, feature_name, launch_date)
        VALUES ({place_holder}, {place_holder}, {place_holder}, {place_holder}, {place_holder})
    """, [
        (e['experiment_id'], e['user_id'], e['experiment_group'], e['feature_name'], e['launch_date'].isoformat())
        for e in experiments
    ])

    # 3. Sessions
    cursor.executemany(f"""
        INSERT INTO sessions (session_id, user_id, session_duration, device_type, session_date, discount_coupon_applied)
        VALUES ({place_holder}, {place_holder}, {place_holder}, {place_holder}, {place_holder}, {place_holder})
    """, [
        (s['session_id'], s['user_id'], s['session_duration'], s['device_type'], s['session_date'].isoformat(), s['discount_coupon_applied'])
        for s in sessions
    ])

    # 4. Events
    cursor.executemany(f"""
        INSERT INTO events (event_id, user_id, session_id, event_type, feature_name, timestamp)
        VALUES ({place_holder}, {place_holder}, {place_holder}, {place_holder}, {place_holder}, {place_holder})
    """, [
        (ev['event_id'], ev['user_id'], ev['session_id'], ev['event_type'], ev['feature_name'], ev['timestamp'].strftime('%Y-%m-%d %H:%M:%S'))
        for ev in events
    ])

    # 5. Orders
    cursor.executemany(f"""
        INSERT INTO orders (order_id, user_id, session_id, amount, category, order_date)
        VALUES ({place_holder}, {place_holder}, {place_holder}, {place_holder}, {place_holder}, {place_holder})
    """, [
        (o['order_id'], o['user_id'], o['session_id'], o['amount'], o['category'], o['order_date'].isoformat())
        for o in orders
    ])

    conn.commit()
    print("Database populate completed successfully.")

# Run database validation queries and print anomalies
def run_validation_checks(conn, db_type):
    print("\n" + "="*40)
    print("      DATABASE METRIC VALIDATIONS")
    print("="*40)
    
    cursor = conn.cursor()

    # Table counts
    print("\n[Count Validation] Row counts per table:")
    for tbl in ['users', 'experiments', 'sessions', 'events', 'orders']:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cursor.fetchone()[0]
        print(f"  - {tbl}: {cnt}")

    # Anomaly 1 Check: iOS Funnel Leakage (Add To Cart -> Checkout)
    print("\n[Anomaly 1 Validation] iOS device leakage checkout conversion:")
    cursor.execute("""
        SELECT 
            s.device_type,
            COUNT(DISTINCT CASE WHEN e.event_type = 'Add To Cart' THEN s.session_id END) as cart_sessions,
            COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.session_id END) as checkout_sessions,
            (1.0 * COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.session_id END) / 
             NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'Add To Cart' THEN s.session_id END), 0)) * 100 as transition_rate_pct
        FROM sessions s
        JOIN events e ON s.session_id = e.session_id
        GROUP BY s.device_type
    """)
    res_device = cursor.fetchall()
    for row in res_device:
        print(f"  - {row[0]}: {row[1]} carts -> {row[2]} checkouts ({row[3]:.2f}% conversion)")

    # Anomaly 2 Check: Meta Ads Retention Decay and Dormant classification
    print("\n[Anomaly 2 Validation] D1 and D7 retention by channel:")
    if db_type == 'mysql':
        cursor.execute("""
            SELECT 
                u.acquisition_channel,
                COUNT(DISTINCT u.user_id) as total_users,
                COUNT(DISTINCT CASE WHEN s.session_date = u.signup_date THEN u.user_id END) as d0_users,
                COUNT(DISTINCT CASE WHEN s.session_date = DATE_ADD(u.signup_date, INTERVAL 1 DAY) THEN u.user_id END) as d1_users,
                COUNT(DISTINCT CASE WHEN s.session_date = DATE_ADD(u.signup_date, INTERVAL 7 DAY) THEN u.user_id END) as d7_users
            FROM users u
            LEFT JOIN sessions s ON u.user_id = s.user_id
            GROUP BY u.acquisition_channel
        """)
    else:
        cursor.execute("""
            SELECT 
                u.acquisition_channel,
                COUNT(DISTINCT u.user_id) as total_users,
                COUNT(DISTINCT CASE WHEN s.session_date = u.signup_date THEN u.user_id END) as d0_users,
                COUNT(DISTINCT CASE WHEN s.session_date = DATE(u.signup_date, '+1 day') THEN u.user_id END) as d1_users,
                COUNT(DISTINCT CASE WHEN s.session_date = DATE(u.signup_date, '+7 day') THEN u.user_id END) as d7_users
            FROM users u
            LEFT JOIN sessions s ON u.user_id = s.user_id
            GROUP BY u.acquisition_channel
        """)
    res_ret = cursor.fetchall()
    for row in res_ret:
        d1_pct = (row[3] / row[1] * 100) if row[1] > 0 else 0
        d7_pct = (row[4] / row[1] * 100) if row[1] > 0 else 0
        print(f"  - {row[0]}: Total Users: {row[1]} | Day 1: {row[3]} ({d1_pct:.2f}%) | Day 7: {row[4]} ({d7_pct:.2f}%)")

    print("\n[Anomaly 2 Segment Verification] User Segment split by channel:")
    cursor.execute("""
        SELECT acquisition_channel, user_segment, COUNT(*) as cnt
        FROM users
        GROUP BY acquisition_channel, user_segment
        ORDER BY acquisition_channel, user_segment
    """)
    res_seg = cursor.fetchall()
    for row in res_seg:
        print(f"  - {row[0]} | Segment: {row[1]} | Count: {row[2]}")

    # Anomaly 3 Check: Experiment Lift
    print("\n[Anomaly 3 Validation] Experiment Checkout-to-Purchase conversion:")
    cursor.execute("""
        SELECT 
            ex.experiment_group,
            COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.session_id END) as checkout_sessions,
            COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.session_id END) as purchase_sessions,
            (1.0 * COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.session_id END) / 
             NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.session_id END), 0)) * 100 as conversion_rate_pct
        FROM sessions s
        JOIN events e ON s.session_id = e.session_id
        JOIN experiments ex ON s.user_id = ex.user_id
        GROUP BY ex.experiment_group
    """)
    res_exp = cursor.fetchall()
    for row in res_exp:
        print(f"  - {row[0]}: {row[1]} checkouts -> {row[2]} purchases ({row[3]:.2f}% conversion)")

def main():
    load_env()
    conn, db_type = get_db_connection()
    try:
        init_db(conn, db_type)
        
        # Generate data
        users, experiments, sessions, events, orders = generate_synthetic_data(num_users=1500, days_window=90)
        
        # Save to database
        save_data_to_db(conn, db_type, users, experiments, sessions, events, orders)
        
        # Run validation check queries
        run_validation_checks(conn, db_type)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
