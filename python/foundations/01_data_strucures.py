from faker import Faker
import random
import time
from datetime import datetime, timedelta

fake = Faker()

# --- Generate fake orders with intentional duplicates ---
def generate_orders(total=10000, unique_count=6000):
    unique_orders = [
        {
            "order_id": fake.uuid4(),
            "customer_id": fake.random_int(min=1, max=1000),
            "amount": round(random.uniform(10.0, 500.0), 2),
            "status": random.choice(["pending", "shipped", "delivered"])
        }
        for _ in range(unique_count)
    ]
    # Simulate duplicates by randomly repeating orders
    orders = unique_orders + random.choices(unique_orders, k=total - unique_count)
    random.shuffle(orders)
    return orders


orders = generate_orders()

# Step 1: Deduplicate orders by order_id
unique_orders = {}
duplicate_count = 0
for order in orders:
    order_id = order["order_id"]
    if order_id in unique_orders:
        duplicate_count += 1
    # Always overwrite — last record wins (useful for CDC patterns later)
    unique_orders[order_id] = order
# Step 2: Track how many duplicates were caught (already done in the loop)
# Step 3: Print the required information
total_records = len(orders)
unique_count = len(unique_orders)
duplicate_rate = (duplicate_count / total_records) * 100
print(f"Total records received: {total_records}")
print(f"Unique orders: {unique_count}")
print(f"Duplicate count: {duplicate_count}")
print(f"% duplicate rate: {duplicate_rate:.2f}%")


# # --- Data Setup ---
# # A catalog of 50,000 products
# catalog = [
#     {
#         "product_id": i,
#         "product_name": fake.bs(),
#         "price": round(random.uniform(1.0, 999.0), 2)
#     }
#     for i in range(50_000)
# ]
#
# # 100,000 incoming order line items
# order_lines = [
#     {
#         "order_line_id": fake.uuid4(),
#         "product_id": random.randint(0, 49_999),
#         "quantity": random.randint(1, 10)
#     }
#     for _ in range(100_000)
# ]
#
#
# # --- APPROACH 1: Naive list scan ---
# # For each order line, loop through catalog to find the product
# # YOUR CODE HERE
# # Note: This is O(n*m) where n = number of order lines and m = number of products in catalog
#
# # APPROACH 1: Naive List Scan
# start_time = time.time()
#
# enriched_order_lines = []
#
# for order_line in order_lines:
#     product_id = order_line["product_id"]
#
#     # Naive search: loop through entire catalog
#     for product in catalog:
#         if product["product_id"] == product_id:
#             order_line["product_name"] = product["product_name"]
#             order_line["price"] = product["price"]
#             break
#
#     enriched_order_lines.append(order_line)
#
# end_time = time.time()
# execution_time = end_time - start_time
#
# print(f"Approach 1 (Naive Scan) - Execution Time: {execution_time:.4f} seconds")
# print(f"Sample enriched order line: {enriched_order_lines[0]}")
#
# # --- APPROACH 2: Hash map pre-index ---
# # Pre-build a dict from the catalog, then do O(1) lookups
# start_time_2 = time.time()
#
# # Step 1: Pre-build a dictionary (hash map) indexed by product_id
# product_index = {}
# for product in catalog:
#     product_index[product["product_id"]] = product
#
# # Step 2: Use O(1) dictionary lookup instead of looping through catalog
# enriched_order_lines_2 = []
# for order_line in order_lines:
#     product_id = order_line["product_id"]
#
#     # O(1) lookup: direct access to product via dictionary
#     if product_id in product_index:
#         product = product_index[product_id]
#         order_line["product_name"] = product["product_name"]
#         order_line["price"] = product["price"]
#
#     enriched_order_lines_2.append(order_line)
#
# end_time_2 = time.time()
# execution_time_2 = end_time_2 - start_time_2
#
# print(f"\nApproach 2 (Hash Map Pre-Index) - Execution Time: {execution_time_2:.4f} seconds")
# print(f"Sample enriched order line: {enriched_order_lines_2[0]}")
#
# # --- PERFORMANCE COMPARISON ---
# print(f"\n{'='*60}")
# print(f"PERFORMANCE COMPARISON")
# print(f"{'='*60}")
# print(f"Approach 1 (Naive Scan):      {execution_time:.4f} seconds")
# print(f"Approach 2 (Hash Map Index):  {execution_time_2:.4f} seconds")
# if execution_time_2 > 0:
#     speedup = execution_time / execution_time_2
#     print(f"Speedup:                      {speedup:.2f}x faster with Approach 2")
#     print(f"Time saved:                   {execution_time - execution_time_2:.4f} seconds")
# print(f"{'='*60}")


# --- Generate clickstream events ---
# --- Helper: get index of first occurrence ---
def generate_clickstream(num_users=1000, events_per_user=10):
    event_types = ["page_view", "add_to_cart", "purchase", "wishlist", "search"]
    events = []
    base_time = datetime(2024, 1, 1, 9, 0, 0)

    for user_num in range(num_users):
        user_id = f"user_{user_num}"
        for j in range(events_per_user):
            events.append({
                "user_id": user_id,
                "event_type": random.choice(event_types),
                "timestamp": base_time + timedelta(minutes=random.randint(0, 1440))
            })

    random.shuffle(events)
    return events


events = generate_clickstream()


# --- Helper: get index of first occurrence ---
def get_first_index(event_types_list, event_name):
    try:
        return event_types_list.index(event_name)
    except ValueError:
        return -1


# --- Group events by user_id ---
user_events_map = {}
for event in events:
    uid = event["user_id"]
    if uid not in user_events_map:
        user_events_map[uid] = []
    user_events_map[uid].append(event)


# --- Classify each user ---
converter_count = 0
abandoned_cart_count = 0
other_count = 0

for user, user_events in user_events_map.items():
    # Sort by timestamp — ORDER MATTERS
    user_events.sort(key=lambda x: x["timestamp"])
    event_types_list = [e["event_type"] for e in user_events]

    pv_idx  = get_first_index(event_types_list, "page_view")
    atc_idx = get_first_index(event_types_list, "add_to_cart")
    pur_idx = get_first_index(event_types_list, "purchase")

    # Sequence must be strictly ordered
    if pv_idx != -1 and atc_idx > pv_idx and pur_idx > atc_idx:
        converter_count += 1
    elif pv_idx != -1 and atc_idx > pv_idx and pur_idx == -1:
        abandoned_cart_count += 1
    else:
        other_count += 1


# --- Results ---
total_users = len(user_events_map)
print(f"Total users:       {total_users}")
print(f"Converters:        {converter_count}")
print(f"Abandoned carts:   {abandoned_cart_count}")
print(f"Other:             {other_count}")