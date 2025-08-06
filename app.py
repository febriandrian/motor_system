from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
from functools import wraps

# ----------------- APP CONFIG -----------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ----------------- MODELS -----------------
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)


class School(db.Model):
    __tablename__ = 'school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    kabupaten = db.Column(db.String(50), nullable=False)
    tanggal_input = db.Column(db.DateTime, nullable=False)

    motor_entries = db.relationship('MotorEntry', back_populates='school')


class MotorType(db.Model):
    __tablename__ = 'motor_type'
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)

    entries = db.relationship('MotorEntry', back_populates='motor_type')


class MotorEntry(db.Model):
    __tablename__ = 'motor_entry'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('motor_type.id'), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    petugas_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)

    motor_type = db.relationship('MotorType', back_populates='entries')
    school = db.relationship('School', back_populates='motor_entries')

# ----------------- LOGIN MANAGER -----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------- ROLE DECORATOR -----------------
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash("Akses ditolak: Anda tidak punya izin untuk halaman ini.")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ----------------- ROUTES -----------------
@app.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('dashboard_admin'))
    elif current_user.role == 'petugas':
        return redirect(url_for('dashboard_petugas'))
    elif current_user.role == 'manager':
        return redirect(url_for('dashboard_manager'))
    return "Role tidak dikenal."

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login gagal. Username atau password salah.')
    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------- DASHBOARD ADMIN ----------
@app.route('/dashboard/admin')
@login_required
@role_required('admin')
def dashboard_admin():
    schools = School.query.all()
    motors = MotorType.query.all()  # Tambahkan ini
    return render_template('admin_school_list.html', schools=schools, motors=motors)


@app.route('/admin/delete_motor/<int:motor_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_motor(motor_id):
    motor = MotorType.query.get_or_404(motor_id)
    db.session.delete(motor)
    db.session.commit()
    flash(f"Model motor '{motor.model}' berhasil dihapus.", "success")
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/add_school', methods=['POST'])
@login_required
@role_required('admin')
def add_school():
    name = request.form['name']
    kabupaten = request.form['kabupaten']
    tanggal_str = request.form['tanggal_input']
    try:
        tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d')
    except ValueError:
        flash("Format tanggal salah. Gunakan YYYY-MM-DD.")
        return redirect(url_for('dashboard_admin'))

    if not School.query.filter_by(name=name).first():
        db.session.add(School(name=name, kabupaten=kabupaten, tanggal_input=tanggal))
        db.session.commit()
        flash("Sekolah berhasil ditambahkan.")
    else:
        flash("Sekolah sudah ada.")
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/add_motor', methods=['POST'])
@login_required
@role_required('admin')
def add_motor():
    brand = request.form['brand']
    model = request.form['model']
    db.session.add(MotorType(brand=brand, model=model))
    db.session.commit()
    flash("Model motor berhasil ditambahkan.")
    return redirect(url_for('dashboard_admin'))

# ---------- VIEW & EDIT DATA MOTOR ----------
@app.route('/admin/sekolah/<int:school_id>/motor')
@login_required
@role_required('admin')
def admin_view_motor(school_id):
    school = School.query.get_or_404(school_id)
    data_motor = db.session.query(
        MotorEntry.id,
        MotorType.brand,
        MotorType.model,
        MotorEntry.jumlah
    ).join(MotorType, MotorEntry.model_id == MotorType.id) \
     .filter(MotorEntry.school_id == school_id).all()
    return render_template('admin_view_motor.html', school=school, data_motor=data_motor)

@app.route('/admin/motor/edit/<int:motor_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_motor(motor_id):
    motor_entry = MotorEntry.query.get_or_404(motor_id)
    if request.method == 'POST':
        motor_entry.jumlah = request.form['jumlah']
        db.session.commit()
        flash('Data motor berhasil diperbarui.', 'success')
        return redirect(url_for('admin_view_motor', school_id=motor_entry.school_id))
    return render_template('admin_edit_motor.html', motor_entry=motor_entry)

# ---------- DASHBOARD PETUGAS ----------
@app.route('/dashboard/petugas', methods=['GET', 'POST'])
@login_required
@role_required('petugas')
def dashboard_petugas():
    schools = School.query.all()
    motors = MotorType.query.order_by(MotorType.brand).all()
    if request.method == 'POST':
        school_id = request.form['school_id']
        for motor in motors:
            jumlah = request.form.get(f"model_{motor.id}")
            if jumlah and jumlah.isdigit() and int(jumlah) > 0:
                entry = MotorEntry(
                    school_id=school_id,
                    model_id=motor.id,
                    jumlah=int(jumlah),
                    petugas_id=current_user.id
                )
                db.session.add(entry)
        db.session.commit()
        flash("Data motor berhasil disimpan.")
        return redirect(url_for('dashboard_petugas'))
    return render_template('dashboard_petugas.html', schools=schools, motors=motors)

# ---------- DASHBOARD MANAGER ----------
@app.route('/dashboard/manager')
@login_required
@role_required('manager')
def dashboard_manager():
    entries = db.session.query(
        School.name.label("nama_sekolah"),
        School.kabupaten.label("kabupaten"),
        MotorType.brand.label("merek"),
        MotorType.model.label("model"),
        db.func.sum(MotorEntry.jumlah).label('total')
    ).join(School, MotorEntry.school_id == School.id) \
     .join(MotorType, MotorEntry.model_id == MotorType.id) \
     .group_by(School.name, School.kabupaten, MotorType.brand, MotorType.model) \
     .all()

    total_motor = db.session.query(db.func.sum(MotorEntry.jumlah)).scalar() or 0
    sekolah_terbanyak = db.session.query(
        School.name, db.func.sum(MotorEntry.jumlah).label('jumlah')
    ).join(School, MotorEntry.school_id == School.id) \
     .group_by(School.name) \
     .order_by(db.desc('jumlah')).first()
    model_terpopuler = db.session.query(
        MotorType.model, db.func.sum(MotorEntry.jumlah).label('jumlah')
    ).join(MotorType, MotorEntry.model_id == MotorType.id) \
     .group_by(MotorType.model) \
     .order_by(db.desc('jumlah')).first()
    daerah_terbanyak = db.session.query(
        School.kabupaten, db.func.sum(MotorEntry.jumlah).label('jumlah')
    ).join(School, MotorEntry.school_id == School.id) \
     .group_by(School.kabupaten) \
     .order_by(db.desc('jumlah')).first()
    chart_data = db.session.query(
        MotorType.model,
        db.func.sum(MotorEntry.jumlah).label('jumlah')
    ).join(MotorType, MotorEntry.model_id == MotorType.id) \
     .group_by(MotorType.model) \
     .order_by(db.desc('jumlah')).all()

    return render_template(
        'dashboard_manager.html',
        entries=entries,
        total_motor=total_motor,
        sekolah_terbanyak=sekolah_terbanyak,
        model_terpopuler=model_terpopuler,
        daerah_terbanyak=daerah_terbanyak,
        chart_data=chart_data
    )

# ---------- INIT DATA ----------
def init_data():
    if not User.query.first():
        db.session.add(User(username='admin', password=bcrypt.generate_password_hash('admin123').decode('utf-8'), role='admin'))
        db.session.add(User(username='petugas', password=bcrypt.generate_password_hash('petugas123').decode('utf-8'), role='petugas'))
        db.session.add(User(username='manager', password=bcrypt.generate_password_hash('manager123').decode('utf-8'), role='manager'))
    if not MotorType.query.first():
        motors = [
            ("Honda", "BeAT"), ("Honda", "BeAT Street"), ("Honda", "Scoopy"), ("Honda", "Genio"),
            ("Honda", "Vario 125"), ("Honda", "Vario 160"), ("Honda", "PCX 160"), ("Honda", "ADV 160"),
            ("Honda", "Revo"), ("Honda", "Supra X 125"), ("Honda", "CB150R Streetfire"), ("Honda", "CBR150R"), ("Honda", "CRF150L"),
            ("Yamaha", "Mio M3"), ("Yamaha", "Mio Z"), ("Yamaha", "Mio S"), ("Yamaha", "Gear 125"),
            ("Yamaha", "Fazzio Hybrid"), ("Yamaha", "Aerox 155"), ("Yamaha", "NMAX 155"), ("Yamaha", "Lexi 125"),
            ("Yamaha", "FreeGo 125"), ("Yamaha", "XMAX 250"), ("Yamaha", "Jupiter Z1"), ("Yamaha", "MX King 150"),
            ("Suzuki", "Nex II"), ("Suzuki", "Address FI"), ("Suzuki", "Burgman Street 125EX"), ("Suzuki", "Satria F150"),
            ("Suzuki", "GSX-R150"), ("Suzuki", "GSX-S150"),
            ("Vespa", "LX 125 i-get"), ("Vespa", "S 125 i-get"), ("Vespa", "Primavera 150 i-get"),
            ("Vespa", "Sprint 150 i-get"), ("Vespa", "GTS 300")
        ]
        for brand, model in motors:
            db.session.add(MotorType(brand=brand, model=model))
    db.session.commit()

# ---------- MAIN ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_data()
    app.run(debug=True)
