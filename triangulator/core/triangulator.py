from flask import Flask, request

app = Flask(__name__)

@app.route('/triangulate', methods=['POST'])
def triangulate_endpoint():
    # Validation basique
    if not request.is_json:
        return "Invalid JSON", 400
    data = request.get_json()
    if 'pointSetId' not in data:
        return "Missing pointSetId", 400

    # Logique non implémentée → on lève une exception
    raise NotImplementedError("Triangulation logic not implemented yet")