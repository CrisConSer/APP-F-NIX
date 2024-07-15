from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Función para inicializar la base de datos
def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rival TEXT,
                            player1 TEXT,
                            player2 TEXT,
                            court TEXT,
                            points_player1 INTEGER,
                            points_player2 INTEGER,
                            points_couple TEXT,
                            total_points INTEGER,
                            result TEXT)''')
        conn.commit()

# Ruta principal
@app.route('/')
def index():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, rival, player1, player2, court, points_player1, points_player2, points_couple, total_points, result FROM matches')
        matches = cursor.fetchall()
    return render_template('index.html', matches=matches)

# Ruta para agregar un partido
@app.route('/add_match', methods=['POST'])
def add_match():
    rival = request.form['rival']
    player1 = request.form['player1']
    player2 = request.form['player2']
    court = request.form['court']
    points_player1 = request.form['points_player1']
    points_player2 = request.form['points_player2']
    points_couple = request.form['points_couple']
    result = request.form.get('result')  # Checkbox

    if not player1 or not player2 or not court or not points_player1 or not points_player2 or result is None:
        return "Todos los campos son obligatorios", 400
    
    try:
        points_player1 = int(points_player1)
        points_player2 = int(points_player2)
    except ValueError:
        return "Los puntos deben ser números enteros", 400

    total_points = points_player1 + points_player2

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO matches (rival, player1, player2, court, points_player1, points_player2, total_points, result, points_couple) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                       (rival, player1, player2, court, points_player1, points_player2, total_points, result, points_couple))
        conn.commit()
    
    return redirect('/')

# Ruta para eliminar un partido
@app.route('/delete_match/<int:id>')
def delete_match(id):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM matches WHERE id = ?', (id,))
        conn.commit()
    return redirect('/')

# Ruta para editar un partido
@app.route('/edit_match/<int:id>', methods=['GET', 'POST'])
def edit_match_view(id):
    if request.method == 'POST':
        rival = request.form['rival']
        player1 = request.form['player1']
        player2 = request.form['player2']
        court = request.form['court']
        points_player1 = request.form['points_player1']
        points_player2 = request.form['points_player2']
        points_couple = request.form['points_couple']
        result = request.form.get('result')  # Checkbox

        if not player1 or not player2 or not court or not points_player1 or not points_player2 or result is None:
            return "Todos los campos son obligatorios", 400

        try:
            points_player1 = int(points_player1)
            points_player2 = int(points_player2)
        except ValueError:
            return "Los puntos deben ser números enteros", 400

        total_points = points_player1 + points_player2

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE matches SET rival = ?, player1 = ?, player2 = ?, court = ?, points_player1 = ?, points_player2 = ?, points_couple=?, total_points = ?, result = ? WHERE id = ?',
                           (rival, player1, player2, court, points_player1, points_player2, points_couple, total_points, result, id))
            conn.commit()
        return redirect('/')
    
    else:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT rival, player1, player2, court, points_player1, points_player2, points_couple, result FROM matches WHERE id = ?', (id,))
            match = cursor.fetchone()
        return render_template('edit_match.html', match=match, id=id)

# Ruta para el perfil de una jugadora
@app.route('/player/<name>')
def player_profile(name):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM matches WHERE player1 = ? OR player2 = ?', (name, name))
        matches = cursor.fetchall()

        # Obtener estadísticas de partidos ganados y perdidos
        cursor.execute('SELECT result, COUNT(*) FROM matches WHERE player1 = ? OR player2 = ? GROUP BY result', (name, name))
        data = cursor.fetchall()
    
    results = {result: count for result, count in data}
    won = results.get('Ganado', 0)
    lost = results.get('Perdido', 0)

    return render_template('player_profile.html', name=name, matches=matches, won=won, lost=lost)

# Ruta para la búsqueda de jugadoras
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        player_name = request.form['player_name']
        return redirect(f'/player/{player_name}')
    return render_template('search.html')

# Ruta para el gráfico de partidos ganados vs perdidos
@app.route('/plot')
def plot():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT result, COUNT(*) FROM matches GROUP BY result')
        data = cursor.fetchall()

    results = {result: count for result, count in data}
    won = results.get('Ganado', 0)
    lost = results.get('Perdido', 0)

    labels = ['Ganados', 'Perdidos']
    values = [won, lost]

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Partidos Ganados vs Perdidos')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return send_file(buf, mimetype='image/png')

# Ruta para el gráfico de partidos ganados vs perdidos por jugador
@app.route('/plot_player/<name>')
def plot_player(name):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT result, COUNT(*) FROM matches WHERE player1 = ? OR player2 = ? GROUP BY result', (name, name))
        data = cursor.fetchall()

    results = {result: count for result, count in data}
    won = results.get('Ganado', 0)
    lost = results.get('Perdido', 0)

    labels = ['Ganados', 'Perdidos']
    values = [won, lost]

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f'Partidos Ganados vs Perdidos de {name}')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')
