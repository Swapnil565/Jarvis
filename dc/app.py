from flask import Flask, request, jsonify
import requests
from datetime import datetime
import sys

app = Flask(__name__)

# CONFIGURE THIS FOR EACH SERVER
# Server 1: SERVER_ID='1', PORT=5001
# Server 2: SERVER_ID='2', PORT=5002
# Server 3: SERVER_ID='3', PORT=5003

SERVER_ID = sys.argv[1] if len(sys.argv) > 1 else '1'
PORT = 5000 + int(SERVER_ID)

# REPLACE WITH YOUR ACTUAL AWS EC2 PUBLIC IPs
# Modified for local execution
SERVERS = {
    '1': 'http://127.0.0.1:5001',
    '2': 'http://127.0.0.1:5002',
    '3': 'http://127.0.0.1:5003'
}

# In-memory database
database = {
    'trains': {
        'T101': {'name': 'Mumbai Express', 'available_seats': 50},
        'T102': {'name': 'Delhi Rajdhani', 'available_seats': 30}
    },
    'bookings': []
}

def log(msg):
    print(f"[SERVER {SERVER_ID}] [{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

@app.route('/')
def home():
    return jsonify({
        'server_id': SERVER_ID,
        'status': 'RUNNING',
        'trains': database['trains'],
        'bookings': len(database['bookings'])
    })

@app.route('/check/<train_id>')
def check(train_id):
    log(f"CHECK availability for {train_id}")
    if train_id in database['trains']:
        seats = database['trains'][train_id]['available_seats']
        log(f"Available seats: {seats}")
        return jsonify({
            'server_id': SERVER_ID,
            'train_id': train_id,
            'available_seats': seats
        })
    return jsonify({'error': 'Train not found'}), 404

@app.route('/book', methods=['POST'])
def book():
    data = request.json
    train_id = data['train_id']
    seats = data['seats']
    passenger = data['passenger']
    
    log(f"BOOK REQUEST: {seats} seats on {train_id} for {passenger}")
    
    if train_id not in database['trains']:
        return jsonify({'error': 'Train not found'}), 404
    
    available = database['trains'][train_id]['available_seats']
    log(f"Current seats: {available}")
    
    if available < seats:
        log("REJECTED: Not enough seats")
        return jsonify({'error': 'Not enough seats'}), 400
    
    # Replicate to other servers
    log("Sending to other servers for consensus...")
    votes = 1  # self vote
    
    for sid, url in SERVERS.items():
        if sid != SERVER_ID:
            try:
                r = requests.post(f"{url}/replicate", 
                    json={'op': 'book', 'train_id': train_id, 
                          'seats': seats, 'passenger': passenger},
                    timeout=3)
                if r.status_code == 200:
                    votes += 1
                    log(f"Server {sid}: YES")
            except:
                log(f"Server {sid}: NO RESPONSE")
    
    log(f"VOTES: {votes}/3")
    
    if votes >= 2:
        # Commit
        database['trains'][train_id]['available_seats'] -= seats
        bid = f"BK{len(database['bookings'])+1:03d}"
        database['bookings'].append({
            'id': bid, 'train': train_id, 
            'passenger': passenger, 'seats': seats
        })
        new_seats = database['trains'][train_id]['available_seats']
        log(f"SUCCESS: {bid} confirmed | Seats remaining: {new_seats}")
        
        return jsonify({
            'status': 'SUCCESS',
            'booking_id': bid,
            'replicated': f'{votes}/3 servers'
        })
    else:
        log("FAILED: No consensus")
        return jsonify({'error': 'Replication failed'}), 500

@app.route('/replicate', methods=['POST'])
def replicate():
    data = request.json
    log(f"Replication request received")
    
    train_id = data['train_id']
    seats = data['seats']
    
    if database['trains'][train_id]['available_seats'] >= seats:
        database['trains'][train_id]['available_seats'] -= seats
        bid = f"BK{len(database['bookings'])+1:03d}"
        database['bookings'].append({
            'id': bid, 'train': train_id,
            'passenger': data['passenger'], 'seats': seats
        })
        log(f"Replicated: New seats = {database['trains'][train_id]['available_seats']}")
        return jsonify({'status': 'ok'})
    
    log("Replication REJECTED")
    return jsonify({'status': 'rejected'}), 400

@app.route('/bookings')
def bookings():
    return jsonify({
        'server_id': SERVER_ID,
        'bookings': database['bookings']
    })

if __name__ == '__main__':
    log(f"Starting Railway Reservation Server...")
    log(f"Port: {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
