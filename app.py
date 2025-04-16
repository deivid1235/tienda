from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta'  # Clave para la sesión

# Ruta absoluta para evitar errores con la base de datos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'sitio.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # Crea la carpeta si no existe

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa SQLAlchemy
db = SQLAlchemy(app)

# Modelo de la base de datos para Libros
class Libro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    imagen = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Libro {self.nombre}>'

# Modelo de la base de datos para Mensajes
class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    remitente = db.Column(db.String(50), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Mensaje {self.id}>'

# Modelo de la base de datos para Documentos
class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Documento {self.nombre}>'

# Crear las tablas si no existen
with app.app_context():
    db.create_all()

# Rutas del sitio
@app.route('/')
def inicio():
    return render_template('sitio/index.html', welcome_message="Bienvenid@")

@app.route('/libros')
def libros():
    libros = Libro.query.all()
    return render_template('sitio/libros.html', libros=libros)

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

@app.route('/chat')
def chat():
    return render_template('sitio/chat.html', remitente='sitio')

# Rutas de administración
@app.route('/admin/')
def admin_index():
    if session.get('logged_in'):
        return render_template('admin/index.html')
    return redirect('/admin/login')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'imanbruno2006':  # Contraseña válida
            session['logged_in'] = True
            return redirect('/admin/')
        return render_template('admin/login.html', error="Contraseña incorrecta.")
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect('/admin/login')

@app.route('/admin/libros')
def admin_libros():
    if not session.get('logged_in'):
        return redirect('/admin/login')
    libros = Libro.query.all()
    return render_template("admin/libros.html", libros=libros)

@app.route('/admin/libros/guardar', methods=['POST'])
def admin_libros_guardar():
    if not session.get('logged_in'):
        return redirect('/admin/login')
    _nombre = request.form['txtNombre']
    _url = request.form['txtURL']
    _archivo = request.files['txtImagen']

    try:
        nombre_archivo = _archivo.filename if _archivo else ''
        nuevo_libro = Libro(nombre=_nombre, url=_url, imagen=nombre_archivo)
        db.session.add(nuevo_libro)
        db.session.commit()

        if _archivo:
            os.makedirs('static/images', exist_ok=True)
            _archivo.save(f'static/images/{nombre_archivo}')

        return redirect('/admin/libros')
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        return "Error al guardar los datos."

@app.route('/admin/libros/eliminar/<int:id>', methods=['POST'])
def eliminar_libro_post(id):
    if not session.get('logged_in'):
        return redirect('/admin/login')
    try:
        libro = Libro.query.get(id)
        if libro:
            ruta_imagen = f'static/images/{libro.imagen}'
            if os.path.exists(ruta_imagen):
                os.remove(ruta_imagen)
            db.session.delete(libro)
            db.session.commit()
        return redirect('/admin/libros')
    except Exception as e:
        print(f"Error al eliminar el libro: {e}")
        return "Error al eliminar el libro."

# Rutas para el chat
@app.route('/admin/chat')
def admin_chat():
    if not session.get('logged_in'):
        return redirect('/admin/login')
    return render_template('admin/chat.html', remitente='admin')

# Ruta para obtener mensajes (AJAX)
@app.route('/obtener_mensajes', methods=['GET'])
def obtener_mensajes():
    mensajes = Mensaje.query.order_by(Mensaje.fecha.asc()).all()
    mensajes_json = [{
        'id': msg.id,
        'remitente': msg.remitente,
        'mensaje': msg.mensaje,
        'fecha': msg.fecha.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in mensajes]
    return jsonify(mensajes_json)

# Ruta para enviar mensajes (AJAX)
@app.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    data = request.json
    remitente = data.get('remitente')
    mensaje = data.get('mensaje')

    if not remitente or not mensaje:
        return jsonify({'error': 'Faltan datos'}), 400

    nuevo_mensaje = Mensaje(remitente=remitente, mensaje=mensaje)
    db.session.add(nuevo_mensaje)
    db.session.commit()

    return jsonify({'status': 'success'})

# Otras rutas de administración
@app.route('/admin/trabajos')
def admin_trabajos():
    if not session.get('logged_in'):
        return redirect('/admin/login')
    return render_template('admin/trabajos.html')

@app.route('/admin/videos')
def admin_videos():
    if not session.get('logged_in'):
        return redirect('/admin/login')
    return render_template('admin/videos.html')

@app.route('/admin/cerrar')
def admin_cerrar():
    session.pop('logged_in', None)  # Elimina la sesión
    return redirect('/admin/login')  # Redirige al login

if __name__ == '__main__':
    app.run(debug=True)