from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_FILE = 'clinica.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(''' CREATE TABLE IF NOT EXISTS pacientes (id INTEGER PRIMARY KEY, nombre TEXT)''')

    c.execute(''' CREATE TABLE IF NOT EXISTS expedientes
                (id INTEGER PRIMARY KEY, paciente_id INTEGER, diagnostico TEXT, medicamento TEXT, es_vip INTEGER)''')
    
    c.execute("SELECT count(*) FROM pacientes")
    if c.fetchone()[0] == 0:
        
        c.execute("INSERT INTO pacientes (id, nombre) VALUES (1, 'Bob (Atacante)')")
        c.execute("INSERT INTO pacientes (id, nombre) VALUES (2, 'Alice (Directora VIP)')")
    
        c.execute("INSERT INTO expedientes (paciente_id, diagnostico, medicamento, es_vip) VALUES (1, 'Resfriado', 'Paracetamol', 0)")
        c.execute("INSERT INTO expedientes (paciente_id, diagnostico, medicamento, es_vip) VALUES (2, 'Tratamiento Confidencial', 'Medicina Experimental', 1)")
        conn.commit()
    conn.close()


@app.route('/api/expediente/<int:expediente_id>', methods=['GET'])
def ver_expediente(expediente_id):
    """Vulnerabilidad 1: IDOR en lectura de Base de Datos"""

    paciente_actual_id = int(request.headers.get('X-Paciente-Id', 1))
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Para devolver diccionarios
    c = conn.cursor()
    
    c.execute("SELECT * FROM expedientes WHERE id = ?", (expediente_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "No encontrado"}), 404


@app.route('/api/expediente/<int:expediente_id>/update', methods=['PUT'])
def actualizar_expediente(expediente_id):
    """Vulnerabilidad 2: Broken Access Control por SQL Dinámico Inseguro"""
    datos = request.json
    if not datos:
        return jsonify({"error": "No hay datos"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    columnas_a_actualizar = []
    valores = []
    
    for columna, valor in datos.items():
        columnas_a_actualizar.append(f"{columna} = ?")
        valores.append(valor)
        
    set_clause = ", ".join(columnas_a_actualizar)
    valores.append(expediente_id)
    
    query = f"UPDATE expedientes SET {set_clause} WHERE id = ?"
    
    try:
        c.execute(query, valores)
        conn.commit()
    except sqlite3.OperationalError as e:
        return jsonify({"error": f"Error SQL: {e}"}), 400
    finally:
        conn.close()

    return jsonify({"mensaje": "Expediente actualizado en BD", "query_ejecutado": query})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)