import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Import data dari file
from data.makanan import image_map_makanan
from data.minuman import image_map_minuman
from data.sayur import image_map_sayur
from data.buah import image_map_buah
from data.snack import image_map_snack

# Gabungkan semua nama item
semua_nama = list(image_map_makanan.keys()) + list(image_map_minuman.keys()) + \
             list(image_map_sayur.keys()) + list(image_map_buah.keys()) + \
             list(image_map_snack.keys())

# Logika sederhana untuk pelabelan
tidak_sehat_keywords = ["goreng", "chiki", "martabak", "donat", "oreo", "chitato", "beng beng", "sosis", "kue", "keripik", "minuman soda", "Captain Morgan"]

data_latih = []
for nama in semua_nama:
    label = "tidak sehat" if any(k in nama.lower() for k in tidak_sehat_keywords) else "sehat"
    data_latih.append((nama.lower(), label))

# Pisahkan teks dan label
texts, labels = zip(*data_latih)

# Buat pipeline TF-IDF + Naive Bayes
pipeline = make_pipeline(TfidfVectorizer(), MultinomialNB())

# Latih model
pipeline.fit(texts, labels)

# Simpan model dan vectorizer
os.makedirs('model', exist_ok=True)
with open('model/food_model.pkl', 'wb') as f:
    pickle.dump((pipeline.named_steps['tfidfvectorizer'], pipeline.named_steps['multinomialnb']), f)

print("✅ Model berhasil dibuat dan disimpan di folder 'model'")
