import duckdb

con = duckdb.connect('data/cms.db')

# Create clean provider table (corrected for 2024 column names)
con.execute("DROP TABLE IF EXISTS providers_clean")
con.execute("""
    CREATE TABLE providers_clean AS
    SELECT
        Rndrng_NPI                                          AS npi,
        Rndrng_Prvdr_Last_Org_Name                          AS provider_name,
        Rndrng_Prvdr_State_Abrvtn                           AS state,
        Rndrng_Prvdr_Type                                   AS specialty,
        Rndrng_Prvdr_City                                   AS city,
        HCPCS_Cd                                            AS hcpcs_code,
        HCPCS_Desc                                          AS procedure_desc,
        Place_Of_Srvc                                       AS place_of_service,
        CAST(Tot_Srvcs AS DOUBLE)                           AS total_services,
        CAST(Tot_Benes AS DOUBLE)                           AS total_beneficiaries,
        CAST(Avg_Sbmtd_Chrg AS DOUBLE)                     AS avg_submitted_charge,
        CAST(Avg_Mdcr_Alowd_Amt AS DOUBLE)                 AS avg_allowed_per_svc,
        CAST(Avg_Mdcr_Pymt_Amt AS DOUBLE)                  AS avg_medicare_payment,

        -- Total allowed (reconstruct from avg x volume)
        CAST(Avg_Mdcr_Alowd_Amt AS DOUBLE) *
            CAST(Tot_Srvcs AS DOUBLE)                       AS total_allowed_amt,

        -- Billing markup ratio
        CAST(Avg_Sbmtd_Chrg AS DOUBLE) /
            NULLIF(CAST(Avg_Mdcr_Alowd_Amt AS DOUBLE), 0)  AS charge_to_allowed_ratio

    FROM provider_svc
    WHERE
        Tot_Srvcs IS NOT NULL
        AND Avg_Mdcr_Alowd_Amt IS NOT NULL
        AND CAST(Tot_Srvcs AS DOUBLE) > 0
        AND CAST(Avg_Mdcr_Alowd_Amt AS DOUBLE) > 0
        AND Rndrng_Prvdr_State_Abrvtn IN (
            'AL','AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID',
            'IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO',
            'MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA',
            'RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
        )
""")

print("providers_clean created.")

# Top 15 procedures by national volume
top_procedures = con.execute("""
    SELECT
        hcpcs_code,
        procedure_desc,
        SUM(total_services)                     AS national_volume,
        ROUND(AVG(avg_allowed_per_svc), 2)      AS avg_allowed
    FROM providers_clean
    GROUP BY hcpcs_code, procedure_desc
    ORDER BY national_volume DESC
    LIMIT 15
""").fetchdf()

print("\nTop 15 procedures by national volume:")
print(top_procedures.to_string(index=False))

# Create geo benchmark table
con.execute("DROP TABLE IF EXISTS state_benchmarks")
con.execute("""
    CREATE TABLE state_benchmarks AS
    SELECT
        Rndrng_Prvdr_Geo_Desc       AS state_name,
        Rndrng_Prvdr_Geo_Lvl        AS geo_level,
        HCPCS_Cd                    AS hcpcs_code,
        Place_Of_Srvc               AS place_of_service,
        CAST(Avg_Mdcr_Alowd_Amt AS DOUBLE)  AS state_avg_allowed,
        CAST(Avg_Mdcr_Pymt_Amt AS DOUBLE)   AS state_avg_payment,
        CAST(Avg_Sbmtd_Chrg AS DOUBLE)      AS state_avg_charge,
        CAST(Tot_Srvcs AS DOUBLE)           AS state_total_services
    FROM geo_svc
    WHERE
        Rndrng_Prvdr_Geo_Lvl = 'State'
        AND Avg_Mdcr_Alowd_Amt IS NOT NULL
""")
print("state_benchmarks created.")

# Export final clean CSV for Excel + Tableau
con.execute("""
    COPY (
        WITH state_map AS (
            SELECT abbrev, full_name FROM (VALUES
                ('AL','Alabama'),('AK','Alaska'),('AZ','Arizona'),('AR','Arkansas'),
                ('CA','California'),('CO','Colorado'),('CT','Connecticut'),('DE','Delaware'),
                ('DC','District of Columbia'),('FL','Florida'),('GA','Georgia'),('HI','Hawaii'),
                ('ID','Idaho'),('IL','Illinois'),('IN','Indiana'),('IA','Iowa'),
                ('KS','Kansas'),('KY','Kentucky'),('LA','Louisiana'),('ME','Maine'),
                ('MD','Maryland'),('MA','Massachusetts'),('MI','Michigan'),('MN','Minnesota'),
                ('MS','Mississippi'),('MO','Missouri'),('MT','Montana'),('NE','Nebraska'),
                ('NV','Nevada'),('NH','New Hampshire'),('NJ','New Jersey'),('NM','New Mexico'),
                ('NY','New York'),('NC','North Carolina'),('ND','North Dakota'),('OH','Ohio'),
                ('OK','Oklahoma'),('OR','Oregon'),('PA','Pennsylvania'),('RI','Rhode Island'),
                ('SC','South Carolina'),('SD','South Dakota'),('TN','Tennessee'),('TX','Texas'),
                ('UT','Utah'),('VT','Vermont'),('VA','Virginia'),('WA','Washington'),
                ('WV','West Virginia'),('WI','Wisconsin'),('WY','Wyoming')
            ) t(abbrev, full_name)
        )
        SELECT
            p.npi,
            p.provider_name,
            p.city,
            p.state,
            sm.full_name                                                AS state_full,
            p.specialty,
            p.hcpcs_code,
            p.procedure_desc,
            p.place_of_service,
            p.total_services,
            p.total_beneficiaries,
            p.avg_submitted_charge,
            p.avg_allowed_per_svc,
            p.avg_medicare_payment,
            p.total_allowed_amt,
            p.charge_to_allowed_ratio,
            b.state_avg_allowed,
            b.state_avg_charge,
            b.state_total_services,
            ROUND(p.avg_allowed_per_svc / NULLIF(b.state_avg_allowed, 0), 3)    AS cost_index,
            ROUND((p.avg_allowed_per_svc - b.state_avg_allowed)
                / NULLIF(b.state_avg_allowed, 0) * 100, 1)                      AS pct_vs_state,
            CASE
                WHEN p.charge_to_allowed_ratio > 5 THEN 'Extreme'
                WHEN p.charge_to_allowed_ratio > 3 THEN 'High'
                WHEN p.charge_to_allowed_ratio > 2 THEN 'Elevated'
                ELSE 'Normal'
            END AS markup_flag
        FROM providers_clean p
        JOIN state_map sm ON p.state = sm.abbrev
        JOIN state_benchmarks b
            ON sm.full_name = b.state_name
            AND p.hcpcs_code = b.hcpcs_code
            AND p.place_of_service = b.place_of_service
        WHERE
            p.total_services >= 50
            AND p.hcpcs_code IN ('99214','99213','97110','36415')
    ) TO 'output/cms_clean_export.csv' (HEADER, DELIMITER ',')
""")

# Confirm export
count = con.execute("SELECT COUNT(*) FROM read_csv_auto('output/cms_clean_export.csv')").fetchone()[0]
print(f"\nExport complete: {count:,} rows written to output/cms_clean_export.csv")