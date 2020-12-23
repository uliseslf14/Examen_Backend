#Libraries
from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_mysqldb import MySQL
import hashlib
from datetime import timedelta

app = Flask(__name__)

#Manejamos sesion de 24 horas
@app.before_request
def set_session_timeout():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1440)

#Configuraciones de conexión a la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'books_db'
mysql=MySQL(app)

app.secret_key = 'mysecretkey'
#Ruta para mostar indice
@app.route('/')
def index():
	return render_template("index.html")

#Mostramos formularios ya sea registro o de login
@app.route('/auth')
def authentication():
	return render_template("auth.html")

#Obtenemos los datos de registro
@app.route('/auth/register', methods=['POST'])
def register():
	num_of_items = 1;
	if request.method == 'POST':
		#obtenemos datos del formulario de registro
		name = request.form['name']
		email = request.form['email']
		password = hashlib.md5(str(request.form['password']).encode('utf-8')).hexdigest()
		cur = mysql.connection.cursor()

		#Verificamos que no exista el nombre de usuario obteniendo la cantidad
		#de registros con el mismo nobre
		try:
			cur.execute('SELECT count(email) FROM users WHERE email = "' + str(email) +'"')
			num_of_items =  [v for v in cur.fetchone()][0]

		except mysql.connection.Error as e:
			flash('Error de conexión '+str(e))

		#Si el registro no existe, lo agregamos a la base de datos y vamos de nuevo 
		#A la ruta con los formularios de login y registro
		if(num_of_items==0):
			try:
				cur.execute('INSERT INTO users (name, email, password) VALUES (%s,%s,%s)', (name, email, password))
				mysql.connection.commit()
				flash('Registro Correcto ')
			except mysql.connection.Error as e:
				flash('Error de conexión '+str(e))
			
		else:
			flash('Le dirección del email ya está registrada.')

		return redirect(url_for('authentication'))

#Ruta de inicio de sesión
@app.route('/auth/login', methods=['POST'])
def login():
	num_of_items = 0;
	if request.method == 'POST':
		#Recibimos los datos del formulario de login
		email = request.form['email']
		#Encriptamos la contraseña
		password = hashlib.md5(str(request.form['password']).encode('utf-8')).hexdigest()

		cur = mysql.connection.cursor()
		#Verificamos si las credenciales son correctas
		try:
			cur.execute('SELECT count(*) FROM users WHERE email = "' + str(email) +'" AND password = "' + str(password) +'"')
			num_of_items =  [v for v in cur.fetchone()][0]
		except mysql.connection.Error as e:
			flash('Error de conexión '+str(e))

		#Si exoste el usuario, iniciamos sesion obteniendo su id y su email, y accedemos a la ruta que muestra sus libros
		if num_of_items==1 :
			cur.execute('SELECT id FROM users WHERE email = "' + str(email) +'" AND password = "' + str(password) +'"')
			id_user =  [v for v in cur.fetchone()][0]
			session['email']=email
			session['id'] = id_user
			return redirect(url_for('books'))
		else:
			flash('Las credenciales con incorrectas.')
			return redirect(url_for('authentication'))


#Ruta para mostrar los libros de un usuario
@app.route('/books', methods=['GET' , 'POST'])
def books():
	#Verificamos si existe una sesión iniciada
	if 'email' in session:
		cur = mysql.connection.cursor()

		#Obtenemos la tabla de los registos de los libros que tiene un usuario
		#Ademas mostramos un formulario para registrar libros
		try:
			cur.execute('SELECT id, isbn,title,author, release_date  FROM books where users_id = '+str(session['id']))
			data = cur.fetchall()
			return render_template('books.html', books=data)
		except mysql.connection.Error as e:
			flash('Error de conexión '+str(e))

	else: 
		flash('Expiró la sesión')
		return redirect(url_for('authentication'))

#GEstion de eliminación y creación de libros
@app.route('/books_saved', methods=['POST'])
def books_saved():
	if request.method == 'POST':
		#Obtenemos los datos del formulario para registrar libros
		num_of_items=1
		isbn = request.form['isbn']
		author = request.form['author']
		title = request.form['title']
		release_date = request.form['release_date']
		cur = mysql.connection.cursor()

		#Verificamos si al ingresar un libro se repite un ISBN
		try:
			cur.execute('SELECT count(isbn) FROM books WHERE users_id = "' + str(session['id']) +'" AND isbn = '+str(isbn)+'')
			num_of_items =  [v for v in cur.fetchone()][0]
		except mysql.connection.Error as e:
			flash('Error de conexión '+str(e))
		#Si no se repite el ISBN agregamos el libro y nos dirigimos de nuevo la gestión de libros
		if(num_of_items==0):
			try:
				cur.execute('INSERT INTO books (isbn, author, title, release_date, users_id) VALUES ("'+str(isbn)+'","'+str(author)+'","'+str(title)+'","'+str(release_date)+'",'+str(session['id'])+')')
				mysql.connection.commit()
				flash('Registro Correcto ')
				return redirect(url_for('books'))
			except mysql.connection.Error as e:
				flash('Error de conexión '+str(e))
				return redirect(url_for('books'))
		else:
			flash('El ISBN ya ha sido registrado anteriormente.')
			return redirect(url_for('books'))
	return render_template('books.html')

#Ruta que elimina libros a partir de un parametro id (identificador inequivoco de la tabla en la base de datos)
@app.route('/delete/<string:id>')
def books_delete(id):
	cur = mysql.connection.cursor()
	#De manera simple se ejecuta una eliminación haciendo uso del id del libro y del id del usuario en sesion
	try:
		cur.execute('DELETE FROM books WHERE users_id = "' + str(session['id']) +'" AND id = '+str(id)+'')
		mysql.connection.commit()
		flash('Eliminación exitosa ')
		return redirect(url_for('books'))
	except mysql.connection.Error as e:
		flash('Error de conexión '+str(e))
		return redirect(url_for('books'))

if __name__ == '__main__':
	app.run(port = 3000, debug = True)

