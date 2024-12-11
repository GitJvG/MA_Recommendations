import nltk
import os

def setup():
    appdata_path = os.environ.get('APPDATA')
    nltk_data_dir = os.path.join(appdata_path, 'nltk_data')

    required_resources = ['wordnet', 'omw-1.4']

    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir)

    for resource in required_resources:
        resource_path = os.path.join(nltk_data_dir, 'corpora', f"{resource}.zip")
        if not os.path.exists(resource_path):
            print(resource_path)
            print(f"Downloading NLTK resource: {resource}")
            nltk.download(resource, download_dir=nltk_data_dir)
        else:
            print(f"NLTK resource {resource} is already downloaded.")