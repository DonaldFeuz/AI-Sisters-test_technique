"""
Page Streamlit : Interface de chat avec RAG
"""
import streamlit as st
from typing import List, Dict
from datetime import datetime
from loguru import logger

from src.utils.llm_handler import LLMHandler
from src.utils.vector_store import VectorStoreManager
from src.utils.conversation_manager import ConversationManager


def render_chat_interface(
    llm_handler: LLMHandler,
    vector_store_manager: VectorStoreManager,
    conversation_manager: ConversationManager
):
    """
    Affiche l'interface de chat
    
    Args:
        llm_handler: Gestionnaire LLM
        vector_store_manager: Gestionnaire de base vectorielle
        conversation_manager: Gestionnaire de conversations
    """
    st.title("💬 Chat avec vos Documents Juridiques")
    st.markdown("---")
    
    # Vérifier si des documents sont chargés
    doc_count = vector_store_manager.get_document_count()
    
    if doc_count == 0:
        _display_empty_state()
        return
    
    # Afficher les informations sur la base
    _display_database_info(vector_store_manager)
    
    st.markdown("---")
    
    # Initialiser l'historique de conversation
    _initialize_chat_state(conversation_manager)
    
    # Sidebar avec options ET historique
    _render_sidebar(llm_handler, conversation_manager)
    
    # Afficher l'historique de conversation
    _display_chat_history()
    
    # Zone de saisie utilisateur
    _render_chat_input(llm_handler, conversation_manager)


def _initialize_chat_state(conversation_manager: ConversationManager):
    """Initialise l'état de la conversation dans st.session_state"""
    
    # ID de la conversation courante
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = conversation_manager.generate_conversation_id()
        logger.info(f"🆕 Nouvelle conversation: {st.session_state.current_conversation_id}")
    
    # Historique de la conversation courante
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        logger.info("💬 Historique de conversation initialisé")
    
    # Compteur de messages
    if "message_count" not in st.session_state:
        st.session_state.message_count = 0
    
    # Flag pour savoir si modifié depuis dernière sauvegarde
    if "conversation_modified" not in st.session_state:
        st.session_state.conversation_modified = False


def _render_sidebar(llm_handler: LLMHandler, conversation_manager: ConversationManager):
    """Affiche la sidebar avec options, historique et informations"""
    with st.sidebar:
        st.header("⚙️ Options")
        
        # Bouton pour nouvelle conversation
        if st.button("🆕 Nouvelle Conversation", use_container_width=True):
            _save_current_conversation(conversation_manager)
            _start_new_conversation(conversation_manager)
            st.rerun()
        
        # Bouton pour sauvegarder
        if st.button("💾 Sauvegarder", use_container_width=True, disabled=not st.session_state.conversation_modified):
            if _save_current_conversation(conversation_manager):
                st.success("✅ Conversation sauvegardée !")
                st.session_state.conversation_modified = False
        
        st.markdown("---")
        
        # Historique des conversations
        st.subheader("📚 Historique")
        _display_conversation_history(conversation_manager)
        
        st.markdown("---")
        
        # Compteur de messages
        st.metric(
            "📨 Messages (conversation actuelle)",
            st.session_state.message_count
        )
        
        st.markdown("---")
        
        # Informations sur le modèle
        st.subheader("🤖 Configuration du Modèle")
        
        from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, MAX_TOKENS
        
        st.write(f"**Modèle :** `{LLM_MODEL}`")
        st.write(f"**Température :** `{LLM_TEMPERATURE}`")
        st.write(f"**Max Tokens :** `{MAX_TOKENS}`")
        
        st.markdown("---")
        
        # Afficher le prompt système (bonus)
        with st.expander("📋 Voir le Prompt Système"):
            st.code(llm_handler.get_system_prompt(), language="text")
        
        st.markdown("---")
        
        # Conseils d'utilisation
        with st.expander("💡 Conseils d'Utilisation"):
            st.markdown("""
            **Pour obtenir les meilleures réponses :**
            
            1. 🎯 Soyez précis dans vos questions
            2. 📝 Mentionnez le type de document si nécessaire
            3. 🔍 Utilisez des termes juridiques appropriés
            4. 💬 Posez des questions de suivi pour approfondir
            5. ✅ Vérifiez toujours les sources citées
            
            **Exemples de bonnes questions :**
            - "Quelle est la clause de confidentialité dans le contrat ?"
            - "Quelles sont les obligations des parties ?"
            - "Y a-t-il une durée mentionnée dans les documents ?"
            """)


def _display_conversation_history(conversation_manager: ConversationManager):
    """Affiche la liste des conversations sauvegardées"""
    conversations = conversation_manager.list_conversations()
    
    if not conversations:
        st.info("Aucune conversation sauvegardée")
        return
    
    st.write(f"**{len(conversations)} conversation(s) :**")
    
    for conv in conversations[:10]:  # Limiter à 10 pour ne pas surcharger
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Afficher titre avec indicateur si c'est la conversation courante
            is_current = conv["id"] == st.session_state.current_conversation_id
            prefix = "▶️ " if is_current else "📄 "
            
            if st.button(
                f"{prefix}{conv['title'][:30]}",
                key=f"load_{conv['id']}",
                use_container_width=True,
                type="primary" if is_current else "secondary"
            ):
                _load_conversation(conversation_manager, conv["id"])
                st.rerun()
        
        with col2:
            if st.button(
                "🗑️",
                key=f"delete_{conv['id']}",
                help="Supprimer",
                disabled=is_current  # Ne pas permettre de supprimer la conversation courante
            ):
                if conversation_manager.delete_conversation(conv["id"]):
                    st.success("✅ Supprimée")
                    st.rerun()
        
        # Afficher infos (petite taille)
        st.caption(f"💬 {conv['message_count']} msgs | 🕒 {conv['updated_at']}")


def _save_current_conversation(conversation_manager: ConversationManager) -> bool:
    """Sauvegarde la conversation courante"""
    if not st.session_state.chat_history:
        logger.info("⚠️ Aucun message à sauvegarder")
        return False
    
    success = conversation_manager.save_conversation(
        conversation_id=st.session_state.current_conversation_id,
        messages=st.session_state.chat_history
    )
    
    if success:
        st.session_state.conversation_modified = False
    
    return success


def _start_new_conversation(conversation_manager: ConversationManager):
    """Démarre une nouvelle conversation"""
    # Générer un nouvel ID
    st.session_state.current_conversation_id = conversation_manager.generate_conversation_id()
    st.session_state.chat_history = []
    st.session_state.message_count = 0
    st.session_state.conversation_modified = False
    
    logger.info(f"🆕 Nouvelle conversation démarrée: {st.session_state.current_conversation_id}")


def _load_conversation(conversation_manager: ConversationManager, conversation_id: str):
    """Charge une conversation existante"""
    # Sauvegarder la conversation courante si modifiée
    if st.session_state.conversation_modified:
        _save_current_conversation(conversation_manager)
    
    # Charger la conversation
    conversation_data = conversation_manager.load_conversation(conversation_id)
    
    if conversation_data:
        st.session_state.current_conversation_id = conversation_id
        st.session_state.chat_history = conversation_data["messages"]
        st.session_state.message_count = len(conversation_data["messages"])
        st.session_state.conversation_modified = False
        
        logger.info(f"📂 Conversation chargée: {conversation_id}")
    else:
        st.error("❌ Impossible de charger la conversation")


def _display_empty_state():
    """Affiche un message si aucun document n'est chargé"""
    st.info(
        "📭 **Aucun document chargé dans la base.**\n\n"
        "Pour commencer à poser des questions, veuillez d'abord uploader "
        "des documents dans la section **📄 Gestion des Documents**."
    )
    
    st.warning(
        "👈 Utilisez la navigation dans la **barre latérale** pour accéder à la gestion des documents."
    )


def _display_database_info(vector_store_manager: VectorStoreManager):
    """Affiche les informations sur la base de documents"""
    stats = vector_store_manager.get_stats()
    
    with st.expander("ℹ️ Informations sur la Base de Documents", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total Chunks", stats["total_chunks"])
        
        with col2:
            st.metric("📁 Documents", stats["total_sources"])
        
        with col3:
            st.metric("🔍 Top-K", stats["top_k_results"])
        
        if stats["sources"]:
            st.write("**📚 Documents disponibles :**")
            for source in stats["sources"]:
                st.write(f"- {source}")


def _display_chat_history():
    """Affiche l'historique de conversation"""
    if not st.session_state.chat_history:
        st.info("👋 Posez votre première question ci-dessous pour commencer !")
        return
    
    # Afficher chaque message
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Afficher les sources si disponibles (pour les réponses assistant)
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                with st.expander("📚 Sources utilisées"):
                    for source in message["sources"]:
                        st.write(f"- {source}")
            
            # Afficher le timestamp
            if "timestamp" in message:
                st.caption(f"🕒 {message['timestamp']}")


def _render_chat_input(llm_handler: LLMHandler, conversation_manager: ConversationManager):
    """Zone de saisie pour les questions utilisateur"""
    
    # Input utilisateur
    user_question = st.chat_input(
        "Posez votre question sur les documents juridiques...",
        key="chat_input"
    )
    
    if user_question:
        _process_user_question(user_question, llm_handler, conversation_manager)


def _process_user_question(
    question: str, 
    llm_handler: LLMHandler,
    conversation_manager: ConversationManager
):
    """Traite la question de l'utilisateur et génère une réponse"""
    
    # Valider la question
    is_valid, error_msg = llm_handler.validate_question(question)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    # Ajouter la question à l'historique
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.chat_history.append({
        "role": "user",
        "content": question,
        "timestamp": timestamp
    })
    st.session_state.message_count += 1
    st.session_state.conversation_modified = True
    
    # Afficher la question immédiatement
    with st.chat_message("user"):
        st.markdown(question)
        st.caption(f"🕒 {timestamp}")
    
    # Générer la réponse
    with st.chat_message("assistant"):
        with st.spinner("🤔 Recherche dans les documents..."):
            # Préparer l'historique pour le LLM (sans les métadonnées)
            chat_history_for_llm = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.chat_history[:-1]  # Exclure la dernière question
            ]
            
            # Générer la réponse
            response = llm_handler.generate_response(
                question=question,
                chat_history=chat_history_for_llm
            )
            
            # Afficher la réponse
            st.markdown(response["answer"])
            
            # Afficher les sources
            if response["sources"]:
                with st.expander("📚 Sources utilisées", expanded=True):
                    for source in response["sources"]:
                        st.write(f"- {source}")
                
                # Afficher le nombre de chunks utilisés
                st.caption(f"🔍 {response['relevant_chunks']} chunks pertinents utilisés")
            
            # Timestamp
            response_timestamp = datetime.now().strftime("%H:%M:%S")
            st.caption(f"🕒 {response_timestamp}")
    
    # Ajouter la réponse à l'historique
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response["answer"],
        "sources": response["sources"],
        "timestamp": response_timestamp
    })
    st.session_state.message_count += 1
    st.session_state.conversation_modified = True
    
    logger.info(
        f"💬 Question traitée: '{question[:50]}...' | "
        f"Réponse: {len(response['answer'])} caractères | "
        f"Sources: {len(response['sources'])}"
    )
    
    # Sauvegarde automatique après chaque échange
    _save_current_conversation(conversation_manager)