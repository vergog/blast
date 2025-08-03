from flask import Blueprint, jsonify, request, render_template, current_app, flash, redirect, url_for
from flask_socketio import emit
from werkzeug.utils import secure_filename
import os
from .models import Bridge
from . import db, socketio
from .data_importer import import_bridges_from_excel, clear_bridge_data

main = Blueprint('main', __name__)

@main.route("/map")
def index():
    return render_template("map.html")

@main.route("/table")
def table():
    return render_template("table.html")

@main.route("/table2")
def table2():
    return render_template("table2.html")

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

@main.route("/api/bridges/<bin>", methods=["DELETE"])
def delete_bridge(bin):
    try:
        bridge = Bridge.query.filter_by(bin=bin).first()
        if not bridge:
            return jsonify({'error': 'Bridge not found'}), 404
            
        db.session.delete(bridge)
        db.session.commit()
        
        # Emit socket event to all connected clients
        socketio.emit('bridge_deleted', {'bin': bin})
        
        return jsonify({'message': f'Bridge {bin} deleted successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error deleting bridge: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main.route('/admin/import', methods=['GET', 'POST'])
def import_data():
    """Route for importing bridge data from Excel file"""
    if request.method == 'GET':
        return render_template('admin/import.html')
    
    if request.method == 'POST':
        # Check if file was uploaded
        if 'excel_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['excel_file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            
            try:
                # Clear existing data if requested
                if request.form.get('clear_existing'):
                    clear_result = clear_bridge_data()
                    if not clear_result['success']:
                        flash(f'Error clearing existing data: {clear_result["error"]}', 'error')
                        return redirect(request.url)
                
                # Import data
                result = import_bridges_from_excel(temp_path)
                
                # Clean up temp file
                os.remove(temp_path)
                
                if result['success']:
                    flash(f'Import successful! Imported: {result["imported"]}, Updated: {result["updated"]}, Errors: {result["errors"]}', 'success')
                else:
                    flash(f'Import failed: {result["error"]}', 'error')
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                flash(f'Import error: {str(e)}', 'error')
            
            return redirect(url_for('main.import_data'))
        else:
            flash('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'error')
            return redirect(request.url)

def allowed_file(filename):
    """Check if uploaded file is an allowed Excel file"""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/api/import/status')
def import_status():
    """API endpoint to get current bridge count"""
    count = Bridge.query.count()
    return jsonify({'bridge_count': count})

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

@main.route('/api/debug/bridges')
def debug_bridges():
    """Debug endpoint to see raw bridge data"""
    bridges = Bridge.query.limit(5).all()  # Get first 5 bridges
    debug_data = []
    
    for bridge in bridges:
        debug_data.append({
            'bin': bridge.bin,
            'lat': bridge.lat,
            'lat_type': type(bridge.lat).__name__,
            'lon': bridge.lon,
            'lon_type': type(bridge.lon).__name__,
            'due': bridge.due,
            'county': bridge.county,
            'region': bridge.region
        })
    
    return jsonify({
        'count': Bridge.query.count(),
        'sample_data': debug_data
    })


