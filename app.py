from flask import Flask, request, render_template, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pickle
import os
from model.preprocessing import clean_text
from data.makanan import image_map_makanan, nutrition_info_makanan, category_map_makanan, saran_sehat_makanan
from data.snack import image_map_snack, nutrition_info_snack, category_map_snack, saran_sehat_snack
from data.minuman import image_map_minuman, nutrition_info_minuman, category_map_minuman, saran_sehat_minuman
from data.sayur import image_map_sayur, nutrition_info_sayur, category_map_sayur, saran_sehat_sayur
from data.buah import image_map_buah, nutrition_info_buah, category_map_buah, saran_sehat_buah
import random

app = Flask(__name__)
app.secret_key = 'rahasia_ganti_ini'

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///riwayat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inisialisasi database
db = SQLAlchemy(app)

# Model database
class Riwayat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_makanan = db.Column(db.String(100), nullable=False)
    hasil = db.Column(db.String(20), nullable=False)
    kategori = db.Column(db.String(50))
    waktu = db.Column(db.DateTime, default=datetime.utcnow)

# Load model
model_path = os.path.join('model', 'food_model.pkl')
with open(model_path, 'rb') as f:
    vectorizer, model = pickle.load(f)

# Gabungkan semua data kategori
image_map = {**image_map_makanan, **image_map_minuman, **image_map_sayur, **image_map_buah, **image_map_snack}
nutrition_info = {**nutrition_info_makanan, **nutrition_info_minuman, **nutrition_info_sayur, **nutrition_info_buah, **nutrition_info_snack}
category_map = {**category_map_makanan, **category_map_minuman, **category_map_sayur, **category_map_buah, **category_map_snack}
saran_sehat = {**saran_sehat_makanan, **saran_sehat_minuman, **saran_sehat_sayur, **saran_sehat_buah, **saran_sehat_snack}

manual_label_map = {
    "nasi goreng": "Tidak Sehat",
    "mie instan": "Tidak Sehat",
    "mie goreng": "Tidak Sehat",
    "sosis bakar": "Tidak Sehat",
    "captain morgan": "Tidak Sehat",
    "azul": "Tidak Sehat",
    "fanta anggur": "Tidak Sehat",
    "label 5": "Tidak Sehat",
    "chiki": "Tidak Sehat",
    "oreo": "Tidak Sehat",
    "kue cubit": "Sehat",
    "martabak": "Tidak Sehat",
    "keripik singkong": "Sehat",
    "chitato": "Tidak Sehat",
    "beng beng": "Tidak Sehat",
    "pisang coklat": "Tidak Sehat",
    "donat": "Tidak Sehat",
    "pentol": "Sehat",
    "salad": "Sehat",
    "bayam": "Sehat",
    "pisang": "Sehat",
    "brokoli": "Sehat",
    "sate": "Tidak Sehat",
    "soto": "Tidak Sehat",
    "rawon": "Tidak Sehat",
    "mie ayam": "Tidak Sehat",
    "gado gado": "Sehat",
    "bakso": "Tidak Sehat",
    "ayam goreng": "Tidak Sehat",
    "ayam geprek": "Tidak Sehat",
    "ayam bakar": "Sehat"
}

def get_match(makanan_input):
    for key in image_map:
        if key.lower() in makanan_input.lower():
            return key
    return None

def get_category_label(kategori_text):
    if not kategori_text:
        return None
    kategori_text = kategori_text.lower()
    if "minuman" in kategori_text:
        return "Minuman"
    elif "sayur" in kategori_text or "vegetable" in kategori_text:
        return "Sayur"
    elif "buah" in kategori_text or "fruit" in kategori_text:
        return "Buah"
    elif "snack" in kategori_text:
        return "Snack"
    elif "makanan" in kategori_text or "food" in kategori_text:
        return "Makanan"
    else:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    hasil = None
    makanan = ""
    gambar = "default.jpg"
    nutrisi = ""
    kategori = ""
    pesan = ""
    saran = ""
    status_kesehatan = ""
    show_button = False
    rekomendasi_saran = {}

    if request.method == 'POST' and 'dark_mode' in request.form:
        session['dark_mode'] = not session.get('dark_mode', False)
        return redirect(url_for('index'))

    dark_mode = session.get('dark_mode', False)

    if request.method == 'POST' and 'makanan' in request.form:
        makanan = request.form['makanan'].strip()

        if not makanan or len(makanan) < 3:
            pesan = "Mohon masukkan nama makanan yang valid."
        else:
            makanan_lower = makanan.lower()
            match_key = get_match(makanan)
            manual_result = None

            for key in manual_label_map:
                if key in makanan_lower:
                    manual_result = manual_label_map[key]
                    match_key = key
                    break

            try:
                if manual_result:
                    hasil = manual_result
                else:
                    makanan_bersih = clean_text(makanan)
                    X_input = vectorizer.transform([makanan_bersih])
                    prediksi = model.predict(X_input)[0]
                    hasil = prediksi

                status_kesehatan = "Sehat" if hasil.lower() == "sehat" else "Tidak Sehat"
                show_button = hasil.lower() == "tidak sehat"

                if match_key:
                    gambar = image_map.get(match_key, "default.jpg")
                    nutrisi = nutrition_info.get(match_key, "Informasi tidak tersedia.")
                    kategori = category_map.get(match_key, "Kategori tidak diketahui.")
                    saran = saran_sehat.get(match_key, "")
                    session['last_input'] = match_key

                    # Simpan riwayat
                    riwayat = Riwayat(nama_makanan=match_key, hasil=hasil, kategori=kategori)
                    db.session.add(riwayat)
                    db.session.commit()
                else:
                    gambar = "default.jpg"
                    nutrisi = "Informasi tidak tersedia."
                    kategori = "Kategori tidak dikenali."
                    saran = ""

                kategori_label = get_category_label(kategori)

                if hasil.lower() == "tidak sehat":
                    rekomendasi_saran = {
                        "Makanan": {k: v for k, v in saran_sehat_makanan.items() if k != match_key},
                        "Minuman": saran_sehat_minuman,
                        "Buah": saran_sehat_buah,
                        "Sayur": saran_sehat_sayur
                    }
                else:
                    rekomendasi_saran = {}

                pesan = f"{kategori_label} {status_kesehatan}" if kategori_label else status_kesehatan

            except Exception as e:
                pesan = f"Terjadi kesalahan: {e}"
                hasil = None
                gambar = "default.jpg"
                nutrisi = ""
                kategori = ""
                saran = ""
                show_button = False
                status_kesehatan = ""
                rekomendasi_saran = {}

    return render_template("index.html", hasil=hasil, makanan=makanan,
                           gambar=gambar, nutrisi=nutrisi,
                           kategori=kategori, pesan=pesan,
                           saran=saran, show_button=show_button,
                           dark_mode=dark_mode, status_kesehatan=status_kesehatan,
                           rekomendasi_saran=rekomendasi_saran)

@app.route('/saran', methods=['GET', 'POST'])
def saran_page():
    if request.method == 'POST' and 'dark_mode' in request.form:
        session['dark_mode'] = not session.get('dark_mode', False)
        return redirect(url_for('saran_page'))

    dark_mode = session.get('dark_mode', False)
    last_input = session.get('last_input')

    semua_saran = {
        "Makanan": saran_sehat_makanan,
        "Minuman": saran_sehat_minuman,
        "Sayur": saran_sehat_sayur,
        "Buah": saran_sehat_buah,
        "Snack": saran_sehat_snack
    }

    daftar_saran_terpilih = {}

    if last_input and last_input in saran_sehat:
        daftar_saran_terpilih["Makanan"] = {last_input: saran_sehat[last_input]}
    else:
        daftar_saran_terpilih["Makanan"] = {}

    for kategori in ["Minuman", "Sayur", "Buah"]:
        saran_kat = semua_saran.get(kategori, {})
        if saran_kat:
            nama_random = random.choice(list(saran_kat.keys()))
            daftar_saran_terpilih[kategori] = {nama_random: saran_kat[nama_random]}
        else:
            daftar_saran_terpilih[kategori] = {}

    return render_template("saran.html", daftar_saran=daftar_saran_terpilih, dark_mode=dark_mode)

@app.route('/riwayat')
def riwayat_page():
    dark_mode = session.get('dark_mode', False)
    daftar_riwayat = Riwayat.query.order_by(Riwayat.waktu.desc()).all()
    return render_template("riwayat.html", daftar_riwayat=daftar_riwayat, dark_mode=dark_mode)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
