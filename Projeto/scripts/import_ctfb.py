import csv
import sys
from pathlib import Path

# Adicionar diretório pai ao PATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from models import engine, create_db_and_tables, Animal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImportadorCTFB:
    def __init__(self):
        self.mapeamento_taxons = {}
        self.nomes_cientificos_vistos = set()
        self.ids_processados = set()
    
    def carregar_taxons(self, arquivo_taxon: str):
        """Carrega informações taxonômicas do arquivo taxon.txt"""
        logger.info(f"Carregando taxons de: {arquivo_taxon}")
        
        taxons = {}
        
        with open(arquivo_taxon, 'r', encoding='utf-8') as f:
            # Detectar delimitador
            primeira_linha = f.readline()
            f.seek(0)
            
            if '\t' in primeira_linha:
                delimiter = '\t'
            elif ';' in primeira_linha:
                delimiter = ';'
            else:
                delimiter = ','
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for linha in reader:
                taxon_id = linha.get('id')
                if not taxon_id:
                    continue
                
                try:
                    taxon_id = int(taxon_id)
                except:
                    continue
                
                nome_cientifico = linha.get('scientificName', '').strip()
                if not nome_cientifico:
                    continue
                
                taxons[taxon_id] = {
                    'id': taxon_id,
                    'scientificName': nome_cientifico,
                    'taxonRank': linha.get('taxonRank', '').strip().upper(),
                    'kingdom': linha.get('kingdom', '').strip(),
                    'phylum': linha.get('phylum', '').strip(),
                    'class': linha.get('class', '').strip(),
                    'order': linha.get('order', '').strip(),
                    'family': linha.get('family', '').strip(),
                    'genus': linha.get('genus', '').strip(),
                    'specificEpithet': linha.get('specificEpithet', '').strip(),
                    'parentNameUsageID': linha.get('parentNameUsageID', None),
                }
                
                # Converter parentNameUsageID
                if taxons[taxon_id]['parentNameUsageID']:
                    try:
                        taxons[taxon_id]['parentNameUsageID'] = int(taxons[taxon_id]['parentNameUsageID'])
                    except:
                        taxons[taxon_id]['parentNameUsageID'] = None
            
            logger.info(f"Carregados {len(taxons)} registros taxonômicos")
        
        return taxons
    
    def carregar_nomes_populares(self, arquivo_vernacular: str):
        """Carrega nomes populares do arquivo vernacularname.txt"""
        logger.info(f"Carregando nomes populares de: {arquivo_vernacular}")
        
        nomes_populares = {}
        
        try:
            with open(arquivo_vernacular, 'r', encoding='utf-8') as f:
                primeira_linha = f.readline()
                f.seek(0)
                
                delimiter = '\t' if '\t' in primeira_linha else ','
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for linha in reader:
                    try:
                        taxon_id = int(linha['id'])
                        nome = linha.get('vernacularName', '').strip()
                        idioma = linha.get('language', '').strip()
                        
                        if nome and idioma == 'PORTUGUES':
                            # Se já existe um nome, podemos manter o primeiro
                            # ou pegar o mais curto, etc.
                            if taxon_id not in nomes_populares:
                                nomes_populares[taxon_id] = nome
                    except:
                        continue
            
            logger.info(f"Carregados {len(nomes_populares)} nomes populares")
        
        except Exception as e:
            logger.error(f"Erro ao carregar nomes: {e}")
        
        return nomes_populares
    
    def eh_especie(self, taxon: dict) -> bool:
        """Verifica se o táxon é uma espécie"""
        rank = taxon.get('taxonRank', '').upper()
        ranks_validos = ['ESPECIE', 'SPECIES', 'SUBESPECIE', 'SUBSPECIES']
        return rank in ranks_validos
    
    def importar_animais(self, arquivo_taxon: str, arquivo_vernacular: str):
        """Importa animais usando dados dos dois arquivos"""
        
        # Criar tabelas se não existirem
        create_db_and_tables()
        
        # Carregar dados
        taxons = self.carregar_taxons(arquivo_taxon)
        nomes_populares = self.carregar_nomes_populares(arquivo_vernacular)
        
        if not taxons:
            logger.error("Nenhum dado taxonômico carregado!")
            return
        
        with Session(engine) as session:
            importados = 0
            ignorados_nao_especie = 0
            ignorados_duplicados = 0
            ja_existentes = 0
            batch = []
            BATCH_SIZE = 1000
            
            # Primeiro, vamos coletar TODOS os nomes já existentes no banco
            nomes_existentes = set()
            for animal in session.exec(select(Animal)).all():
                nomes_existentes.add(animal.nome_cientifico)
            
            logger.info(f"Já existem {len(nomes_existentes)} espécies no banco")
            
            # Processar cada táxon
            for taxon_id, taxon_data in taxons.items():
                nome_cientifico = taxon_data['scientificName']
                
                # 1. Pular se não tem nome científico
                if not nome_cientifico:
                    ignorados_nao_especie += 1
                    continue
                
                # 2. Pular se não é espécie
                if not self.eh_especie(taxon_data):
                    ignorados_nao_especie += 1
                    continue
                
                # 3. Pular se já vimos este nome nesta execução
                if nome_cientifico in self.nomes_cientificos_vistos:
                    ignorados_duplicados += 1
                    logger.debug(f"Duplicata ignorada: {nome_cientifico}")
                    continue
                
                # 4. Pular se já existe no banco
                if nome_cientifico in nomes_existentes:
                    ja_existentes += 1
                    continue
                
                # Marcar como visto
                self.nomes_cientificos_vistos.add(nome_cientifico)
                
                # Criar objeto Animal
                animal = Animal(
                    nome_cientifico=nome_cientifico[:200],
                    nome_popular=nomes_populares.get(taxon_id, None),
                    reino=taxon_data.get('kingdom', None),
                    filo=taxon_data.get('phylum', None),
                    classe=taxon_data.get('class', None),
                    ordem=taxon_data.get('order', None),
                    familia=taxon_data.get('family', None),
                    genero=taxon_data.get('genus', None),
                    especie=taxon_data.get('specificEpithet', None),
                )
                
                batch.append(animal)
                importados += 1
                
                # Inserir em lote
                if len(batch) >= BATCH_SIZE:
                    session.add_all(batch)
                    session.commit()
                    logger.info(f"📦 Lote salvo: {importados} espécies importadas...")
                    batch = []
            
            # Inserir restante
            if batch:
                session.add_all(batch)
                session.commit()
                logger.info(f"📦 Último lote: {len(batch)} espécies")
            
            logger.info(f"\n✅ Importação concluída!")
            logger.info(f"✓ Importadas: {importados}")
            logger.info(f"✓ Já existiam no banco: {ja_existentes}")
            logger.info(f"✓ Ignoradas (duplicatas no arquivo): {ignorados_duplicados}")
            logger.info(f"✓ Ignoradas (não são espécies): {ignorados_nao_especie}")
            logger.info(f"✓ Total no banco: {session.exec(select(Animal)).all().__len__()}")

def main():

    importador = ImportadorCTFB()
    importador.importar_animais("ctfb/taxon.txt", "ctfb/vernacularname.txt")

if __name__ == "__main__":
    main()