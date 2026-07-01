import duckdb

con = duckdb.connect('data/cms.db')

# Summary 1: State-level cost comparison (for Research Q1 — regional variation)
con.execute("""
    COPY (
        SELECT
            state_full,
            hcpcs_code,
            procedure_desc,
            place_of_service,
            COUNT(DISTINCT npi)            AS provider_count,
            SUM(total_services)            AS total_services,
            ROUND(AVG(avg_allowed_per_svc), 2)  AS avg_allowed,
            ROUND(AVG(state_avg_allowed), 2)    AS state_benchmark,
            ROUND(AVG(pct_vs_state), 1)         AS avg_pct_vs_state
        FROM read_csv_auto('output/cms_clean_export.csv')
        GROUP BY state_full, hcpcs_code, procedure_desc, place_of_service
    ) TO 'output/summary_by_state.csv' (HEADER, DELIMITER ',')
""")

# Summary 2: Provider-level anomalies — only the flagged ones (for Research Q2)
con.execute("""
    COPY (
        SELECT *
        FROM read_csv_auto('output/cms_clean_export.csv')
        WHERE markup_flag IN ('Elevated', 'High', 'Extreme')
        ORDER BY charge_to_allowed_ratio DESC
        LIMIT 5000
    ) TO 'output/summary_anomalies.csv' (HEADER, DELIMITER ',')
""")

# Summary 3: Specialty-level efficiency rollup (for Research Q3)
con.execute("""
    COPY (
        SELECT
            specialty,
            hcpcs_code,
            procedure_desc,
            COUNT(DISTINCT npi)               AS provider_count,
            SUM(total_services)               AS total_services,
            ROUND(AVG(cost_index), 3)         AS avg_cost_index,
            ROUND(AVG(charge_to_allowed_ratio), 2) AS avg_markup_ratio
        FROM read_csv_auto('output/cms_clean_export.csv')
        GROUP BY specialty, hcpcs_code, procedure_desc
        HAVING COUNT(DISTINCT npi) >= 20
        ORDER BY avg_cost_index DESC
    ) TO 'output/summary_by_specialty.csv' (HEADER, DELIMITER ',')
""")

print("Three summary files created:")
print(" - output/summary_by_state.csv")
print(" - output/summary_anomalies.csv")
print(" - output/summary_by_specialty.csv")