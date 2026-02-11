from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llm_brain_api')

# Load environment variables
load_dotenv()

# Import core brain
try:
    import llm_brain
    logger.info("Successfully imported llm_brain")
except ImportError as e:
    logger.error(f"Failed to import llm_brain: {e}")
    sys.exit(1)

# Import new core modules
try:
    from core.traffic_logger import TrafficLogger
    from core.settings_manager import SettingsManager
    traffic_logger = TrafficLogger()
    settings_manager = SettingsManager()
except ImportError as e:
    logger.warning(f"Failed to import core modules: {e}")
    traffic_logger = None
    settings_manager = None

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "ClawBrain API",
        "env": os.getenv("CLAWBRAIN_ENV", "production")
    }), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        message = data.get('message', '')
        sender = data.get('sender', 'unknown')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        logger.info(f"Received message from {sender}: {message[:50]}...")
        
        # Determine complexity based on message content
        # For now, let llm_brain decide internally or default to simple
        # Future enhancement: expose complexity param in API
        
        # Generate response using llm_brain
        # llm_brain.generate_text handles auto-upgrading to AgentLoop if needed
        response = llm_brain.generate_text(message)
        
        logger.info(f"Generated response for {sender}: {response[:50]}...")
        
        return jsonify({
            "response": response,
            "metadata": {
                "processed_by": "ClawBrain v1.0.0"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# --- Traffic & Settings Endpoints ---

@app.route('/api/traffic', methods=['GET'])
def get_traffic_logs():
    if not traffic_logger:
        return jsonify({"error": "Traffic logger not available"}), 503
    
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    logs = traffic_logger.get_recent_traffic(limit, offset)
    return jsonify({"logs": logs}), 200

@app.route('/api/traffic/stats', methods=['GET'])
def get_traffic_stats():
    if not traffic_logger:
        return jsonify({"error": "Traffic logger not available"}), 503
    
    stats = traffic_logger.get_stats()
    return jsonify({"stats": stats}), 200

@app.route('/api/settings', methods=['GET'])
def get_settings():
    if not settings_manager:
        return jsonify({"error": "Settings manager not available"}), 503
        
    keys = settings_manager.get_api_keys()
    return jsonify({"keys": keys}), 200

@app.route('/api/settings', methods=['POST'])
def update_settings():
    if not settings_manager:
        return jsonify({"error": "Settings manager not available"}), 503
        
    data = request.json
    key_name = data.get('name')
    new_value = data.get('value')
    
    if not key_name or not new_value:
        return jsonify({"error": "Missing name or value"}), 400
        
    success = settings_manager.update_api_key(key_name, new_value)
    if success:
        return jsonify({"status": "updated", "message": "Restart required for changes to take effect fully."}), 200
    else:
        return jsonify({"error": "Failed to update setting"}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8001))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting ClawBrain API on port {port} (Debug: {debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
