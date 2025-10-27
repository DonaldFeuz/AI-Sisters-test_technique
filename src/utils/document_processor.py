"""
Traitement et nettoyage des documents
"""
import re
from pathlib import Path
from typing import List, Dict
import chardet
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from loguru import logger

from src.config.settings import CHUNK_SIZE, CHUNK_OVERLAP


class DocumentProcessor:
    """Classe pour traiter et nettoyer les documents"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        logger.info(
            f"DocumentProcessor initialisé (chunk_size={CHUNK_SIZE}, "
            f"chunk_overlap={CHUNK_OVERLAP})"
        )
    
    def load_document(self, file_path: Path) -> str:
        """
        Charge un document selon son extension
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Contenu du fichier en texte brut
        """
        extension = file_path.suffix.lower()
        
        try:
            if extension == ".txt":
                return self._load_txt(file_path)
            elif extension == ".csv":
                return self._load_csv(file_path)
            elif extension == ".html":
                return self._load_html(file_path)
            else:
                raise ValueError(f"Extension non supportée: {extension}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {file_path.name}: {e}")
            raise
    
    def _load_txt(self, file_path: Path) -> str:
        """Charge un fichier texte avec détection d'encodage"""
        # Détecter l'encodage
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] or 'utf-8'
        
        logger.debug(f"Encodage détecté pour {file_path.name}: {encoding}")
        
        # Lire avec l'encodage détecté
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        
        logger.info(f"Fichier TXT chargé: {file_path.name} ({len(content)} caractères)")
        return content
    
    def _load_csv(self, file_path: Path) -> str:
        """Charge un fichier CSV et le convertit en texte"""
        import pandas as pd
        
        try:
            # Essayer de lire le CSV
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Convertir le DataFrame en texte formaté
            text_parts = []
            
            # Ajouter les en-têtes
            headers = " | ".join(df.columns)
            text_parts.append(f"=== En-têtes ===\n{headers}\n")
            
            # Ajouter chaque ligne
            for idx, row in df.iterrows():
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
                text_parts.append(f"Ligne {idx + 1}: {row_text}")
            
            content = "\n".join(text_parts)
            logger.info(
                f"Fichier CSV chargé: {file_path.name} "
                f"({len(df)} lignes, {len(df.columns)} colonnes)"
            )
            return content
            
        except Exception as e:
            logger.warning(f"Erreur lors de la lecture CSV structurée: {e}. Lecture brute.")
            # Fallback : lecture brute
            return self._load_txt(file_path)
    
    def _load_html(self, file_path: Path) -> str:
        """Charge un fichier HTML et extrait le texte"""
        # Lire le contenu HTML
        html_content = self._load_txt(file_path)
        
        # Parser avec BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Supprimer scripts, styles et autres éléments non pertinents
        for element in soup(["script", "style", "meta", "link", "noscript"]):
            element.decompose()
        
        # Extraire le texte
        text = soup.get_text(separator="\n")
        
        logger.info(f"Fichier HTML chargé: {file_path.name} ({len(text)} caractères)")
        return text
    
    def clean_text(self, text: str) -> str:
        """
        Nettoie le texte
        
        Args:
            text: Texte brut
            
        Returns:
            Texte nettoyé
        """
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Normaliser les espaces multiples
        text = re.sub(r' +', ' ', text)
        
        # Normaliser les sauts de ligne multiples
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Supprimer les lignes vides au début et à la fin
        text = text.strip()
        
        logger.debug(f"Texte nettoyé: {len(text)} caractères")
        return text
    
    def split_into_chunks(self, text: str, metadata: Dict = None) -> List[Document]:
        """
        Découpe le texte en chunks
        
        Args:
            text: Texte à découper
            metadata: Métadonnées à attacher aux chunks
            
        Returns:
            Liste de Documents LangChain
        """
        # Nettoyer le texte
        clean_text = self.clean_text(text)
        
        if not clean_text:
            logger.warning("Texte vide après nettoyage")
            return []
        
        # Créer les chunks
        chunks = self.text_splitter.create_documents(
            texts=[clean_text],
            metadatas=[metadata or {}]
        )
        
        logger.info(f"Document découpé en {len(chunks)} chunks")
        
        # Ajouter des métadonnées supplémentaires à chaque chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)
        
        return chunks
    
    def process_file(self, file_path: Path) -> List[Document]:
        """
        Pipeline complet de traitement d'un fichier
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Liste de Documents prêts pour la vectorisation
        """
        logger.info(f"🔄 Début du traitement: {file_path.name}")
        
        try:
            # 1. Charger le contenu
            text = self.load_document(file_path)
            
            if not text or len(text.strip()) == 0:
                logger.warning(f"Fichier vide: {file_path.name}")
                return []
            
            # 2. Créer les métadonnées
            metadata = {
                "source": file_path.name,
                "file_path": str(file_path),
                "extension": file_path.suffix,
                "file_size": file_path.stat().st_size
            }
            
            # 3. Découper en chunks
            chunks = self.split_into_chunks(text, metadata)
            
            logger.info(
                f"✅ Traitement terminé: {file_path.name} "
                f"({len(chunks)} chunks créés)"
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de {file_path.name}: {e}")
            raise
    
    def validate_file(self, file_path: Path, max_size_mb: int = 10) -> tuple[bool, str]:
        """
        Valide un fichier avant traitement
        
        Args:
            file_path: Chemin vers le fichier
            max_size_mb: Taille maximale en MB
            
        Returns:
            (is_valid, error_message)
        """
        # Vérifier l'existence
        if not file_path.exists():
            return False, "Le fichier n'existe pas"
        
        # Vérifier l'extension
        from src.config.settings import SUPPORTED_EXTENSIONS
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False, f"Extension non supportée. Utilisez: {', '.join(SUPPORTED_EXTENSIONS)}"
        
        # Vérifier la taille
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"Fichier trop volumineux ({size_mb:.1f}MB). Maximum: {max_size_mb}MB"
        
        # Vérifier que ce n'est pas un dossier
        if file_path.is_dir():
            return False, "Ceci est un dossier, pas un fichier"
        
        return True, ""