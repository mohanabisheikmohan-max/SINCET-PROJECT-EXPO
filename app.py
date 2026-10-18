import os, sqlite3, csv, io, secrets
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
load_dotenv()
app=Flask(__name__); app.secret_key=os.getenv('SESSION_SECRET') or secrets.token_hex(32)
UPLOAD=Path('uploads'); UPLOAD.mkdir(exist_ok=True)
DB='registrations.db'
DATABASE_URL=os.getenv('DATABASE_URL','').strip()
USE_POSTGRES=DATABASE_URL.startswith(('postgres://','postgresql://'))
def db():
 if USE_POSTGRES:
  import psycopg
  from psycopg.rows import dict_row
  return psycopg.connect(DATABASE_URL, sslmode=os.getenv('PGSSLMODE','require'), row_factory=dict_row)
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
 c=db(); sql=('CREATE TABLE IF NOT EXISTS registrations (id BIGSERIAL PRIMARY KEY, team_leader TEXT, member1 TEXT, member2 TEXT, topic_name TEXT, topic_description TEXT, email TEXT, phone TEXT, transaction_id TEXT, payment_proof TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)' if USE_POSTGRES else 'CREATE TABLE IF NOT EXISTS registrations (id INTEGER PRIMARY KEY AUTOINCREMENT, team_leader TEXT, member1 TEXT, member2 TEXT, topic_name TEXT, topic_description TEXT, email TEXT, phone TEXT, transaction_id TEXT, payment_proof TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'); c.execute(sql); c.commit(); c.close()
@app.route('/')
def index(): return render_template('index.html')
@app.post('/register')
def register():
 keys=['team_leader','member1','member2','topic_name','topic_description','email','phone','transaction_id']; d={k:request.form.get(k,'').strip() for k in keys}
 if any(not x for x in d.values()): flash('அனைத்து விவரங்களையும் நிரப்பவும்.','error'); return redirect(url_for('index'))
 f=request.files.get('payment_proof'); filename=''
 if f and f.filename:
  name=secure_filename(f.filename); ext=name.rsplit('.',1)[-1].lower() if '.' in name else ''
  if ext not in {'png','jpg','jpeg','pdf'}: flash('PNG/JPG/PDF proof மட்டும் upload செய்யவும்.','error'); return redirect(url_for('index'))
  filename=secrets.token_hex(8)+'_'+name; f.save(UPLOAD/filename)
 c=db(); mark='%s' if USE_POSTGRES else '?'; marks=', '.join([mark]*9); 
c.execute(
    f'''INSERT INTO registrations (
        team_leader,
        member_1,
        member_2,
        topic_name,
        topic_description,
        email,
        phone,
        transaction_id,
        payment_proof
    ) VALUES ({marks})''',
    tuple(d[k] for k in keys) + (filename,)
)

def admin_only(fn):
 @wraps(fn)
 def w(*a,**kw):
  if not session.get('admin'): return redirect(url_for('admin_login'))
  return fn(*a,**kw)
 return w
@app.route('/admin',methods=['GET','POST'])
def admin_login():
 if request.method=='POST':
  if request.form.get('username')==os.getenv('ADMIN_USERNAME','admin') and os.getenv('ADMIN_PASSWORD_HASH') and check_password_hash(os.getenv('ADMIN_PASSWORD_HASH'),request.form.get('password','')): session['admin']=True; return redirect(url_for('dashboard'))
  flash('Login failed. .env credentials சரிபார்க்கவும்.','error')
 return render_template('admin_login.html')
@app.route('/admin/dashboard')
@admin_only
def dashboard():
 c=db(); rows=c.execute('SELECT * FROM registrations ORDER BY id DESC').fetchall(); c.close(); return render_template('dashboard.html',rows=rows)
@app.route('/admin/proof/<path:name>')
@admin_only
def proof(name):
 p=UPLOAD/os.path.basename(name)
 if not p.is_file(): return ('Not found',404)
 return send_file(p,as_attachment=True)
@app.route('/admin/export.csv')
@admin_only
def export():
 c=db(); rows=c.execute('SELECT * FROM registrations ORDER BY id DESC').fetchall(); c.close(); s=io.StringIO(); w=csv.writer(s); w.writerow(list(rows[0].keys()) if rows else ['id','team_leader','member1','member2','topic_name','topic_description','email','phone','transaction_id','payment_proof','created_at']); w.writerows([[r[k] for k in r.keys()] for r in rows]); return send_file(io.BytesIO(s.getvalue().encode('utf-8-sig')),mimetype='text/csv',as_attachment=True,download_name='registrations.csv')
@app.route('/admin/logout')
def logout(): session.clear(); return redirect(url_for('index'))
if __name__=='__main__': init_db(); app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')))
