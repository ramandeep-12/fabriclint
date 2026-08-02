customer_df = spark.table("bronze.customers")

active_customer_df = customer_df.filter(
    "status = 'active'"
)

active_customer_df.write.format("delta").saveAsTable(
    "silver.customers"
)