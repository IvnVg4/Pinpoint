import random
import re
import string
import unicodedata
from enum import Enum 

import nltk
from nltk.corpus import wordnet as wn


from nltk.corpus.reader.wordnet import Synset
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize


#Definimos los 3 estados posibles del juego
class EstadoJuego(Enum):
    JUGANDO = "jugando"
    GANADO = "ganado"
    PERDIDO = "perdido"

    
class Pista:
    def __init__(self, texto: str, relacion: str) -> None:
        self.texto = texto.strip()
        self.relacion = relacion.strip()
        
        
class Normalizador:
    def __init__(self, idioma: str) -> None:
        idiomas = {"spa":"spanish", "eng":"english"}
        self.idioma = idioma
        self.stemmer = SnowballStemmer(idiomas[idioma])
            
    def quitar_acentos(self, texto:str) -> None:
        reemplazos = {
                "á": "a",
                "é": "e",
                "í": "i",
                "ó": "o",
                "ú": "u",
                "Á": "A",
                "É": "E",
                "Í": "I",
                "Ó": "O",
                "Ú": "U",
            }
        for acento, letra in reemplazos.items():
            texto = texto.replace(acento,letra)
        return texto
    
    def quitar_puntuacion(self, texto: str):
        puntuacion = set(string.punctuation) | {"¡","¿"}
        return "".join(
            caracter
            for caracter in texto
            if caracter not in puntuacion
        )
    
    def tokens(self, texto: str) -> list[str]:
        idiomas = {"spa":"spanish", "eng":"english"}
        return word_tokenize(texto, language = idiomas [self.idioma])
    
    def normalizar(self, texto: str) -> str:
        texto = texto.lower()
        texto = self.quitar_acentos(texto)
        texto = self.quitar_puntuacion(texto)
        palabras = self.tokens(texto)
        raices = [self.stemmer.stem(palabra) for palabra in palabras]
        return " ".join(raices)
        
    
    
"""
        prueba de clase Normalizador
        
normalizador = Normalizador("spa")

texto = "¡Los jugadores están corriendo rápidamente!"

print("Texto original:")
print(texto)

print("\nSin acentos:")
print(normalizador.quitar_acentos(texto))

print("\nSin puntuación:")
print(normalizador.quitar_puntuacion(texto))

print("\nTokens:")
print(normalizador.tokens(texto))

print("\nNormalizado:")
print(normalizador.normalizar(texto))

"""

class GestorWordNet:
    BANCO_CATEGORIAS = [
    "computer.n.01",
    "snake.n.01",
    "dog.n.01",
    "sport.n.01",
    "pencil.n.01",
    ]

    def __init__(self, idioma: str) -> None:
        #aseguramos que solo sea ingles o español
        if idioma not in ("spa", "eng"):
            raise ValueError(f"Idioma no soportado: '{idioma}'. Usa 'spa' o 'eng'")
        self.idioma = idioma

    def elegir_categoria(self):
        elegibles = self.BANCO_CATEGORIAS[:]
        random.shuffle(elegibles)

        for identificador in elegibles:
            try:
                synset = wn.synset(identificador)
                pistas = self.construir_pistas(synset)
                return synset
            except (ValueError, LookupError):
                continue

        raise RuntimeError("Ninguna categoria del banco pudo generar 5 pistas")

    def nombres(self, synset) -> list[str]:
        nombres = []
        for lema in synset.lemma_names(self.idioma):
            nombre = lema.replace("_", " ")
            if nombre not in nombres:
                nombres.append(nombre)
        return nombres

    def sinonimos(self, synset) -> list[str]:
        return self.nombres(synset)[1:]

    def hiperonimos(self, synset) -> list[str]:
        directos = synset.hypernyms()
        lejanos = [abuelo for padre in directos for abuelo in padre.hypernyms()]

        hiperonimos = []
        for grupo in lejanos + directos:
            hiperonimos.extend(self.nombres(grupo))
        return hiperonimos

    def hiponimos(self, synset) -> list[str]:
        hiponimos = []
        for hiponimo in synset.hyponyms():
            hiponimos.extend(self.nombres(hiponimo))
        return hiponimos

    def construir_pistas(self, synset) -> list[Pista]:
        nombres = self.nombres(synset)
        if not nombres:
            raise ValueError(f"'{synset.name()}' no tiene nombre en '{self.idioma}'")
        respuesta = nombres[0].lower()

        usadas = []
        listas = []

        for palabras in (self.hiperonimos(synset), self.hiponimos(synset), self.sinonimos(synset)):
            filtradas = []
            for palabra in palabras:
                if respuesta not in palabra.lower() and palabra.lower() not in usadas:
                    usadas.append(palabra.lower())
                    filtradas.append(palabra)
            listas.append(filtradas)

        hiper, hipo, sino = listas

        if not hiper or not hipo or not sino:
            raise ValueError(f"'{synset.name()}' no tiene las tres relaciones en '{self.idioma}'")

        elegidos_hiper = [hiper[0], hiper[-1]] if len(hiper) > 1 else [hiper[0]]
        elegidos_hipo = hipo[:2]
        elegidos_sino = sino[:1]

        sobrantes_hipo = hipo[len(elegidos_hipo):]
        sobrantes_sino = sino[len(elegidos_sino):]
        sobrantes_hiper = [h for h in hiper if h not in elegidos_hiper]
        faltan = 5 - len(elegidos_hiper) - len(elegidos_hipo) - len(elegidos_sino)

        while faltan > 0 and (sobrantes_hipo or sobrantes_sino or sobrantes_hiper):
            if sobrantes_hipo:
                elegidos_hipo.append(sobrantes_hipo.pop(0))
            elif sobrantes_sino:
                elegidos_sino.append(sobrantes_sino.pop(0))
            else:
                elegidos_hiper.insert(-1, sobrantes_hiper.pop(0))
            faltan -= 1

        if faltan > 0:
            raise ValueError(f"'{synset.name()}' no alcanza para 5 pistas en '{self.idioma}'")

        return (
            [Pista(p, "hiperonimo") for p in elegidos_hiper]
            + [Pista(p, "hiponimo") for p in elegidos_hipo]
            + [Pista(p, "sinonimo") for p in elegidos_sino]
        )
   

"""

#Prueba de clase GestorWordNet

gestor = GestorWordNet("spa")
synset = gestor.elegir_categoria()
pistas = gestor.construir_pistas(synset)

print("respuesta: ", gestor.nombres(synset)[0])
for p in pistas:
    print(f"{p.relacion}: {p.texto}")
    
    
"""