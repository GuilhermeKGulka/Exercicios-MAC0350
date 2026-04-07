import httpx, logging, re
from typing import Optional, Dict
from urllib.parse import quote
from sqlmodel import Session
from models import Animal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Pega a chave User-Agent para ser usada no header da API da wikimedia
def get_user_agent():
    with open("env.txt", "r") as f:
        return f.read().split("=")[1]
    
async def api_img_search(animal: Animal, session: Session) -> Optional[Dict]:
    #Se ja esta salva no banco, pega o url diretamente sem request
    if animal.img_url:
        return {"img_url": animal.img_url, "img_author": animal.img_author}

    #Usa apenas genero e especie para busca
    especie = f"{animal.genero} {animal.epitetoEspecifico}"
    usage_key = animal.gbif_id
    
    #Se uma usage key ja esta salva, mas nenhuma imagem, a request ja foi feita anteriormente, e nao encontrou nenhuma imagem, nao tentamos repeti-la
    if usage_key:
        return None

    headers = {"User-Agent": get_user_agent()}

    #Tentamos encontrar imagem na wikimedia
    try:
        # 1. Tenta buscar a página pelo nome científico
        wiki_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageimages",
            "piprop": "original",
            "titles": especie,
            "redirects": 1
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(wiki_url, params=params, headers=headers)
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "original" in page_data:
                    img_url = page_data["original"]["source"]
                    img_author = "Wikimedia Commons"
                    
                    return salvar_no_banco(animal, session, img_url, img_author)
                    
    except Exception as e:
        print(f"Erro na busca Wikimedia para {especie}: {e}")

    #Se nao foi encontrado na wikimedia tentamos na GBIF (imagens de menor qualidade mas de especies mais raras)
    async with httpx.AsyncClient() as client:
        try:
            match_res = await client.get(f"https://api.gbif.org/v1/species/match?name={quote(especie)}")
            usage_key = match_res.json().get("usageKey")
            animal.gbif_id = usage_key

            if usage_key: 
                params_gbif = [
                    ("taxonKey", usage_key), 
                    ("mediaType", "StillImage"), 
                    ("limit", "1")
                ]
                res_g = await client.get("https://api.gbif.org/v1/occurrence/search", params=params_gbif)
                results = res_g.json().get("results", [])
                if results and results[0].get("media"):
                    media = results[0]["media"][0]

                    img_author = media.get("publisher") or media.get("rightsHolder") or "GBIF"
                    img_url = media["identifier"]

                    return salvar_no_banco(animal, session, img_url, img_author)
            return salvar_no_banco(animal, session, None, None)
        except Exception as e:
            logging.error(f"Erro GBIF: {e}")

def salvar_no_banco(animal, session, img_url, img_author):
    animal.img_url = img_url
    animal.img_author = img_author
    session.add(animal)
    session.commit()
    session.refresh(animal)
    return {"img_url": img_url, "img_author": img_author}