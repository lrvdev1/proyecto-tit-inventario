from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'clave-secreta-nup-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://nup_user:nup_password@db:5432/nup_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(minutes=30)

db = SQLAlchemy(app)

# ==================== MODELOS ====================
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)

class Lote(db.Model):
    __tablename__ = 'lotes'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    numero_lote = db.Column(db.String(50), nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    stock_actual = db.Column(db.Integer, default=0)
    producto = db.relationship('Producto', backref='lotes')

class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lotes.id'))
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    comentario = db.Column(db.Text)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class BitacoraSeguridad(db.Model):
    __tablename__ = 'bitacora_seguridad'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    accion = db.Column(db.String(100), nullable=False)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== RUTAS ====================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(password) and usuario.activo:
            session['user_id'] = usuario.id
            session['user_nombre'] = usuario.nombre
            session['user_rol'] = usuario.rol
            session.permanent = True
            
            bitacora = BitacoraSeguridad(usuario_id=usuario.id, accion='login exitoso')
            db.session.add(bitacora)
            db.session.commit()
            
            flash('Bienvenido!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', usuario=session)

@app.route('/inventario')
def inventario():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    lotes = Lote.query.all()
    return render_template('inventario.html', lotes=lotes, usuario=session)

@app.route('/movimiento', methods=['GET', 'POST'])
def movimiento():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        tipo = request.form['tipo']
        lote_id = request.form['lote_id']
        cantidad = int(request.form['cantidad'])
        comentario = request.form.get('comentario', '')
        
        lote = Lote.query.get(lote_id)
        if tipo in ['salida', 'reposicion'] and cantidad > lote.stock_actual:
            flash('Error: Cantidad mayor al stock disponible', 'error')
            return redirect(url_for('movimiento'))
        
        movimiento = Movimiento(
            lote_id=lote_id,
            tipo=tipo,
            cantidad=cantidad,
            vendedor_id=session['user_id'],
            comentario=comentario
        )
        db.session.add(movimiento)
        
        if tipo == 'entrada':
            lote.stock_actual += cantidad
        else:
            lote.stock_actual -= cantidad
        
        db.session.commit()
        
        bitacora = BitacoraSeguridad(usuario_id=session['user_id'], accion=f'{tipo} de {cantidad} unidades')
        db.session.add(bitacora)
        db.session.commit()
        
        flash('Movimiento registrado exitosamente', 'success')
        return redirect(url_for('inventario'))
    
    lotes = Lote.query.all()
    return render_template('movimiento.html', lotes=lotes, usuario=session)

@app.route('/logout')
def logout():
    if 'user_id' in session:
        bitacora = BitacoraSeguridad(usuario_id=session['user_id'], accion='logout')
        db.session.add(bitacora)
        db.session.commit()
        session.clear()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('login'))

@app.route('/productos')
def productos():
    if 'user_id' not in session or session.get('user_rol') != 'administrador':
        flash('Acceso denegado', 'error')
        return redirect(url_for('dashboard'))
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos, usuario=session)

@app.route('/lotes')
def lotes():
    if 'user_id' not in session or session.get('user_rol') != 'administrador':
        flash('Acceso denegado', 'error')
        return redirect(url_for('dashboard'))
    lotes = Lote.query.all()
    return render_template('lotes.html', lotes=lotes, usuario=session)

@app.route('/reportes')
def reportes():
    if 'user_id' not in session or session.get('user_rol') != 'administrador':
        flash('Acceso denegado', 'error')
        return redirect(url_for('dashboard'))
    
    from sqlalchemy import func
    from datetime import datetime
    
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    
    # Reporte 1: Producto más vendido
    mas_vendido = db.session.query(
        Producto.nombre,
        func.sum(Movimiento.cantidad).label('total')
    ).join(Lote, Lote.producto_id == Producto.id)\
     .join(Movimiento, Movimiento.lote_id == Lote.id)\
     .filter(Movimiento.tipo == 'salida')\
     .filter(func.extract('month', Movimiento.fecha_hora) == mes_actual)\
     .group_by(Producto.id).first()
    
    # Reporte 2: Pérdidas por vencimiento
    perdidas = db.session.query(
        Producto.nombre,
        func.sum(Lote.stock_actual).label('total')
    ).join(Lote, Lote.producto_id == Producto.id)\
     .filter(Lote.fecha_vencimiento < datetime.now().date())\
     .group_by(Producto.id).all()
    
    return render_template('reportes.html', 
                          mas_vendido=mas_vendido, 
                          perdidas=perdidas, 
                          usuario=session)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Usuario.query.filter_by(email='admin@nup.cl').first():
            hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            admin = Usuario(nombre='Administrador', email='admin@nup.cl', password_hash=hashed.decode('utf-8'), rol='administrador', activo=True)
            db.session.add(admin)
            db.session.commit()
            print("Usuario admin creado: admin@nup.cl / admin123")
    app.run(host='0.0.0.0', debug=True)