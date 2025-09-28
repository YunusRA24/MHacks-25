from flask import Flask, request, jsonify
from flask_cors import CORS
import agents

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
  return jsonify({"ok": True})

@app.route('/api/shop', methods=['POST'])
def api_shop():
  try:
    data = request.get_json(force=True)
    raw_text = data.get('text', '') if isinstance(data, dict) else ''
    send_email = bool(data.get('send_email')) if isinstance(data, dict) else False
    to_override = data.get('to') if isinstance(data, dict) else None
    if not raw_text:
      return jsonify({"error": "Missing 'text' in body"}), 400

    result = agents.process_user_text(raw_text)

    if send_email and isinstance(result, dict):
      email_result = agents.send_agentmail_email(result, to=to_override)
      result["email"] = email_result

    return jsonify(result), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
