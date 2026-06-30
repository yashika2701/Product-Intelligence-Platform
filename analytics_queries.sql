-- =====================================================================
-- AI-Powered Business & Product Intelligence Platform
-- Phase 2: SQL Analytics Queries (SQLite Dialect)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. FUNNEL ANALYSIS BY DEVICE TYPE
-- Calculates absolute user volumes, drop-offs, and step-to-step 
-- conversion rates across: App Open -> Search -> View Product -> Add To Cart -> Checkout -> Purchase.
-- Grouped by device type to expose the pre-baked iOS checkout layout leakage.
-- ---------------------------------------------------------------------

WITH funnel_base AS (
    SELECT 
        s.device_type,
        COUNT(DISTINCT CASE WHEN e.event_type = 'App Open' THEN s.user_id END) as app_open,
        COUNT(DISTINCT CASE WHEN e.event_type = 'Search' THEN s.user_id END) as search,
        COUNT(DISTINCT CASE WHEN e.event_type = 'View Product' THEN s.user_id END) as view_product,
        COUNT(DISTINCT CASE WHEN e.event_type = 'Add To Cart' THEN s.user_id END) as add_to_cart,
        COUNT(DISTINCT CASE WHEN e.event_type = 'Checkout' THEN s.user_id END) as checkout,
        COUNT(DISTINCT CASE WHEN e.event_type = 'Purchase' THEN s.user_id END) as purchase
    FROM sessions s
    LEFT JOIN events e ON s.session_id = e.session_id
    GROUP BY s.device_type
)
SELECT 
    device_type,
    app_open as app_open_users,
    
    search as search_users,
    ROUND(100.0 * search / NULLIF(app_open, 0), 2) as search_step_conv_pct,
    ROUND(100.0 * (app_open - search) / NULLIF(app_open, 0), 2) as search_step_drop_pct,
    
    view_product as view_product_users,
    ROUND(100.0 * view_product / NULLIF(search, 0), 2) as view_product_step_conv_pct,
    ROUND(100.0 * (search - view_product) / NULLIF(search, 0), 2) as view_product_step_drop_pct,
    
    add_to_cart as add_to_cart_users,
    ROUND(100.0 * add_to_cart / NULLIF(view_product, 0), 2) as add_to_cart_step_conv_pct,
    ROUND(100.0 * (view_product - add_to_cart) / NULLIF(view_product, 0), 2) as add_to_cart_step_drop_pct,
    
    checkout as checkout_users,
    ROUND(100.0 * checkout / NULLIF(add_to_cart, 0), 2) as checkout_step_conv_pct,
    ROUND(100.0 * (add_to_cart - checkout) / NULLIF(add_to_cart, 0), 2) as checkout_step_drop_pct,
    
    purchase as purchase_users,
    ROUND(100.0 * purchase / NULLIF(checkout, 0), 2) as purchase_step_conv_pct,
    ROUND(100.0 * (checkout - purchase) / NULLIF(checkout, 0), 2) as purchase_step_drop_pct,
    
    ROUND(100.0 * purchase / NULLIF(app_open, 0), 2) as overall_conversion_pct
FROM funnel_base;


-- ---------------------------------------------------------------------
-- 2. COHORT RETENTION BY ACQUISITION CHANNEL
-- Calculates Day 1 and Day 7 user retention, grouped by acquisition 
-- channel to isolate and confirm the Meta_Ads retention decay.
-- ---------------------------------------------------------------------

WITH user_signups AS (
    SELECT 
        user_id,
        signup_date,
        acquisition_channel
    FROM users
),
user_sessions AS (
    SELECT DISTINCT
        user_id,
        session_date
    FROM sessions
),
user_retention AS (
    SELECT 
        u.user_id,
        u.acquisition_channel,
        -- Check if user had a session on Day 0 (Signup Date)
        MAX(CASE WHEN s.session_date = u.signup_date THEN 1 ELSE 0 END) as d0_active,
        -- Check if user had a session on Day 1 (Signup Date + 1 Day)
        MAX(CASE WHEN s.session_date = DATE(u.signup_date, '+1 day') THEN 1 ELSE 0 END) as d1_active,
        -- Check if user had a session on Day 7 (Signup Date + 7 Days)
        MAX(CASE WHEN s.session_date = DATE(u.signup_date, '+7 day') THEN 1 ELSE 0 END) as d7_active
    FROM user_signups u
    LEFT JOIN user_sessions s ON u.user_id = s.user_id
    GROUP BY u.user_id, u.acquisition_channel, u.signup_date
)
SELECT 
    acquisition_channel,
    COUNT(user_id) as cohort_size,
    SUM(d0_active) as d0_users,
    SUM(d1_active) as d1_users,
    ROUND(100.0 * SUM(d1_active) / NULLIF(COUNT(user_id), 0), 2) as d1_retention_pct,
    SUM(d7_active) as d7_users,
    ROUND(100.0 * SUM(d7_active) / NULLIF(COUNT(user_id), 0), 2) as d7_retention_pct
FROM user_retention
GROUP BY acquisition_channel;


-- ---------------------------------------------------------------------
-- 3. TOP-LINE MARKETPLACE KPIs
-- Computes executive e-commerce metrics: Total Revenue, Average Order Value (AOV),
-- Overall Conversion Rate, and Cart Abandonment Rate (1 - purchases / add_to_carts).
-- ---------------------------------------------------------------------

WITH order_metrics AS (
    SELECT 
        SUM(amount) as total_revenue,
        AVG(amount) as avg_order_value,
        COUNT(DISTINCT session_id) as total_orders
    FROM orders
),
session_metrics AS (
    SELECT 
        COUNT(DISTINCT session_id) as total_sessions
    FROM sessions
),
funnel_metrics AS (
    SELECT 
        COUNT(DISTINCT CASE WHEN event_type = 'Add To Cart' THEN session_id END) as cart_add_sessions,
        COUNT(DISTINCT CASE WHEN event_type = 'Purchase' THEN session_id END) as purchase_sessions
    FROM events
)
SELECT 
    ROUND(o.total_revenue, 2) as total_revenue_usd,
    ROUND(o.avg_order_value, 2) as average_order_value_usd,
    ROUND(100.0 * o.total_orders / NULLIF(s.total_sessions, 0), 2) as overall_conversion_rate_pct,
    ROUND(100.0 * (1.0 - 1.0 * f.purchase_sessions / NULLIF(f.cart_add_sessions, 0)), 2) as cart_abandonment_rate_pct
FROM order_metrics o
CROSS JOIN session_metrics s
CROSS JOIN funnel_metrics f;
