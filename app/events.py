from flask_socketio import emit
from . import socketio
from .models import Bridge

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def broadcast_bridge_update(data):
    """
    Broadcast bridge updates to all connected clients
    """
    socketio.emit('bridge_update', data, broadcast=True)