# Pinpoint

## Ejecutar

Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Descarga los recursos de NLTK una vez:

```powershell
python -c "import nltk; [nltk.download(r) for r in ('wordnet', 'omw-1.4', 'omw-2.0', 'punkt', 'punkt_tab')]"
```

Inicia la aplicación:

```powershell
python Controlador\app.py
```

Luego abre `http://127.0.0.1:5000`.