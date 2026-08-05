# This file contains deliberately unsafe examples for testing FabricLint.
# All credentials and identifiers below are fake.

client_secret = "fake-test-only-secret"

workspace_id = "12345678-1234-1234-1234-123456789012"

sales_df = spark.table("bronze.sales")

local_sales = sales_df.collect()  # fabriclint: ignore FL003
sales_df.coalesce(1).write.mode("overwrite").format("delta").save(
    "Tables/sales"
)
