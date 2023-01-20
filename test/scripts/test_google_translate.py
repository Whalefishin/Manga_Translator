# from googletrans import Translator

# translator = Translator()
# translator.translate('안녕하세요.')
# translator.translate('僕は下僕を雇う主人として力を見せてやったんだ.', src='ja', dest='en')


# from google_trans_new import google_translator  
# translator = google_translator()  
# translate_text = translator.translate('สวัสดีจีน', lang_tgt='en')  
# print(translate_text)


from os import environ
from google.cloud import translate
import json

environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"cred/translation_sa_key.json"
project_id = json.load(open('cred/translation_project_settings.json'))['id']

# project_id = environ.get("PROJECT_ID", "")
# assert project_id

parent = f"projects/{project_id}"
client = translate.TranslationServiceClient()

sample_text = "Hello world!"
target_language_code = "tr"

response = client.translate_text(
    contents=[sample_text],
    target_language_code=target_language_code,
    parent=parent,
)

for translation in response.translations:
    print(translation.translated_text)