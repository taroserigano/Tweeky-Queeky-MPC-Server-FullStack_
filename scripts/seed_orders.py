"""Seed sample orders into MongoDB for testing order tracking."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_sync_db
from bson import ObjectId
from datetime import datetime, timedelta

def seed_orders():
    db = get_sync_db()
    
    # Clear existing test orders
    db.orders.delete_many({})
    print("Cleared existing orders")
    
    # Get real products and users
    products = list(db.products.find({}, {'_id':1,'name':1,'price':1,'image':1}).limit(10))
    users = list(db.users.find({}, {'_id':1,'name':1}))
    
    john = next(u for u in users if u['name'] == 'John Doe')
    jane = next(u for u in users if u['name'] == 'Jane Doe')
    
    plist = list(products)
    
    orders = [
        # Order 1: John - Delivered (completed order)
        {
            'user': john['_id'],
            'orderItems': [
                {'name': plist[0]['name'], 'qty': 1, 'image': plist[0].get('image', '/images/sample.jpg'), 'price': plist[0]['price'], 'product': plist[0]['_id']},
                {'name': plist[1]['name'], 'qty': 1, 'image': plist[1].get('image', '/images/sample.jpg'), 'price': plist[1]['price'], 'product': plist[1]['_id']},
            ],
            'shippingAddress': {'address': '123 Main St', 'city': 'New York', 'postalCode': '10001', 'country': 'US'},
            'paymentMethod': 'PayPal',
            'itemsPrice': round(plist[0]['price'] + plist[1]['price'], 2),
            'taxPrice': round((plist[0]['price'] + plist[1]['price']) * 0.1, 2),
            'shippingPrice': 0,
            'totalPrice': round((plist[0]['price'] + plist[1]['price']) * 1.1, 2),
            'isPaid': True,
            'paidAt': datetime.utcnow() - timedelta(days=10),
            'isDelivered': True,
            'deliveredAt': datetime.utcnow() - timedelta(days=3),
            'createdAt': datetime.utcnow() - timedelta(days=12),
            'updatedAt': datetime.utcnow() - timedelta(days=3),
        },
        # Order 2: Jane - Paid, in transit
        {
            'user': jane['_id'],
            'orderItems': [
                {'name': plist[2]['name'], 'qty': 1, 'image': plist[2].get('image', '/images/sample.jpg'), 'price': plist[2]['price'], 'product': plist[2]['_id']},
            ],
            'shippingAddress': {'address': '456 Oak Ave', 'city': 'Los Angeles', 'postalCode': '90001', 'country': 'US'},
            'paymentMethod': 'PayPal',
            'itemsPrice': round(plist[2]['price'], 2),
            'taxPrice': round(plist[2]['price'] * 0.1, 2),
            'shippingPrice': 9.99,
            'totalPrice': round(plist[2]['price'] * 1.1 + 9.99, 2),
            'isPaid': True,
            'paidAt': datetime.utcnow() - timedelta(days=2),
            'isDelivered': False,
            'createdAt': datetime.utcnow() - timedelta(days=3),
            'updatedAt': datetime.utcnow() - timedelta(days=2),
        },
        # Order 3: John - Pending payment
        {
            'user': john['_id'],
            'orderItems': [
                {'name': plist[3]['name'], 'qty': 2, 'image': plist[3].get('image', '/images/sample.jpg'), 'price': plist[3]['price'], 'product': plist[3]['_id']},
                {'name': plist[4]['name'], 'qty': 1, 'image': plist[4].get('image', '/images/sample.jpg'), 'price': plist[4]['price'], 'product': plist[4]['_id']},
            ],
            'shippingAddress': {'address': '789 Pine Dr', 'city': 'Chicago', 'postalCode': '60601', 'country': 'US'},
            'paymentMethod': 'PayPal',
            'itemsPrice': round(plist[3]['price']*2 + plist[4]['price'], 2),
            'taxPrice': round((plist[3]['price']*2 + plist[4]['price']) * 0.1, 2),
            'shippingPrice': 0,
            'totalPrice': round((plist[3]['price']*2 + plist[4]['price']) * 1.1, 2),
            'isPaid': False,
            'isDelivered': False,
            'createdAt': datetime.utcnow() - timedelta(hours=6),
            'updatedAt': datetime.utcnow() - timedelta(hours=6),
        },
    ]
    
    result = db.orders.insert_many(orders)
    ids = [str(oid) for oid in result.inserted_ids]
    print(f"\nSeeded {len(ids)} orders:")
    for i, oid in enumerate(ids):
        order = orders[i]
        status = "Delivered" if order['isDelivered'] else ("Paid/In Transit" if order['isPaid'] else "Pending Payment")
        items = ", ".join(item['name'] for item in order['orderItems'])
        print(f"  [{status}] {oid}")
        print(f"    Items: {items}")
        print(f"    Total: ${order['totalPrice']}")
    
    return ids

if __name__ == "__main__":
    seed_orders()
