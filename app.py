from flask import Flask, jsonify
import threading
import time
import subprocess
import os

app = Flask(__name__)

# Global variable to track bot status
bot_status = "not running"
bot_process = None

def run_bot():
    """Run the SMS bot in a separate process"""
    global bot_status, bot_process
    try:
        bot_status = "starting"
        # Run the bot script using subprocess
        bot_process = subprocess.Popen(["python", "sms_hadi.py"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
        bot_status = "running"
        
        # Wait for the process to complete
        stdout, stderr = bot_process.communicate()
        
        if bot_process.returncode == 0:
            bot_status = "completed successfully"
        else:
            bot_status = f"failed with error: {stderr.decode()}"
            
    except Exception as e:
        bot_status = f"crashed: {str(e)}"

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": bot_status,
        "message": "SMS Bot Flask Server is running"
    })

@app.route('/start')
def start_bot():
    global bot_process, bot_status
    
    if bot_process and bot_process.poll() is None:
        return jsonify({"status": "already running", "bot": bot_status})
    
    # Start the bot in a separate thread
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "starting", "bot": bot_status})

@app.route('/status')
def status():
    return jsonify({"status": "online", "bot": bot_status})

if __name__ == '__main__':
    # Start the bot automatically when deployed
    if os.environ.get('RENDER'):
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
    
    app.run(host='0.0.0.0', port=5000)
