import pandas as pd

# Read CSV file
df = pd.read_csv("./SaleData.csv")

# Remove first row if necessary (assuming it contains unwanted data)
df = df.iloc[1:]

# Sort by vendor name
df = df.sort_values(by="Product vendor")

# Initialize variables
current_vendor = None
start_index = 0

# Iterate through the DataFrame by row index
for index in range(len(df)):
    vendor = df.iloc[index]["Product vendor"]

    # If vendor changes, process previous batch
    if current_vendor is not None and vendor != current_vendor:
        # Process and save grouped data
        vendor_df = df.iloc[start_index:index]
        grouped_df = vendor_df.copy()

        # Replace blank values with "Custom Sale"
        grouped_df["Product title"].fillna("Custom Sale", inplace=True)
        grouped_df["Product variant title"].fillna("Custom Sale", inplace=True)

        # Group by Product title & Product variant title
        summary = grouped_df.groupby(["Product title", "Product variant title"], as_index=False).agg({
            "Quantity ordered": "sum",
            "Discounts": "sum",
            "Net sales": "sum"
        })

        summary.to_excel(f"{current_vendor}.xlsx", index=False)
        start_index = index  # Update new batch start

    current_vendor = vendor  # Update current vendor

# Process and save the last batch
vendor_df = df.iloc[start_index:]
grouped_df = vendor_df.copy()

# Replace blank values with "Custom Sale"
grouped_df["Product title"].fillna("Custom Sale", inplace=True)
grouped_df["Product variant title"].fillna("Custom Sale", inplace=True)

# Group by Product title & Product variant title
summary = grouped_df.groupby(["Product title", "Product variant title"], as_index=False).agg({
    "Quantity ordered": "sum",
    "Discounts": "sum",
    "Net sales": "sum"
})

summary.to_excel(f"{current_vendor}.xlsx", index=False)

print("Vendor reports successfully created with grouped transactions.")

