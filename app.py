from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class Motor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merek = db.Column(db.String(50))
    model = db.Column(db.String(50))
    sekolah = db.Column(db.String(100))

@app.route('/')
def index():
    motors = Motor.query.all()
    return render_template('index.html', motors=motors)

@app.route('/add', methods=['POST'])
def add_motor():
    merek = request.form['merek']
    model = request.form['model']
    sekolah = request.form['sekolah']
    motor = Motor(merek=merek, model=model, sekolah=sekolah)
    db.session.add(motor)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
