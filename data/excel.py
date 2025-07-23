import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Define the time period
start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 6, 30)
total_days = (end_date - start_date).days + 1

# Number of transactions
num_transactions = 5000

# Generate transaction dates with time
dates = []
for _ in range(num_transactions):
    random_day = start_date + timedelta(days=random.randint(0, total_days - 1))
    # Weekend spikes (Saturday=5, Sunday=6)
    if random_day.weekday() >= 5 and random.random() < 0.6:
        weight = 1.5
    else:
        weight = 1.0
    # Peak hours (5 PM - 8 PM)
    if random.random() < 0.6:
        hour = random.randint(17, 20)
    else:
        hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    transaction_time = random_day.replace(hour=hour, minute=minute, second=second)
    dates.append(transaction_time)

# Seasonality for Indian festivals (10% of transactions during festivals)
festival_periods = [
    (datetime(2024, 11, 1), datetime(2024, 11, 5)),  # Diwali 2024
    (datetime(2025, 3, 14), datetime(2025, 3, 15)),  # Holi 2025
    (datetime(2024, 12, 24), datetime(2024, 12, 26)), # Christmas 2024
    (datetime(2024, 12, 31), datetime(2025, 1, 1)),   # New Year's
]
festival_transactions = int(num_transactions * 0.1) // len(festival_periods)
for festival_start, festival_end in festival_periods:
    festival_days = (festival_end - festival_start).days + 1
    for _ in range(festival_transactions):
        festival_day = festival_start + timedelta(days=random.randint(0, festival_days - 1))
        hour = random.randint(17, 20)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        dates.append(festival_day.replace(hour=hour, minute=minute, second=second))

# Trim and sort dates to maintain 5000 transactions
dates = sorted(dates)[:num_transactions]

# Generate Transaction IDs
transaction_ids = ['T' + str(i).zfill(7) for i in range(1, num_transactions + 1)]

# Generate Customer IDs (700 unique customers, some recurring)
num_customers = 700
customer_ids = [f'C{str(i).zfill(4)}' for i in range(1, num_customers + 1)]
customer_weights = [1.5 if i % 10 == 0 else 1.0 for i in range(num_customers)]  # Some customers more frequent
customer_weights = np.array(customer_weights) / sum(customer_weights)
customer_ids = np.random.choice(customer_ids, size=num_transactions, p=customer_weights)

# Define products and categories
products = {
    'Basmati Rice': ('Groceries', 150, 120),
    'Dairy Milk Chocolate': ('Snacks & Beverages', 50, 40),
    'Dishwashing Liquid': ('Home Essentials', 120, 90),
    'Fresh Milk': ('Dairy & Bakery', 60, 50),
    'Whole Wheat Bread': ('Dairy & Bakery', 40, 32),
    'Coffee Powder': ('Groceries', 200, 160),
    'Toothpaste': ('Personal Care', 100, 80),
    'Shampoo': ('Personal Care', 250, 200),
    'Biscuits': ('Snacks & Beverages', 30, 24),
    'Snack Chips': ('Snacks & Beverages', 20, 15),
    'Soft Drink': ('Snacks & Beverages', 45, 35),
    'Tomato Ketchup': ('Groceries', 130, 100),
    'Spices Mix': ('Groceries', 80, 60),
    'Frozen Peas': ('Frozen Foods', 90, 70),
    'Eggs': ('Dairy & Bakery', 72, 60),
    'Yogurt': ('Dairy & Bakery', 50, 40),
    'Fresh Vegetables': ('Fresh Produce', 60, 45),
    'Fruits': ('Fresh Produce', 100, 75),
}
product_names = list(products.keys())
product_weights = [2.0 if i < 5 else 1.0 if i < 15 else 0.5 for i in range(len(products))]  # High, medium, low sellers
product_weights = np.array(product_weights) / sum(product_weights)

# Generate product data
product_data = np.random.choice(product_names, size=num_transactions, p=product_weights)
categories = [products[p][0] for p in product_data]
sale_prices = [products[p][1] for p in product_data]
cost_prices = [products[p][2] for p in product_data]

# Generate quantities (1-10, normalized probabilities)
quantity_probs = [0.3, 0.25, 0.2, 0.15, 0.05, 0.025, 0.025, 0.01, 0.01, 0.01]
quantity_probs = np.array(quantity_probs) / sum(quantity_probs)  # Normalize to sum to 1
quantities = np.random.choice(range(1, 11), size=num_transactions, p=quantity_probs)

# Introduce trends and outliers
sale_amounts = [sale_prices[i] * quantities[i] for i in range(num_transactions)]
cost_amounts = [cost_prices[i] * quantities[i] for i in range(num_transactions)]
profits = [sale_amounts[i] - cost_amounts[i] for i in range(num_transactions)]

# Apply trends (e.g., 5% annual sales increase)
for i, date in enumerate(dates):
    month_factor = 1 + 0.05 * ((date.year - 2024) + date.month / 12.0)  # Linear trend
    sale_amounts[i] *= month_factor
    cost_amounts[i] *= month_factor
    profits[i] = sale_amounts[i] - cost_amounts[i]

# Introduce outliers (5% of transactions with high/low sales)
outlier_indices = random.sample(range(num_transactions), int(num_transactions * 0.05))
for i in outlier_indices:
    if random.random() < 0.5:
        sale_amounts[i] *= 3  # High sales
    else:
        sale_amounts[i] *= 0.3  # Low sales
    profits[i] = sale_amounts[i] - cost_amounts[i]

# Create DataFrame
data = {
    'Transaction Date': dates,
    'TransactionID': transaction_ids,
    'CustomerID': customer_ids,
    'Product Name': product_data,
    'Category': categories,
    'Quantity': quantities,
    'SaleAmount': [round(x, 2) for x in sale_amounts],
    'CostPrice': [round(x, 2) for x in cost_amounts],
    'Profit': [round(x, 2) for x in profits]
}
df = pd.DataFrame(data)

# Define the path to the Downloads directory (replace <YourUsername> with your actual Windows username)
downloads_path = r"D:\Online Store Order Analysis\insighthub_transactions.xlsx"
downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", "insighthub_transactions.xlsx")

# Save to Excel in Downloads directory
df.to_excel(downloads_path, index=False, engine='openpyxl')

print(f"Excel file saved to: {downloads_path}")