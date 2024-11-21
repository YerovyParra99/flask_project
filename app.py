from flask import Flask, render_template, request, redirect, session, url_for, flash, Response
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# URI de conexión a MongoDB Atlas
MONGO_URI = "mongodb+srv://parrabeltranangelyerovi:c0D9uVmkdKbEhu0O@cluster0.7svel.mongodb.net/graficos?retryWrites=true&w=majority"

try:
    # Conexión a MongoDB
    client = MongoClient(MONGO_URI)
    db = client["graficos"]  # Base de datos
    usuarios = db["users"]  # Colección de usuarios
    graficos = db["graficos"]  # Colección de gráficos
    print("Conexión exitosa a MongoDB")
except Exception as e:
    print("Error al conectar:", e)


# Página de inicio
@app.route('/')
def index():
    return render_template('index.html')


# Página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = usuarios.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['role'] = user['role']
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas', 'danger')
    return render_template('login.html')


# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        role = 'admin' if request.form.get('admin') else 'user'

        # Verificar si el email ya está registrado
        if usuarios.find_one({'email': email}):
            flash('El correo ya está registrado', 'danger')
        else:
            usuarios.insert_one({'nombre': nombre, 'email': email, 'password': hashed_password, 'role': role})
            flash('Registro exitoso, puedes iniciar sesión ahora', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


# Panel de usuario y administrador
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    if role == 'admin':
        usuarios_normales = usuarios.find({'role': 'user'})
        data = graficos.find()
        return render_template('admin_dashboard.html', usuarios=usuarios_normales, data=data)
    else:
        data = graficos.find()
        return render_template('user_dashboard.html', data=data)


# CRUD para gráficos (Administrador)
@app.route('/add_grafico', methods=['POST'])
def add_grafico():
    if 'role' in session and session['role'] == 'admin':
        valor = request.form.get('valor')
        unidad = request.form.get('unidad')
        vigencia_desde = request.form.get('vigencia_desde')
        vigencia_hasta = request.form.get('vigencia_hasta')
        graficos.insert_one({
            'VALOR': valor,
            'UNIDAD': unidad,
            'VIGENCIADESDE': vigencia_desde,
            'VIGENCIAHASTA': vigencia_hasta
        })
        flash('Gráfico agregado correctamente', 'success')
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/edit_grafico/<id>', methods=['POST'])
def edit_grafico(id):
    if 'role' in session and session['role'] == 'admin':
        graficos.update_one({'_id': ObjectId(id)}, {'$set': {
            'VALOR': request.form.get('valor'),
            'UNIDAD': request.form.get('unidad'),
            'VIGENCIADESDE': request.form.get('vigencia_desde'),
            'VIGENCIAHASTA': request.form.get('vigencia_hasta')
        }})
        flash('Gráfico actualizado correctamente', 'success')
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/delete_grafico/<id>', methods=['GET'])
def delete_grafico(id):
    if 'role' in session and session['role'] == 'admin':
        graficos.delete_one({'_id': ObjectId(id)})
        flash('Gráfico eliminado correctamente', 'success')
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/delete_user/<id>', methods=['GET'])
def delete_user(id):
    if 'role' in session and session['role'] == 'admin':
        usuarios.delete_one({'_id': ObjectId(id)})
        flash('Usuario eliminado correctamente', 'success')
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/edit_user/<id>', methods=['POST'])
def edit_user(id):
    if 'role' in session and session['role'] == 'admin':
        usuarios.update_one({'_id': ObjectId(id)}, {'$set': {
            'nombre': request.form.get('nombre'),
            'email': request.form.get('email'),
            'role': request.form.get('role')
        }})
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# Ruta para generar y descargar el PDF
@app.route('/download_pdf')
def download_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = graficos.find()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Datos de la Colección Gráficos")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "Datos de la Colección Gráficos")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 750, "Valor")
    pdf.drawString(150, 750, "Unidad")
    pdf.drawString(250, 750, "Vigencia Desde")
    pdf.drawString(400, 750, "Vigencia Hasta")

    y = 730
    pdf.setFont("Helvetica", 10)
    for grafico in data:
        pdf.drawString(50, y, str(grafico['VALOR']))
        pdf.drawString(150, y, grafico['UNIDAD'])
        pdf.drawString(250, y, grafico['VIGENCIADESDE'])
        pdf.drawString(400, y, grafico['VIGENCIAHASTA'])
        y -= 20
        if y < 50:
            pdf.showPage()
            y = 800

    pdf.save()
    buffer.seek(0)
    return Response(buffer, mimetype='application/pdf', headers={"Content-Disposition": "attachment;filename=datos_graficos.pdf"})


# Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

