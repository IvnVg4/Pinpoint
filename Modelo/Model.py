"""
Autores: 

Lopez Maldonado Alejandro
Rojas Meneses Emily Victoria
Unzueta Amador Zyanya Valeria
Vega Escobar Hector Ivan

https://github.com/IvnVg4/Pinpoint

"""



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

    #Inicializamos pista que conta de la palabra y que tipo de relacion tiene con la respuesta (hiper,hipo o sino)
class Pista:
    def __init__(self, texto: str, relacion: str) -> None:
        self.texto = texto.strip()
        self.relacion = relacion.strip()
        
    #Clase que se encarga de normalizar las palabras con las que vamos a trabajar o evaluar
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

    #tokenizamos con nltk
    def tokens(self, texto: str) -> list[str]:
        idiomas = {"spa":"spanish", "eng":"english"}
        return word_tokenize(texto, language = idiomas [self.idioma])

    #normalizamos las palabras convinando las funciones previamente declaradas
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
    def __init__(self, idioma: str) -> None:
        #aseguramos que solo sea ingles o español
        if idioma not in ("spa", "eng"):
            raise ValueError(f"Idioma no soportado: '{idioma}'. Usa 'spa' o 'eng'")
        self.idioma = idioma

        #Elige una categoria al azar
    def elegir_categoria(self):
        elegibles = list(wn.all_synsets(pos="n"))
        random.shuffle(elegibles)

        for synset in elegibles:
            try:
                self.construir_pistas(synset)
                return synset
            except (ValueError, LookupError):
                continue

        raise RuntimeError("WordNet no encontro una categoria con 5 pistas validas")

    
    #Limpia los nombres dentro del synset para generar limpiamente las palabras para que se muestren en las pistas o respuestas
    def nombres(self, synset) -> list[str]:
        nombres = []
        for lema in synset.lemma_names(self.idioma):
            nombre = lema.replace("_", " ")
            if nombre not in nombres:
                nombres.append(nombre)
        return nombres

    #Genera los sinonimos eliminando el primer elemento de la lista
    def sinonimos(self, synset) -> list[str]:
        return self.nombres(synset)[1:]

    #Genera los hiperonimos
    def hiperonimos(self, synset) -> list[str]:
        directos = synset.hypernyms()
        lejanos = [abuelo for padre in directos for abuelo in padre.hypernyms()]

        hiperonimos = []
        for grupo in lejanos + directos:
            hiperonimos.extend(self.nombres(grupo))
        return hiperonimos
        
    #Gnera hiponimos del synset
    def hiponimos(self, synset) -> list[str]:
        hiponimos = []
        for hiponimo in synset.hyponyms():
            hiponimos.extend(self.nombres(hiponimo))
        return hiponimos

    #Construye las pistas pistas que se mostraran, desde la mas general hasta la mas cercana
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

        #Armado ideal 2 hiperonimos, 2 hiponimos y 1 sinonimo
        elegidos_hiper = [hiper[0], hiper[-1]] if len(hiper) > 1 else [hiper[0]]
        elegidos_hipo = hipo[:2]
        elegidos_sino = sino[:1]

        #Agregamos en listas los sobrantes por si a caso los ocupamos
        sobrantes_hipo = hipo[len(elegidos_hipo):]
        sobrantes_sino = sino[len(elegidos_sino):]
        sobrantes_hiper = [h for h in hiper if h not in elegidos_hiper]

        #Verificamos si tenemos las 5 pistas para poder jugar
        faltan = 5 - len(elegidos_hiper) - len(elegidos_hipo) - len(elegidos_sino)
        
        #Agregamos "sustitutos" para llenar los espacios vacios
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

class Partida:
    def __init__(self) -> None:
        self.idioma : str = ""
        self.normalizador : Normalizador = None
        self.wordnet : GestorWordNet = None
        self.respuesta: str = ""
        self.pistas: list[Pista] = []
        self.pistas_mostradas: int = 0
        self.intentos: int = 0
        self.estado: EstadoJuego = EstadoJuego.JUGANDO

    def iniciar_juego(self, idioma: str) -> None:
        self.idioma = idioma
        self.normalizador = Normalizador(self.idioma)
        self.wordnet = GestorWordNet(self.idioma)

        synset = self.wordnet.elegir_categoria()
        self.respuesta = self.wordnet.nombres(synset)[0]
        self.pistas = self.wordnet.construir_pistas(synset)

        self.pistas_mostradas = 0
        self.intentos = 0
        self.estado = EstadoJuego.JUGANDO

    def obtener_pista(self) -> Pista:
        if self.pistas_mostradas < len(self.pistas):
            pista = self.pistas[self.pistas_mostradas]
            self.pistas_mostradas += 1
            return pista
        return None

    def verificar_respuesta(self, respuesta:str) -> bool:
        if self.estado != EstadoJuego.JUGANDO:
            return False

        self.intentos +=1

        respuesta_norm = self.normalizador.normalizar(respuesta)
        correcta_norm = self.normalizador.normalizar(self.respuesta)

        if respuesta_norm == correcta_norm:
            self.estado = EstadoJuego.GANADO
            return True
        else:
            if self.intentos >=5:
                self.estado = EstadoJuego.PERDIDO
            return False

    def obtener_estado(self) -> dict:
        return {
            "idioma" : self.idioma,
            "estado" : self.estado.value,
            "intentos" : self.intentos,
            "pistas_mostradas": self.pistas_mostradas,
            "respuesta" : self.respuesta if self.estado != EstadoJuego.JUGANDO else None
    }

    def mostrar_intentos(self, intentos=None):
        return f"Intentos realizados: {self.intentos}"
    
    
