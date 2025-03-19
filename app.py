from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import mysql.connector
import barcode
from barcode.writer import ImageWriter
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

app.config['BARCODE_FOLDER'] = 'static/barcodes'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'barcode_db'

if not os.path.exists(app.config['BARCODE_FOLDER']):
    os.makedirs(app.config['BARCODE_FOLDER'])

def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

@app.route('/')
def index():
    return render_template('index.html')

def add_text_to_image(image_path, text):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    image_width, image_height = image.size
    text_position = ((image_width - text_width) // 2, image_height - 30)
    draw.text(text_position, text, fill="black", font=font)
    image.save(image_path)

@app.route('/generate', methods=['POST'])
def generate():
    product_name = request.form['product_name']
    data = request.form['data']
    filename = f"{product_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(app.config['BARCODE_FOLDER'], filename)
    
    ean = barcode.get_barcode_class('code128')
    barcode_obj = ean(data, writer=ImageWriter())
    barcode_obj.save(filepath[:-4])
    add_text_to_image(filepath, product_name)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO barcodes (product_name, barcode_path, created_at) VALUES (%s, %s, %s)",
                   (product_name, filename, datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'image_url': url_for('serve_barcode', filename=filename), 'filename': filename})

@app.route('/generate_auto', methods=['POST'])
def generate_auto():
    data = request.get_json()
    product_name = data['product_name']
    categoria = str(data['categoria']).zfill(1)
    codigo_base = "788818230"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT IFNULL(MAX(id), 0) + 1 FROM barcodes")
    next_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    codigo_produto = str(next_id).zfill(3)
    ean12 = codigo_base + categoria + codigo_produto
    digito_verificador = str((10 - sum(int(digit) * (3 if i % 2 else 1) for i, digit in enumerate(ean12)) % 10) % 10)
    ean13 = ean12 + digito_verificador
    
    filename = f"{product_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(app.config['BARCODE_FOLDER'], filename)
    
    ean = barcode.get_barcode_class('ean13')
    barcode_obj = ean(ean13, writer=ImageWriter())
    barcode_obj.save(filepath[:-4])
    add_text_to_image(filepath, product_name)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO barcodes (product_name, barcode_path, created_at) VALUES (%s, %s, %s)",
                   (product_name, filename, datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'image_url': url_for('serve_barcode', filename=filename), 'filename': filename})

@app.route('/barcodes/<filename>')
def serve_barcode(filename):
    return send_from_directory(app.config['BARCODE_FOLDER'], filename)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, barcode_path FROM barcodes WHERE product_name LIKE %s OR barcode_path LIKE %s", 
                   (f"%{query}%", f"%{query}%"))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)

@app.route('/download/<filename>')
def download_barcode(filename):
    return send_from_directory(app.config['BARCODE_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
