import db_queries

def test_queries():
    print("=" * 60)
    # 1. KPIs
    print("Testing fetch_business_kpis:")
    kpis = db_queries.fetch_business_kpis()
    for k, v in kpis.items():
        print(f"  {k}: {v}")
        
    print("\n" + "=" * 60)
    # 2. Funnel Data
    print("Testing fetch_funnel_data:")
    df_funnel = db_queries.fetch_funnel_data()
    print(df_funnel.to_string(index=False))
    
    print("\n" + "=" * 60)
    # 3. Retention Data
    print("Testing fetch_retention_data:")
    df_ret = db_queries.fetch_retention_data()
    print(df_ret.to_string(index=False))
    
    print("\n" + "=" * 60)
    # 4. User Segmentation
    print("Testing fetch_user_segmentation:")
    df_seg = db_queries.fetch_user_segmentation()
    print(df_seg.to_string(index=False))
    
    print("\n" + "=" * 60)
    # 5. A/B Test Results
    print("Testing fetch_ab_test_results:")
    df_ab = db_queries.fetch_ab_test_results()
    print(df_ab.to_string(index=False))

if __name__ == "__main__":
    test_queries()
