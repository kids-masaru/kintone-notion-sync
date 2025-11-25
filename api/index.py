from flask import Flask, render_template, request, jsonify
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path to import sync_kintone_notion
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync_kintone_notion import run_script_A, run_script_B

app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync', methods=['POST'])
def sync():
    data = request.json
    filter_date = data.get('date')
    
    if not filter_date:
        return jsonify({"error": "Date is required"}), 400

    try:
        # Run Script A
        created_a, updated_a, errors_a, logs_a = run_script_A(filter_date)
        
        # Run Script B
        created_b, updated_b, errors_b, logs_b = run_script_B(filter_date)
        
        return jsonify({
            "status": "success",
            "script_a": {
                "created": created_a,
                "updated": updated_a,
                "errors": errors_a,
                "logs": logs_a
            },
            "script_b": {
                "created": created_b,
                "updated": updated_b,
                "errors": errors_b,
                "logs": logs_b
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
