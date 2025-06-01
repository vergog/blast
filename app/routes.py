from flask import Blueprint, jsonify, request, render_template, current_app
from flask_socketio import emit
from .models import Bridge
from . import db, socketio

main = Blueprint('main', __name__)

@main.route("/map")
def index():
    return render_template("map.html")

@main.route("/table")
def table():
    return render_template("table.html")

@main.route("/api/bridges")
def get_bridges():
    bridges = Bridge.query.all()
    return jsonify([bridge.to_dict() for bridge in bridges])

@main.route("/api/bridges", methods=["POST"])
def create_bridge():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        if not data.get('bin'):
            return jsonify({'error': 'BIN is required'}), 400
            
        # Check if bridge already exists
        existing = Bridge.query.filter_by(bin=data['bin']).first()
        if existing:
            return jsonify({'error': 'Bridge already exists'}), 409
            
        # Create new bridge
        bridge = Bridge(
            bin=data['bin'],
            region=data.get('region', ''),
            county=data.get('county', ''),
            due=data.get('due', ''),
            completed=data.get('completed', ''),
            week=data.get('week', ''),
            flags=data.get('flags', ''),
            flags_info=data.get('flags_info', ''),
            posting=data.get('posting', ''),
            posting_info=data.get('posting_info', ''),
            access=data.get('access', ''),
            access_info=data.get('access_info', ''),
            spe=data.get('spe', ''),
            stds=data.get('stds', ''),
            field_time=data.get('field_time', ''),
            due_month=data.get('due_month', ''),
            lat=float(data.get('lat', 0)),
            lon=float(data.get('lon', 0)),
            spans=data.get('spans', ''),
            prev_gr=data.get('prev_gr', ''),
            issued=data.get('issued', '')
        )
        
        db.session.add(bridge)
        db.session.commit()
        
        # After successful creation, prepare bridge data for broadcast
        bridge_data = bridge.to_dict()
        print(f"Successfully created bridge {bridge.bin}")
        
        # Emit new_bridge event through Socket.IO
        socketio.emit('new_bridge', bridge_data)
        
        return jsonify(bridge_data), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating bridge: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main.route("/api/bridges/<bin>", methods=["PATCH"])
def update_bridge(bin):
    try:
        bridge = Bridge.query.filter_by(bin=bin).first()
        if not bridge:
            return jsonify({"error": "Bridge not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Type conversion for numeric fields
        if 'lat' in data:
            try:
                data['lat'] = float(data['lat'])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid latitude value"}), 400

        if 'lon' in data:
            try:
                data['lon'] = float(data['lon'])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid longitude value"}), 400

        # Update only valid fields
        for key, value in data.items():
            if hasattr(bridge, key):
                setattr(bridge, key, value)

        db.session.commit()

        # Get updated bridge data
        bridge_data = bridge.to_dict()
        
        # Emit socket event
        socketio.emit('bridge_update', bridge_data)

        return jsonify({
            "message": "Bridge updated successfully",
            "data": bridge_data
        })

    except Exception as e:
        current_app.logger.error(f"Error updating bridge: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@main.route("/api/bridges/<bin>", methods=["GET"])
def get_bridge(bin):
    try:
        bridge = Bridge.query.filter_by(bin=bin).first()
        if not bridge:
            return jsonify({"error": "Bridge not found"}), 404
        
        return jsonify(bridge.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error fetching bridge: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add this to your SocketIO event handlers

@socketio.on('coordinate_update')
def handle_coordinate_update(data):
    # Remove broadcast argument for emit()
    emit('bridge_update', data)

# Add this with your other SocketIO event handlers:

@socketio.on('new_bridge')
def handle_new_bridge(data):
    print('Received new_bridge event:', data)
    emit('new_bridge', data)


