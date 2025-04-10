import os
import joblib
import numpy as np
from PIL import Image
from io import BytesIO
import requests
import gdown
from django.conf import settings
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input as preprocess_input_resnet50
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model
from datetime import datetime
from datetime import datetime
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.text import slugify

# === 1. Constantes ===
DATASET_NAME = "HAM10000_Dataset_bdnvabm_split_80_2_128_128"
METHODE = "ResNet50"

# === 2. Fonction de téléchargement si besoin ===
def download_model(url, path):
    if not path.exists() or path.stat().st_size < 1000:
        print(f"⬇️ Téléchargement de {path.name}...")
        try:
            gdown.download(url, str(path), quiet=False)
        except Exception as e:
            print(f"❌ Échec du téléchargement : {e}")

# === 3. Télécharger les modèles si absents ===
MODEL_BM_PATH = settings.MODELS_DIR / f"model_{DATASET_NAME.replace('_bdnvabm_', '_bm_')}_{METHODE}_bm.pkl"
download_model(settings.MODEL_BM_URL, MODEL_BM_PATH)

MODEL_BDNV_PATH = settings.MODELS_DIR / f"model_{DATASET_NAME.replace('_bdnvabm_', '_bdnv_')}_{METHODE}_bdnv.pkl"
download_model(settings.MODEL_BDNV_URL, MODEL_BDNV_PATH)

MODEL_ABM_PATH = settings.MODELS_DIR / f"model_{DATASET_NAME.replace('_bdnvabm_', '_abm_')}_{METHODE}_abm.pkl"
download_model(settings.MODEL_ABM_URL, MODEL_ABM_PATH)

PCA_PATH = settings.MODELS_DIR / f"pca_{DATASET_NAME}_{METHODE}_bdnvabm.pkl"
download_model(settings.MODEL_PCA_URL, PCA_PATH)


# === 4. Chargement des modèles ===
try:
    MODEL_BM = joblib.load(MODEL_BM_PATH)
    MODEL_BDNV = joblib.load(MODEL_BDNV_PATH)
    MODEL_ABM = joblib.load(MODEL_ABM_PATH)
    PCA_MODEL = joblib.load(PCA_PATH)
    print("✅ Tous les modèles ont été chargés avec succès.")
except Exception as e:
    MODEL_BM = MODEL_BDNV = MODEL_ABM = PCA_MODEL = None
    print(f"❌ Erreur de chargement des modèles : {e}")

# === 5. Charger ResNet50 une seule fois ===
BASE_MODEL_RESNET = ResNet50(weights='imagenet', include_top=False)
FEATURE_MODEL_RESNET = Model(inputs=BASE_MODEL_RESNET.input, outputs=BASE_MODEL_RESNET.output)

# === 6. Fonction d'extraction des features ===
def extract_features_resnet50(pil_img, target_size=(128, 128)):
    img = pil_img.resize(target_size)
    img_data = image.img_to_array(img)
    img_data = np.expand_dims(img_data, axis=0)
    img_data = preprocess_input_resnet50(img_data)
    features = FEATURE_MODEL_RESNET.predict(img_data)
    return features.flatten()

# === 7. Fonction principale de prédiction ===
def predict(pil_image):
    try:
        if None in [MODEL_BM, MODEL_BDNV, MODEL_ABM, PCA_MODEL]:
            print("❌ Les modèles ne sont pas chargés correctement.")
            return None

        features = extract_features_resnet50(pil_image)
        if features is None:
            print("❌ Échec de l'extraction des caractéristiques")
            return None

        features = np.array([features])
        reduced_features = PCA_MODEL.transform(features)

        prediction_bm = MODEL_BM.predict(reduced_features)[0]

        if prediction_bm == 0:  # bénin
            prediction_bdnv = MODEL_BDNV.predict(reduced_features)[0]
            predictions = {0: 'Kératose', 1: 'Dermatofibrome', 2: 'Naevus', 3: 'Lésion vasculaire'}
            return predictions.get(prediction_bdnv, 'inconnu')
        else:  # malin
            prediction_abm = MODEL_ABM.predict(reduced_features)[0]
            predictions = {0: 'Kératose actinique', 1: 'Carcinome basocellulaire', 2: 'Mélanome'}
            return predictions.get(prediction_abm, 'inconnu')

    except Exception as e:
        print(f"❌ Erreur dans predict() : {e}")
        return None

# === 8. Prédiction depuis une URL ===
def predict_diagnostic_from_url(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        pil_image = Image.open(BytesIO(response.content)).convert("RGB")
        result = predict(pil_image)
        return result or "inconnu"
    except Exception as e:
        print(f"❌ Erreur dans predict_diagnostic_from_url : {e}")
        return "erreur"

# === 9. Prédiction depuis fichier local ===
def predict_diagnostic_from_file(image_path):
    try:
        pil_image = Image.open(image_path).convert("RGB")
        result = predict(pil_image)
        return result or "inconnu"
    except Exception as e:
        print(f"❌ Erreur dans predict_diagnostic_from_file : {e}")
        return "erreur"

# === 10. Test automatique au démarrage ===
def test_prediction_on_startup():
    test_image_path = r"C:\Users\Saifon\Downloads\Images test\Images test\ISIC_0024308.jpg"
    result = predict_diagnostic_from_file(test_image_path)
    print(f"🧠 Prédiction automatique au démarrage : {result}")



def handle_uploaded_image(uploaded_file, diagnostic_result):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S%f")[:-3]
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    original_name = os.path.splitext(uploaded_file.name)[0]
    safe_name = slugify(f"{original_name[:20]}_{timestamp}")
    new_filename = f"{diagnostic_result}_{safe_name}{file_ext}"

    uploaded_file.seek(0)  # revenir au début du flux

    return SimpleUploadedFile(
        name=new_filename,
        content=uploaded_file.read(),
        content_type=uploaded_file.content_type
    ), new_filename

