# app.py
from flask import Flask, render_template, send_from_directory, request, redirect, url_for
import psycopg2
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# PostgreSQL configuration (replace with your actual database credentials):
app.config['DATABASE'] = {
    'host': 'localhost',
    'database': 'my_database',
    'user': 'jamshidazizov',
    'password': 'zero'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def connect_db():
    conn = psycopg2.connect(
        host=app.config['DATABASE']['host'],
        database=app.config['DATABASE']['database'],
        user=app.config['DATABASE']['user'],
        password=app.config['DATABASE']['password']
    )
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        image = request.files['image']
        description = request.form['description']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO entries (image_path, description) VALUES (%s, %s)', (image_path, description))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))

    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM entries ORDER BY id DESC')
    entries = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('index.html', entries=entries)

# Route to serve static files (CSS, JS, images, etc.):
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)



# Route for editing an entry (text)
@app.route('/edit/<int:id>', methods=['POST'])
def edit_entry(id):
    conn = connect_db()
    cur = conn.cursor()

    # Get the new text from the request data
    data = request.json
    new_text = data.get('text', '').strip()

    # Update the text in the database
    cur.execute('UPDATE entries SET description = %s WHERE id = %s', (new_text, id))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for('index'))

# Route for deleting an entry (both image and text)
@app.route('/delete/<int:id>', methods=['POST'])
def delete_entry(id):
    conn = connect_db()
    cur = conn.cursor()

    # Get the image path from the database using the provided ID
    cur.execute('SELECT image_path FROM entries WHERE id = %s', (id,))
    image_path = cur.fetchone()[0]

    # Delete the image file from the server
    if os.path.exists(image_path):
        os.remove(image_path)

    # Delete the entry from the database
    cur.execute('DELETE FROM entries WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
