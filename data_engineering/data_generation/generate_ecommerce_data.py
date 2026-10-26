#!/usr/bin/env python3
"""
Generate realistic e-commerce sample data for ETL pipeline practice.

Usage:
    python data_engineering/data_generation/generate_ecommerce_data.py --rows 10000 --output data/raw/

Creates:
    - users.csv (10000 rows)
    - products.csv (500 rows)
    - orders.csv (50000 rows - 5 orders per user avg)
"""
import csv
import argparse
from pathlib import Path
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

def generate_users(num_users, output_dir):
    """Generate user records"""
    output_file = Path(output_dir) / 'users.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {num_users} users...")
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'email', 'name', 'signup_date'])

        seen_emails = set()
        for i in range(num_users):
            user_id = i + 1
            email = fake.unique.email()
            name = fake.name()
            signup_date = fake.date_between(start_date='-3y', end_date='today')

            writer.writerow([user_id, email, name, signup_date])

            if (i + 1) % 5000 == 0:
                print(f"  Generated {i + 1} users...")

    print(f"✓ Saved to {output_file}")

def generate_products(num_products, output_dir):
    """Generate product records"""
    output_file = Path(output_dir) / 'products.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Books', 'Beauty', 'Toys']

    print(f"Generating {num_products} products...")
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['product_id', 'name', 'price', 'category'])

        for i in range(num_products):
            product_id = i + 1
            name = fake.word().title() + ' ' + fake.word()
            price = round(random.uniform(10, 500), 2)
            category = random.choice(categories)

            writer.writerow([product_id, name, price, category])

    print(f"✓ Saved to {output_file}")

def generate_orders(num_orders, num_users, num_products, output_dir):
    """Generate order records"""
    output_file = Path(output_dir) / 'orders.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {num_orders} orders...")
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'user_id', 'product_id', 'order_date', 'quantity', 'total'])

        for i in range(num_orders):
            order_id = i + 1
            user_id = random.randint(1, num_users)
            product_id = random.randint(1, num_products)
            order_date = fake.date_between(start_date='-2y', end_date='today')
            quantity = random.randint(1, 10)
            # Assume products are $10-500, so total is roughly quantity * price
            price = round(random.uniform(10, 500), 2)
            total = round(quantity * price, 2)

            writer.writerow([order_id, user_id, product_id, order_date, quantity, total])

            if (i + 1) % 50000 == 0:
                print(f"  Generated {i + 1} orders...")

    print(f"✓ Saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate e-commerce sample data')
    parser.add_argument('--users', type=int, default=10000, help='Number of users')
    parser.add_argument('--products', type=int, default=500, help='Number of products')
    parser.add_argument('--orders', type=int, default=50000, help='Number of orders')
    parser.add_argument('--output', default='data/raw/', help='Output directory')

    args = parser.parse_args()

    print("Generating e-commerce sample data...")
    print(f"  Users: {args.users}")
    print(f"  Products: {args.products}")
    print(f"  Orders: {args.orders}")
    print()

    generate_users(args.users, args.output)
    generate_products(args.products, args.output)
    generate_orders(args.orders, args.users, args.products, args.output)

    print()
    print("✅ All data generated successfully!")
    print(f"Output directory: {args.output}")

if __name__ == '__main__':
    main()
