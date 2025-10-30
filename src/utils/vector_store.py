"""
Gestion de la base vectorielle (FAISS ou ChromaDB)
"""
from pathlib import Path
from typing import List, Optional, Any
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from src.config.settings import (
    VECTOR_STORE_DIR, 
    EMBEDDING_MODEL, 
    OPENAI_API_KEY,
    VECTOR_STORE_TYPE,
    TOP_K_RESULTS
)

# Import conditionnel selon configuration
if VECTOR_STORE_TYPE.lower() == "faiss":
    try:
        from langchain_community.vectorstores import FAISS as VectorStoreClass
    except ImportError:
        raise ImportError(
            "❌ FAISS n'est pas installé.\n"
            "Installez-le avec: pip install faiss-cpu"
        )
elif VECTOR_STORE_TYPE.lower() == "chroma":
    try:
        from langchain_community.vectorstores import Chroma as VectorStoreClass
    except ImportError:
        raise ImportError(
            "❌ ChromaDB n'est pas installé.\n"
            "Installez-le avec: pip install chromadb\n"
            "Note: Nécessite Microsoft Visual C++ Build Tools sur Windows"
        )
else:
    raise ValueError(
        f"❌ VECTOR_STORE_TYPE '{VECTOR_STORE_TYPE}' non supporté.\n"
        f"Valeurs acceptées: 'faiss', 'chroma'"
    )


class VectorStoreManager:
    """Gestionnaire de la base vectorielle (FAISS ou ChromaDB)"""
    
    def __init__(self):
        self.vector_store_type = VECTOR_STORE_TYPE.lower()
        
        # Chemin de stockage selon le type
        if self.vector_store_type == "faiss":
            self.vector_store_path = VECTOR_STORE_DIR / "faiss_index"
        else:  # chroma
            self.vector_store_path = VECTOR_STORE_DIR / "chroma_db"
        
        # Initialisation des embeddings
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Vector store (FAISS ou Chroma selon configuration)
        self.vector_store: Optional[Any] = None
        
        self._load_or_create()
        logger.info(f"✅ VectorStoreManager initialisé (type: {self.vector_store_type})")
    
    def _load_or_create(self):
        """Charge la base existante ou en crée une nouvelle"""
        if self.vector_store_path.exists():
            try:
                if self.vector_store_type == "faiss":
                    from langchain_community.vectorstores import FAISS
                    self.vector_store = FAISS.load_local(
                        str(self.vector_store_path),
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                elif self.vector_store_type == "chroma":
                    from langchain_community.vectorstores import Chroma
                    self.vector_store = Chroma(
                        persist_directory=str(self.vector_store_path),
                        embedding_function=self.embeddings
                    )
                
                doc_count = self.get_document_count()
                logger.info(
                    f"✅ Base vectorielle {self.vector_store_type.upper()} chargée "
                    f"depuis {self.vector_store_path} ({doc_count} chunks)"
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Impossible de charger la base existante: {e}. "
                    f"Création d'une nouvelle base."
                )
                self.vector_store = None
        else:
            logger.info(
                f"📝 Aucune base {self.vector_store_type.upper()} existante. "
                f"Sera créée au premier ajout."
            )
            self.vector_store = None
    
    def add_documents(self, documents: List[Document]) -> int:
        """
        Ajoute des documents à la base vectorielle
        
        Args:
            documents: Liste de documents LangChain
            
        Returns:
            Nombre de documents ajoutés
            
        Raises:
            Exception: Si erreur lors de l'ajout
        """
        if not documents:
            logger.warning("⚠️ Aucun document à ajouter")
            return 0
        
        try:
            if self.vector_store is None:
                # Créer la base pour la première fois
                logger.info(
                    f"🔨 Création de la base {self.vector_store_type.upper()} "
                    f"avec {len(documents)} documents..."
                )
                
                if self.vector_store_type == "faiss":
                    from langchain_community.vectorstores import FAISS
                    self.vector_store = FAISS.from_documents(documents, self.embeddings)
                elif self.vector_store_type == "chroma":
                    from langchain_community.vectorstores import Chroma
                    self.vector_store = Chroma.from_documents(
                        documents=documents,
                        embedding=self.embeddings,
                        persist_directory=str(self.vector_store_path)
                    )
                
                logger.info(f"✅ Nouvelle base créée avec {len(documents)} chunks")
            else:
                # Ajouter à la base existante
                logger.info(f"➕ Ajout de {len(documents)} documents à la base existante...")
                self.vector_store.add_documents(documents)
                logger.info(
                    f"✅ {len(documents)} chunks ajoutés "
                    f"(total: {self.get_document_count()})"
                )
            
            # Sauvegarder automatiquement
            self.save()
            return len(documents)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'ajout de documents: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """
        Recherche les documents les plus similaires à une requête
        
        Args:
            query: Question de l'utilisateur
            k: Nombre de résultats (par défaut: TOP_K_RESULTS depuis .env)
            
        Returns:
            Liste de documents pertinents (triés par similarité décroissante)
        """
        if self.vector_store is None:
            logger.warning("⚠️ Base vectorielle vide, aucune recherche possible")
            return []
        
        if not query or query.strip() == "":
            logger.warning("⚠️ Requête vide")
            return []
        
        # Utiliser TOP_K_RESULTS si k non spécifié
        if k is None:
            k = TOP_K_RESULTS
        
        try:
            logger.info(f"🔍 Recherche de similarité pour: '{query[:50]}...' (k={k})")
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"✅ {len(results)} résultats trouvés")
            
            # Log des sources trouvées
            if results:
                sources = set(doc.metadata.get("source", "Unknown") for doc in results)
                logger.debug(f"📚 Sources: {', '.join(sources)}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche: {e}")
            return []
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = None
    ) -> List[tuple[Document, float]]:
        """
        Recherche avec scores de similarité
        
        Args:
            query: Question de l'utilisateur
            k: Nombre de résultats (par défaut: TOP_K_RESULTS)
            
        Returns:
            Liste de tuples (Document, score)
        """
        if self.vector_store is None:
            logger.warning("⚠️ Base vectorielle vide")
            return []
        
        # Utiliser TOP_K_RESULTS si k non spécifié
        if k is None:
            k = TOP_K_RESULTS
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.info(f"✅ {len(results)} résultats avec scores trouvés")
            return results
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche avec score: {e}")
            return []
    
    def delete_by_source(self, source_name: str) -> bool:
        """
        Supprime tous les documents d'une source donnée
        
        Note: FAISS ne supporte pas la suppression native,
        donc on doit reconstruire la base sans les documents à supprimer
        
        Args:
            source_name: Nom du fichier source (ex: "contrat.txt")
            
        Returns:
            True si succès, False sinon
        """
        if self.vector_store is None:
            logger.warning("⚠️ Base vectorielle vide, rien à supprimer")
            return False
        
        try:
            logger.info(f"🗑️ Suppression des documents de la source: {source_name}")
            
            if self.vector_store_type == "chroma":
                # ChromaDB supporte la suppression native
                # Récupérer les IDs des documents à supprimer
                all_data = self.vector_store.get()
                ids_to_delete = [
                    doc_id 
                    for doc_id, metadata in zip(all_data['ids'], all_data['metadatas'])
                    if metadata.get('source') == source_name
                ]
                
                if ids_to_delete:
                    self.vector_store.delete(ids_to_delete)
                    logger.info(f"✅ {len(ids_to_delete)} chunks supprimés")
                    return True
                else:
                    logger.warning(f"⚠️ Aucun document trouvé avec la source: {source_name}")
                    return False
            
            else:  # FAISS
                # FAISS: reconstruire la base
                all_docs = self._get_all_documents()
                
                if not all_docs:
                    logger.warning("⚠️ Aucun document dans la base")
                    return False
                
                # Filtrer : garder tous SAUF ceux de la source à supprimer
                filtered_docs = [
                    doc for doc in all_docs 
                    if doc.metadata.get("source") != source_name
                ]
                
                deleted_count = len(all_docs) - len(filtered_docs)
                if deleted_count == 0:
                    logger.warning(f"⚠️ Aucun document trouvé avec la source: {source_name}")
                    return False
                
                # Reconstruire la base
                if filtered_docs:
                    logger.info(f"🔨 Reconstruction de la base avec {len(filtered_docs)} chunks...")
                    from langchain_community.vectorstores import FAISS
                    self.vector_store = FAISS.from_documents(filtered_docs, self.embeddings)
                    logger.info(
                        f"✅ {deleted_count} chunks supprimés. "
                        f"{len(filtered_docs)} chunks restants."
                    )
                else:
                    logger.info("📝 Plus aucun document, base vidée")
                    self.vector_store = None
                
                self.save()
                return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression: {e}")
            return False
    
    def _get_all_documents(self) -> List[Document]:
        """
        Récupère tous les documents de la base
        
        Utilisé pour la suppression (car FAISS ne permet pas la suppression directe)
        
        Returns:
            Liste de tous les documents
        """
        if self.vector_store is None:
            return []
        
        try:
            if self.vector_store_type == "faiss":
                # Accéder au docstore interne de FAISS
                docstore = self.vector_store.docstore
                all_docs = []
                
                # Parcourir tous les documents via index_to_docstore_id
                for doc_id in self.vector_store.index_to_docstore_id.values():
                    doc = docstore.search(doc_id)
                    if doc:
                        all_docs.append(doc)
                
                logger.debug(f"📋 {len(all_docs)} documents récupérés depuis FAISS")
                return all_docs
            
            elif self.vector_store_type == "chroma":
                # ChromaDB a une méthode get() directe
                results = self.vector_store.get()
                all_docs = []
                
                for doc_id, text, metadata in zip(
                    results['ids'], 
                    results['documents'], 
                    results['metadatas']
                ):
                    doc = Document(page_content=text, metadata=metadata)
                    all_docs.append(doc)
                
                logger.debug(f"📋 {len(all_docs)} documents récupérés depuis ChromaDB")
                return all_docs
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des documents: {e}")
            return []
    
    def get_document_count(self) -> int:
        """
        Retourne le nombre total de chunks dans la base
        
        Returns:
            Nombre de chunks (0 si base vide)
        """
        if self.vector_store is None:
            return 0
        
        try:
            if self.vector_store_type == "faiss":
                # FAISS stocke le nombre de vecteurs dans index.ntotal
                count = self.vector_store.index.ntotal
            elif self.vector_store_type == "chroma":
                # ChromaDB utilise la méthode count()
                count = self.vector_store._collection.count()
            
            return count
        except Exception as e:
            logger.error(f"❌ Erreur lors du comptage: {e}")
            return 0
    
    def get_all_sources(self) -> List[str]:
        """
        Retourne la liste de toutes les sources (noms de fichiers) dans la base
        
        Returns:
            Liste triée des noms de fichiers sources
        """
        if self.vector_store is None:
            return []
        
        try:
            all_docs = self._get_all_documents()
            
            # Extraire les sources uniques
            sources = set()
            for doc in all_docs:
                source = doc.metadata.get("source", "Unknown")
                sources.add(source)
            
            sorted_sources = sorted(list(sources))
            logger.debug(f"📚 Sources trouvées: {sorted_sources}")
            return sorted_sources
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des sources: {e}")
            return []
    
    def save(self):
        """
        Sauvegarde la base vectorielle sur disque
        
        FAISS crée les fichiers :
        - index.faiss : Index vectoriel
        - index.pkl : Métadonnées et docstore
        
        ChromaDB sauvegarde automatiquement dans persist_directory
        """
        if self.vector_store is None:
            logger.debug("📝 Aucune base à sauvegarder (base vide)")
            return
        
        try:
            # Créer le dossier si nécessaire
            self.vector_store_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.vector_store_type == "faiss":
                self.vector_store.save_local(str(self.vector_store_path))
            elif self.vector_store_type == "chroma":
                # ChromaDB sauvegarde automatiquement avec persist_directory
                self.vector_store.persist()
            
            logger.info(
                f"💾 Base {self.vector_store_type.upper()} sauvegardée "
                f"dans {self.vector_store_path}"
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            raise
    
    def clear(self):
        """
        Efface complètement la base vectorielle (mémoire + disque)
        """
        try:
            # Effacer de la mémoire
            self.vector_store = None
            
            # Supprimer les fichiers sur disque
            if self.vector_store_path.exists():
                import shutil
                shutil.rmtree(self.vector_store_path)
                logger.info(
                    f"🗑️ Base {self.vector_store_type.upper()} effacée "
                    f"(mémoire + disque)"
                )
            else:
                logger.info(
                    f"🗑️ Base {self.vector_store_type.upper()} effacée "
                    f"(mémoire uniquement)"
                )
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'effacement: {e}")
            raise
    
    def get_stats(self) -> dict:
        """
        Retourne des statistiques sur la base vectorielle
        
        Returns:
            Dictionnaire avec statistiques
        """
        if self.vector_store is None:
            return {
                "total_chunks": 0,
                "total_sources": 0,
                "sources": [],
                "status": "empty",
                "vector_store_type": self.vector_store_type,
                "embedding_model": EMBEDDING_MODEL,
                "top_k_results": TOP_K_RESULTS
            }
        
        try:
            sources = self.get_all_sources()
            return {
                "total_chunks": self.get_document_count(),
                "total_sources": len(sources),
                "sources": sources,
                "status": "ready",
                "vector_store_type": self.vector_store_type,
                "embedding_model": EMBEDDING_MODEL,
                "top_k_results": TOP_K_RESULTS
            }
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des stats: {e}")
            return {
                "total_chunks": 0,
                "total_sources": 0,
                "sources": [],
                "status": "error",
                "vector_store_type": self.vector_store_type,
                "embedding_model": EMBEDDING_MODEL,
                "top_k_results": TOP_K_RESULTS
            }