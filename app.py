from flask import Flask, render_template, url_for, request, send_from_directory, jsonify, redirect, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import UnmappedInstanceError
from io import BytesIO
import numpy as np
import pickle

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database1.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'malaymeds'
app.config['UPLOAD_FOLDER'] = 'static/'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'
db = SQLAlchemy(app) 
migrate = Migrate(app, db)
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Define TBL_USER
class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(30), unique=True)
  email = db.Column(db.String(100), unique=True)
  password = db.Column(db.String(80))
  role = db.Column(db.String(10))

# Define TBL_FEVER
class tbl_fever(db.Model):
  fever_id = db.Column(db.Integer, primary_key=True)
  fever_name = db.Column(db.String(255))
  fever_scname = db.Column(db.String(255))
  fever_def = db.Column(db.Text)
  fever_symptoms = db.Column(db.Text)
  herbs = db.relationship('tbl_herbs_fever', backref=db.backref('tbl_fever', cascade='all, delete-orphan', single_parent=True))
  methods = db.relationship('tbl_method_fever', backref=db.backref('tbl_fever', cascade='all, delete-orphan', single_parent=True))
  treatment = db.relationship('tbl_treatment', backref=db.backref('tbl_fever', cascade='all, delete-orphan', single_parent=True))

# Define TBL_HERBS_FEVER
class tbl_herbs_fever(db.Model):
  herbs_fever_id = db.Column(db.Integer, primary_key=True)
  herbs_id = db.Column(db.Integer, db.ForeignKey('tbl_herbs.herbs_id', onupdate='CASCADE', ondelete='CASCADE'))
  fever_id = db.Column(db.Integer, db.ForeignKey('tbl_fever.fever_id', onupdate='CASCADE', ondelete='CASCADE'))

# Define TBL_TREATMENT
class tbl_treatment(db.Model):
  treatment_id = db.Column(db.Integer, primary_key=True)
  treatment_steps = db.Column(db.Text)
  fever_id = db.Column(db.Integer, db.ForeignKey('tbl_fever.fever_id', onupdate='CASCADE', ondelete='CASCADE'))
  alt_treatment = db.Column(db.Text)

# Define TBL_HERBS
class tbl_herbs(db.Model):
  herbs_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  herbs_name = db.Column(db.String(255))
  herbs_scname = db.Column(db.String(255))
  herbs_desc = db.Column(db.Text)
  herbs_parts = db.Column(db.String(255))
  herbs_pic = db.Column(db.LargeBinary)
  herbs_filename = db.Column(db.String(50))
  herbs_path = db.Column(db.String(255))
  fevers = db.relationship('tbl_herbs_fever', backref=db.backref('tbl_herbs', cascade='all, delete-orphan', single_parent=True))

# Define TBL_METHOD
class tbl_method(db.Model):
  method_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  method_name = db.Column(db.String(255))
  method_def = db.Column(db.Text)
  method_path = db.Column(db.String(255))
  method_pic = db.Column(db.LargeBinary)
  method_filename = db.Column(db.String(50))
  fevers = db.relationship('tbl_method_fever', backref=db.backref('tbl_method', cascade='all, delete-orphan', single_parent=True))

# Define TBL_METHOD_FEVER
class tbl_method_fever(db.Model):
  method_fever_id = db.Column(db.Integer, primary_key=True)
  fever_id = db.Column(db.Integer, db.ForeignKey('tbl_fever.fever_id', onupdate='CASCADE', ondelete='CASCADE'))
  method_id = db.Column(db.Integer, db.ForeignKey('tbl_method.method_id', onupdate='CASCADE', ondelete='CASCADE'))

# Define TBL_TREATMENT_DETAILS
class tbl_treatment_details(db.Model):
  detail_id = db.Column(db.Integer, primary_key=True)
  treatment_id = db.Column(db.Integer, db.ForeignKey('tbl_treatment.treatment_id', onupdate='CASCADE', ondelete='CASCADE'))
  fever_id = db.Column(db.Integer, db.ForeignKey('tbl_fever.fever_id', onupdate='CASCADE', ondelete='CASCADE'))
  herbs_id = db.Column(db.Integer, db.ForeignKey('tbl_herbs.herbs_id', onupdate='CASCADE', ondelete='CASCADE'))
  method_id = db.Column(db.Integer, db.ForeignKey('tbl_method.method_id', onupdate='CASCADE', ondelete='CASCADE'))
  fever = db.relationship('tbl_fever', backref=db.backref('treatment_details', lazy=True))
  herbs = db.relationship('tbl_herbs', backref=db.backref('treatment_details', lazy=True))
  method = db.relationship('tbl_method', backref=db.backref('treatment_details', lazy=True))
  treatment = db.relationship('tbl_treatment', backref=db.backref('treatment_details', lazy=True))

# to push data into db
with app.app_context():
  db.create_all()

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

@app.route('/')
@app.route('/welcome')
def welcome_page():
  return render_template('welcome.html')

# @app.route('/home')
# def home_page():
#   return render_template('index.html')

# REGISTER AND LOGIN
@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    role = request.form['role']
    if password != confirm_password:
      flash('Kata laluan tidak sepadan. Sila cuba lagi.', 'danger')
      return redirect(url_for('register'))
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
      flash('Nama pengguna atau e-mel sudah wujud. Sila pilih yang lain.', 'danger')
      return redirect(url_for('register'))
    try:
      user = User(username=username, email=email, password=generate_password_hash(password), role=role)
      db.session.add(user)
      db.session.commit()
      flash('Anda telah berjaya mendaftar!', 'success')
      return redirect(url_for('login'))
    except IntegrityError:
      db.session.rollback()
      flash('Ralat berlaku. Sila cuba lagi.', 'danger')    
  return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user:
      if check_password_hash(user.password, password):
        login_user(user, remember=True)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))
      else:
        flash('Log Masuk tidak berjaya. Sila semak nama pengguna dan kata laluan anda.', 'danger')
    else:
        flash('Akaun tidak wujud. Sila daftar akaun.', 'warning')
  return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
  if current_user.role == 'admin':
    return render_template('adminpage.html')
  else:
    return render_template('index.html')

# --------- RECOMMENDATION & TREATMENT VISUALIZATION PAGES --------- #
def ValuePredictor(to_predict_list):
  to_predict = np.array(to_predict_list).reshape(1,5)
  loaded_model = pickle.load(open("model.pkl","rb"))
  result = loaded_model.predict(to_predict)
  return result[0]

@app.route('/diagnoseme',methods = ['GET', 'POST'])
def diagnoseme_page():
  if request.method == 'POST':
    to_predict_list = request.form.to_dict()
    to_predict_list = [int(value) for value in to_predict_list.values() if value.isdigit()]
    if len(to_predict_list) < 5:
      flash("Sila pilih 5 simptom!", "error")
      return redirect(url_for("diagnoseme_page"))
    result = ValuePredictor(to_predict_list)
    fever_id = int(result)

    if int(result)==0:
      fever_id=1
    elif int(result)==1:
      fever_id=2
    elif int(result)==2:
      fever_id=3
    elif int(result)==3:
      fever_id=4
    elif int(result)==4:
      fever_id=5
    elif int(result)==5:
      fever_id=18
    elif int(result)==6:
      fever_id=6
    elif int(result)==7:
      fever_id=19
    elif int(result)==8:
      fever_id=7
    elif int(result)==9:
      fever_id=20
    elif int(result)==10:
      fever_id=8
    elif int(result)==11:
      fever_id=9
    elif int(result)==12:
      fever_id=10
    elif int(result)==13:
      fever_id=11
    elif int(result)==14:
      fever_id=12
    elif int(result)==15:
      fever_id=14
    elif int(result)==16:
      fever_id=15
    elif int(result)==17:
      fever_id=13
    elif int(result)==18:
      fever_id=16
    else:
      fever_id=17
    
    fever_details = tbl_fever.query.get(fever_id)
    all_treatment_details = tbl_treatment_details.query.filter_by(fever_id=fever_id).all()
    treatment_details = tbl_treatment.query.all()

    herb_ids = [detail.herbs_id for detail in all_treatment_details]
    method_ids = [detail.method_id for detail in all_treatment_details]

    herbs_details = tbl_herbs.query.filter(tbl_herbs.herbs_id.in_(herb_ids)).all()
    methods_details = tbl_method.query.filter(tbl_method.method_id.in_(method_ids)).all()

    herb_pic_paths = [url_for('uploaded_file', filename=herb.herbs_path) for herb in herbs_details]
    method_pic_paths = [url_for('uploaded_file', filename=method.method_path) for method in methods_details]

    return render_template("recommendation.html", fever_details=fever_details, all_treatment_details=all_treatment_details, 
                           herbs_details=herbs_details, methods_details=methods_details, treatment_details=treatment_details,
                           herb_pic_paths=herb_pic_paths, method_pic_paths=method_pic_paths, fever_id=fever_id)
  return render_template("diagnosemeform.html")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
  return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --------- SEARCH HERBS, METHOD AND FEVER PAGES --------- #
@app.route('/searchherbs')
def searchherbs_page():
  ser_herbs_data = tbl_herbs.query.all()
  return render_template('searchherbs.html', ser_herbs_data=ser_herbs_data)

@app.route("/searchherbsres", methods=["POST", "GET"])
def searchherbsres_page():
  if request.method == 'POST':
    search_word = request.form['query']
    print(search_word)
    if search_word == '':
      herbs = tbl_herbs.query.order_by(tbl_herbs.herbs_name).all()
    else:
      herbs = tbl_herbs.query.filter(
          (tbl_herbs.herbs_name.like(f'%{search_word}%')) |
          (tbl_herbs.herbs_scname.like(f'%{search_word}%')) |
          (tbl_herbs.herbs_parts.like(f'%{search_word}%'))
      ).all()
  return jsonify({'htmlresponse': render_template('res_searchherbs.html', herb=herbs)})

@app.route('/searchmethod')
def searchmethods_page():
  ser_method_data = tbl_method.query.all()
  return render_template('searchmethod.html', ser_method_data=ser_method_data)

@app.route("/searchmethodsres", methods=["POST", "GET"])
def searchmethodsres_page():
  if request.method == 'POST':
    search_word = request.form['query']
    # search_word = request.get_json().get('query')
    print(search_word)
    if search_word == '':
      meths = tbl_method.query.order_by(tbl_method.method_name).all()
    else:
      meths = tbl_method.query.filter(
          (tbl_method.method_name.like(f'%{search_word}%')) |
          (tbl_method.method_def.like(f'%{search_word}%'))
      ).all()
  return jsonify({'htmlresponse': render_template('res_searchmethod.html', meth=meths)})

@app.route('/searchfever')
def searchfever_page():
  ser_fever_data = tbl_fever.query.all()
  return render_template('searchfever.html', ser_fever_data=ser_fever_data)

@app.route("/searchfeverres", methods=["POST", "GET"])
def searchfeverres_page():
  if request.method == 'POST':
    search_word = request.form['query']
    # search_word = request.get_json().get('query')
    print(search_word)
    if search_word == '':
      fevers = tbl_fever.query.order_by(tbl_fever.fever_name).all()
    else:
      fevers = tbl_fever.query.filter(
          (tbl_fever.fever_name.like(f'%{search_word}%')) |
          (tbl_fever.fever_scname.like(f'%{search_word}%')) |
          (tbl_fever.fever_symptoms.like(f'%{search_word}%'))
      ).all()
  return jsonify({'htmlresponse': render_template('res_searchfever.html', fever=fevers)})

# HERBS, METHOD AND FEVER INFORMATION PAGES
@app.route('/herbinformation/<int:herb_id>')
def herbinformation_page(herb_id):
  herb = tbl_herbs.query.get(herb_id)
  return render_template('detailherbs.html', herb=herb)

@app.route('/feverinformation/<int:fever_id>')
def feverinformation_page(fever_id):
  fever = tbl_fever.query.get(fever_id)
  return render_template('detailfever.html', fever=fever)

@app.route('/methodinformation/<int:method_id>')
def methodinformation_page(method_id):
  method = tbl_method.query.get(method_id)
  return render_template('detailmethod.html', method=method)

# ADMIN SIDE
@app.route('/managefever')
def managefever_page():
  all_fever_data = tbl_fever.query.all()
  return render_template('fevermanage.html', all_fever_data=all_fever_data)

@app.route('/editfever/<int:fever_id>', methods=['GET', 'POST'])
def editfever_page(fever_id):
  fever_to_edit = tbl_fever.query.get_or_404(fever_id)
  if request.method == 'POST':
    fever_to_edit.fever_name = request.form['fever_name']
    fever_to_edit.fever_scname = request.form['fever_scname']
    fever_to_edit.fever_def = request.form['fever_def']
    fever_to_edit.fever_symptoms = request.form['fever_symptoms']
    db.session.commit()
    return redirect(url_for('managefever_page'))
  return render_template('feveredit.html', fever=fever_to_edit)

def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/manageherbs')
def manageherbs_page():
  all_herbs_data = tbl_herbs.query.all()
  return render_template('herbsmanage.html', all_herbs_data=all_herbs_data)

@app.route('/insertherbs', methods=['GET', 'POST'])
def insertherbs_page():
  if request.method == 'POST':
    herbs_name = request.form['herbs_name']
    herbs_scname = request.form['herbs_scname']
    herbs_desc = request.form['herbs_desc']
    herbs_parts = request.form['herbs_parts']
    herbs_pic = request.files['herbs_pic']
    # Check if the file is allowed
    if herbs_pic and allowed_file(herbs_pic.filename):
      # Secure filename to prevent directory traversal
      filename = secure_filename(herbs_pic.filename)
      herbs_data = tbl_herbs(herbs_name=herbs_name, herbs_scname=herbs_scname, herbs_desc=herbs_desc, herbs_parts=herbs_parts, herbs_pic=herbs_pic.read(), herbs_filename=filename)
      db.session.add(herbs_data)
      db.session.commit()
      flash("Herba berjaya ditambah!", "success")
      return redirect(url_for('manageherbs_page'))
    else:
      flash("Format fail tidak sah. Sila upload fail berformat JPG atau PNG sahaja.", "error")
  return render_template('herbsinsert.html')

@app.route('/editherbs/<int:herbs_id>', methods=['GET', 'POST'])
def editherbs_page(herbs_id):
  herbs_to_edit = tbl_herbs.query.get_or_404(herbs_id)
  if request.method == 'POST':
    herbs_to_edit.herbs_name = request.form['herbs_name']
    herbs_to_edit.herbs_scname = request.form['herbs_scname']
    herbs_to_edit.herbs_desc = request.form['herbs_desc']
    herbs_to_edit.herbs_parts = request.form['herbs_parts']
    new_herbs_pic = request.files['herbs_pic']
    if new_herbs_pic and allowed_file(new_herbs_pic.filename):
      # Secure filename to prevent directory traversal
      filename = secure_filename(new_herbs_pic.filename)
      herbs_to_edit.method_pic = new_herbs_pic.read()
      herbs_to_edit.method_filename = filename
      db.session.commit()
      flash("Herba berjaya dikemaskini!")
      return redirect(url_for('manageherbs_page'))
    else:
      flash("Format fail tidak sah. Sila upload fail berformat JPG atau PNG sahaja.")
  return render_template('herbsedit.html', herbs=herbs_to_edit)

@app.route('/deleteherbs/<herbs_id>/', methods=['GET', 'POST'])
def deleteherbs(herbs_id):
  try:
    herbs_data = tbl_herbs.query.get_or_404(herbs_id)
    is_used = tbl_treatment_details.query.filter_by(herbs_id=herbs_id).first()
    if is_used:
      flash("Herba tidak boleh dipadam kerana ia digunakan oleh rawatan lain.")
    else:
      db.session.delete(herbs_data)
      db.session.commit()
      flash("Herba berjaya dibuang!")
  except UnmappedInstanceError:
    db.session.rollback()
    flash("Ralat berlaku semasa pemadaman.")
  return redirect(url_for('manageherbs_page'))

@app.route('/managemethod')
def managemethod_page():
  all_method_data = tbl_method.query.all()
  return render_template('methodmanage.html', all_method_data=all_method_data)

@app.route('/insertmethod', methods=['GET', 'POST'])
def insertmethod_page():
  if request.method == 'POST':
    method_name = request.form['method_name']
    method_def = request.form['method_def']
    method_pic = request.files['method_pic']
    # Check if the file is allowed
    if method_pic and allowed_file(method_pic.filename):
      # Secure filename to prevent directory traversal
      filename = secure_filename(method_pic.filename)
      method_data = tbl_method(method_name=method_name, method_def=method_def, method_pic=method_pic.read(), method_filename=filename)
      db.session.add(method_data)
      db.session.commit()
      flash("Kaedah Rawatan berjaya ditambah!")
      return redirect(url_for('managemethod_page'))
    else:
      flash("Format fail tidak sah. Sila upload fail berformat JPG atau PNG sahaja.")
  return render_template('methodsinsert.html')

@app.route('/editmethod/<int:method_id>', methods=['GET', 'POST'])
def editmethod_page(method_id):
  method_to_edit = tbl_method.query.get_or_404(method_id)
  if request.method == 'POST':
    method_to_edit.method_name = request.form['method_name']
    method_to_edit.method_def = request.form['method_def']
    new_method_pic = request.files['method_pic']
    if new_method_pic and allowed_file(new_method_pic.filename):
      # Secure filename to prevent directory traversal
      filename = secure_filename(new_method_pic.filename)
      method_to_edit.method_pic = new_method_pic.read()
      method_to_edit.method_filename = filename
      db.session.commit()
      flash("Kaedah Rawatan berjaya dikemaskini!")
      return redirect(url_for('managemethod_page'))
    else:
      flash("Format fail tidak sah. Sila upload fail berformat JPG atau PNG sahaja.")
  return render_template('methodedit.html', methods=method_to_edit)

@app.route('/deletemethod/<method_id>/', methods=['GET', 'POST'])
def deletemethod(method_id):
  try:
    method_data = tbl_method.query.get_or_404(method_id)
    is_used = tbl_treatment_details.query.filter_by(method_id=method_id).first()
    if is_used:
      flash("Kaedah rawatan tidak boleh dipadam kerana ia digunakan oleh rawatan lain.")
    else:
      db.session.delete(method_data)
      db.session.commit()
      flash("Kaedah rawatan berjaya dibuang!")
  except UnmappedInstanceError:
    db.session.rollback()
    flash("Ralat berlaku semasa pemadaman.")
  return redirect(url_for('managemethod_page'))

@app.route('/managetreatment')
def managetreatment_page():
  all_treatment_data = tbl_treatment.query.all()
  return render_template('treatmentmanage.html', all_treatment_data=all_treatment_data)

@app.route('/edittreatment/<int:treatment_id>', methods=['GET', 'POST'])
def edittreatment_page(treatment_id):
  treatment_to_edit = tbl_treatment.query.get_or_404(treatment_id)
  if request.method == 'POST':
    treatment_to_edit.alt_treatment = request.form['alt_treatment']
    db.session.commit()
    return redirect(url_for('managetreatment_page'))
  return render_template('treatmentedit.html', treatment=treatment_to_edit)

@app.route('/display_herb_image/<int:herb_id>')
def display_herb_image(herb_id):
  herb = tbl_herbs.query.get_or_404(herb_id)
  if herb.herbs_filename.lower().endswith('.jpg') or herb.herbs_filename.lower().endswith('.jpeg'):
    mimetype = 'image/jpeg'
  elif herb.herbs_filename.lower().endswith('.png'):
    mimetype = 'image/png'
  else:
    mimetype = 'image/jpeg'
  return send_file(BytesIO(herb.herbs_pic), mimetype=mimetype)

@app.route('/display_method_image/<int:method_id>')
def display_method_image(method_id):
  method = tbl_method.query.get_or_404(method_id)
  if method.method_filename.lower().endswith('.jpg') or method.method_filename.lower().endswith('.jpeg'):
    mimetype = 'image/jpeg'
  elif method.method_filename.lower().endswith('.png'):
    mimetype = 'image/png'
  else:
    mimetype = 'image/jpeg'
  return send_file(BytesIO(method.method_pic), mimetype=mimetype)

if __name__ == "__main__":
  app.run(debug=True)