import os
import sys
import traceback

# Ensure project root directory is on sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app import app as flask_app
    app = flask_app
except Exception as e:
    tb = traceback.format_exc()
    print("FATAL STARTUP ERROR IN FLASK APP:\n" + tb)
    from flask import Flask, Response
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Startup Error - ClauseEase</title></head>
        <body style="font-family: sans-serif; padding: 2rem; background: #fff5f5; color: #991b1b;">
            <h2>⚠️ Application Startup Error</h2>
            <p>The application encountered an error while starting up on Vercel:</p>
            <pre style="background: #1e1e1e; color: #f87171; padding: 1rem; border-radius: 8px; overflow-x: auto;">{tb}</pre>
        </body>
        </html>
        """
        return Response(html, status=500, mimetype="text/html")
