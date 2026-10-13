# test_analisis.py
from scraper_chaco import buscar_noticias_chaco
from analyzer import analizar_noticia

n = buscar_noticias_chaco("Resistencia", max_resultados=3)
print(f"Noticias de Resistencia: {len(n)}")
print()

for noticia in n[:2]:
    print("---")
    print("Título:", noticia["titulo"][:80])
    resultado = analizar_noticia(noticia)
    print("Categoría:", resultado.get("categoria"))
    print("Score:", resultado.get("score"))
    print("Problemática:", resultado.get("problematica", "")[:100])
    print()