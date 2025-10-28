"""
Gestion de l'intégration LLM (OpenAI)
"""
from typing import List, Dict, Optional
from langchain.schema import Document, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from src.config.settings import (
    LLM_MODEL, 
    LLM_TEMPERATURE, 
    MAX_TOKENS, 
    OPENAI_API_KEY,
    TOP_K_RESULTS
)
from src.utils.vector_store import VectorStoreManager


class LLMHandler:
    """Gestionnaire des interactions avec le LLM"""
    
    # ✅ PROMPT SYSTÈME CENTRALISÉ (attribut de classe)
    SYSTEM_PROMPT = """Tu es un assistant juridique expert travaillant pour le cabinet d'avocats d'Emilia Parenti, spécialisé en droit des affaires à Paris.

RÈGLES STRICTES À RESPECTER :
1. Tu dois UNIQUEMENT répondre en te basant sur les documents fournis dans le CONTEXTE ci-dessous
2. Si l'information n'est PAS explicitement dans le contexte, tu dois dire clairement : "Je ne trouve pas cette information dans les documents disponibles"
3. Tu ne dois JAMAIS inventer, supposer ou déduire des informations qui ne sont pas explicitement dans le contexte
4. Cite toujours la source (nom du document) des informations que tu fournis
5. Sois précis, professionnel et concis dans tes réponses
6. Si la question est ambiguë, demande des clarifications
7. Utilise un langage juridique approprié mais reste compréhensible

FORMAT DE RÉPONSE :
- Réponds de manière claire et structurée
- Utilise des citations entre guillemets si nécessaire pour référencer le texte exact
- Indique toujours les sources à la fin de ta réponse : "Sources : [nom des documents]"
- Si plusieurs documents contiennent des informations pertinentes, synthétise-les de manière cohérente"""
    
    def __init__(self, vector_store_manager: VectorStoreManager):
        """
        Initialise le handler LLM
        
        Args:
            vector_store_manager: Instance du gestionnaire de base vectorielle
        """
        self.vector_store_manager = vector_store_manager
        
        # Initialiser le modèle LLM
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=MAX_TOKENS,
            openai_api_key=OPENAI_API_KEY
        )
        
        logger.info(
            f"✅ LLM Handler initialisé "
            f"(model: {LLM_MODEL}, temp: {LLM_TEMPERATURE}, max_tokens: {MAX_TOKENS})"
        )
    
    def generate_response(
        self, 
        question: str, 
        chat_history: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        Génère une réponse basée sur les documents vectorisés
        
        Args:
            question: Question de l'utilisateur
            chat_history: Historique de conversation (optionnel)
            
        Returns:
            Dictionnaire contenant answer, sources, relevant_chunks
        """
        try:
            # Vérifier si la base vectorielle contient des documents
            doc_count = self.vector_store_manager.get_document_count()
            if doc_count == 0:
                logger.warning("⚠️ Base vectorielle vide")
                return {
                    "answer": (
                        "❌ Aucun document n'a été chargé dans la base. "
                        "Veuillez d'abord uploader des documents dans la section "
                        "'📄 Gestion des Documents'."
                    ),
                    "sources": [],
                    "relevant_chunks": 0
                }
            
            logger.info(f"💬 Question reçue: '{question[:100]}...'")
            
            # Rechercher les documents pertinents
            relevant_docs = self.vector_store_manager.similarity_search(
                question, 
                k=TOP_K_RESULTS
            )
            
            if not relevant_docs:
                logger.warning("⚠️ Aucun document pertinent trouvé")
                return {
                    "answer": (
                        "❌ Aucun document pertinent trouvé pour répondre à votre question. "
                        "Essayez de reformuler ou vérifiez que les documents uploadés "
                        "contiennent des informations sur ce sujet."
                    ),
                    "sources": [],
                    "relevant_chunks": 0
                }
            
            logger.info(f"✅ {len(relevant_docs)} chunks pertinents trouvés")
            
            # Construire le contexte
            context = self._build_context(relevant_docs)
            
            # Construire le prompt
            messages = self._build_prompt(question, context, chat_history)
            
            # Appel au LLM
            logger.info(f"🤖 Appel au LLM ({LLM_MODEL})...")
            response = self.llm.invoke(messages)
            answer = response.content
            
            # Extraire les sources uniques
            sources = self._extract_sources(relevant_docs)
            
            logger.info(
                f"✅ Réponse générée avec succès "
                f"({len(answer)} caractères, {len(sources)} sources)"
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "relevant_chunks": len(relevant_docs)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération de réponse: {e}")
            return {
                "answer": f"❌ Erreur lors de la génération de la réponse: {str(e)}",
                "sources": [],
                "relevant_chunks": 0
            }
    
    def _build_context(self, documents: List[Document]) -> str:
        """
        Construit le contexte à partir des documents pertinents
        
        Args:
            documents: Liste de documents LangChain
            
        Returns:
            Contexte formaté pour le prompt
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "Unknown")
            chunk_index = doc.metadata.get("chunk_index", "?")
            content = doc.page_content.strip()
            
            context_parts.append(
                f"[Document {i} - Source: {source}, Chunk: {chunk_index}]\n{content}\n"
            )
        
        context = "\n".join(context_parts)
        logger.debug(f"📄 Contexte construit: {len(context)} caractères")
        
        return context
    
    def _build_prompt(
        self, 
        question: str, 
        context: str, 
        chat_history: Optional[List[Dict]] = None
    ) -> List:
        """
        Construit le prompt pour le LLM
        
        Args:
            question: Question de l'utilisateur
            context: Contexte des documents pertinents
            chat_history: Historique de conversation (optionnel)
            
        Returns:
            Liste de messages pour le LLM
        """
        # ✅ Utiliser le prompt système centralisé
        system_message = SystemMessage(content=self.SYSTEM_PROMPT)
        
        # Contenu de la question avec contexte
        user_content = f"""CONTEXTE (Documents juridiques disponibles) :
{context}

QUESTION DE L'UTILISATEUR :
{question}

Réponds à la question en te basant UNIQUEMENT sur le contexte ci-dessus. N'invente aucune information."""
        
        # Construction de la liste de messages
        messages = [system_message]
        
        # Ajouter l'historique si disponible (garder les 6 derniers messages = 3 échanges)
        if chat_history:
            for msg in chat_history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Ajouter la question actuelle
        messages.append(HumanMessage(content=user_content))
        
        logger.debug(f"💬 Prompt construit avec {len(messages)} messages")
        
        return messages
    
    def _extract_sources(self, documents: List[Document]) -> List[str]:
        """
        Extrait les sources uniques des documents
        
        Args:
            documents: Liste de documents
            
        Returns:
            Liste triée des sources uniques
        """
        sources = set()
        for doc in documents:
            source = doc.metadata.get("source", "Unknown")
            sources.add(source)
        
        sorted_sources = sorted(list(sources))
        logger.debug(f"📚 Sources extraites: {sorted_sources}")
        
        return sorted_sources
    
    def count_tokens(self, text: str) -> int:
        """
        Compte le nombre de tokens dans un texte (estimation)
        
        Args:
            text: Texte à analyser
            
        Returns:
            Nombre approximatif de tokens
        """
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(LLM_MODEL)
            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"⚠️ Impossible de compter les tokens: {e}. Estimation grossière.")
            # Estimation grossière : 1 token ≈ 4 caractères
            return len(text) // 4
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estime le coût d'un appel API (en dollars)
        
        Args:
            input_tokens: Nombre de tokens en entrée
            output_tokens: Nombre de tokens en sortie
            
        Returns:
            Coût estimé en dollars
        """
        # Prix approximatifs (à jour en janvier 2025)
        pricing = {
            "gpt-4o": {"input": 5.00, "output": 15.00},  # par 1M tokens
            "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        }
        
        # Utiliser les prix du modèle configuré ou valeurs par défaut
        model_pricing = pricing.get(LLM_MODEL, {"input": 10.00, "output": 30.00})
        
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        
        total_cost = input_cost + output_cost
        
        logger.debug(
            f"💰 Coût estimé: ${total_cost:.6f} "
            f"(input: {input_tokens} tokens, output: {output_tokens} tokens)"
        )
        
        return total_cost
    
    def validate_question(self, question: str) -> tuple[bool, str]:
        """
        Valide une question avant traitement
        
        Args:
            question: Question de l'utilisateur
            
        Returns:
            (is_valid, error_message)
        """
        # Vérifier que la question n'est pas vide
        if not question or question.strip() == "":
            return False, "La question ne peut pas être vide"
        
        # Vérifier la longueur minimale
        if len(question.strip()) < 3:
            return False, "La question est trop courte (minimum 3 caractères)"
        
        # Vérifier la longueur maximale
        if len(question) > 5000:
            return False, "La question est trop longue (maximum 5000 caractères)"
        
        # Vérifier qu'il y a au moins une lettre
        if not any(c.isalpha() for c in question):
            return False, "La question doit contenir au moins une lettre"
        
        return True, ""
    
    def get_system_prompt(self) -> str:
        """
        Retourne le prompt système utilisé par le LLM
        
        Utile pour :
        - Debugging
        - Affichage dans l'interface (optionnel)
        - Documentation
        
        Returns:
            Texte du prompt système
        """
        # ✅ Retourne LE VRAI prompt utilisé
        return self.SYSTEM_PROMPT