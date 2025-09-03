from flask import Flask, jsonify
import threading
import time
import os
import sys

app = Flask(__name__)

# Global variable to track bot status
bot_status = "not running"
bot_thread = None

def run_bot():
    """Run the SMS bot"""
    global bot_status
    try:
        bot_status = "running"
        print("Starting SMS bot...")
        
        # Import and run the bot directly
        from sms_hadi import run_sms_bot
        success = run_sms_bot()
        
        if success:
            bot_status = "completed successfully"
        else:
            bot_status = "failed"
            
    except Exception as e:
        bot_status = f"crashed: {str(e)}"
        print(f"Bot error: {e}")

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": bot_status,
        "message": "SMS Bot Flask Server is running"
    })

@app.route('/start')
def start_bot():
    global bot_thread, bot_status
    
    if bot_thread and bot_thread.is_alive():
        return jsonify({"status": "already running", "bot": bot_status})
    
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    return jsonify({"status": "starting", "bot": bot_status})

@app.route('/status')
def status():
    return jsonify({"status": "online", "bot": bot_status})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    # Start the bot automatically when deployed
    if os.environ.get('RENDER'):
        print("Running on Render, starting bot...")
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
