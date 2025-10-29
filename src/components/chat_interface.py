"""
Page Streamlit : Interface de chat avec RAG
Version améliorée avec design moderne et historique persistant
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
    Affiche l'interface de chat avec design amélioré
    
    Args:
        llm_handler: Gestionnaire LLM
        vector_store_manager: Gestionnaire de base vectorielle
        conversation_manager: Gestionnaire de conversations
    """
    # Header avec style
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%); 
                    border-radius: 16px; margin-bottom: 2rem; color: white;'>
            <h1 style='color: white; margin: 0; font-size: 2.5rem;'>💬 Chat Juridique Intelligent</h1>
            <p style='color: rgba(255,255,255,0.9); margin-top: 0.5rem; font-size: 1.1rem;'>
                Posez vos questions, obtenez des réponses précises avec sources
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Vérifier si des documents sont chargés
    doc_count = vector_store_manager.get_document_count()
    
    if doc_count == 0:
        _display_empty_state()
        return
    
    # Afficher les informations sur la base (version compacte)
    _display_database_info_compact(vector_store_manager)
    
    # Initialiser l'historique de conversation
    _initialize_chat_state(conversation_manager)
    
    # Bouton "Nouvelle conversation" dans la page principale
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🆕 Nouvelle Conversation", use_container_width=True, type="secondary"):
            _save_current_conversation(conversation_manager)
            _start_new_conversation(conversation_manager)
            st.rerun()
    
    st.markdown("---")
    
    # Afficher l'historique de conversation
    _display_chat_history_styled()
    
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
        logger.info(f"💾 Conversation sauvegardée: {st.session_state.current_conversation_id}")
    
    return success


def _start_new_conversation(conversation_manager: ConversationManager):
    """Démarre une nouvelle conversation"""
    # Générer un nouvel ID
    st.session_state.current_conversation_id = conversation_manager.generate_conversation_id()
    st.session_state.chat_history = []
    st.session_state.message_count = 0
    st.session_state.conversation_modified = False
    
    logger.info(f"🆕 Nouvelle conversation démarrée: {st.session_state.current_conversation_id}")


def _display_empty_state():
    """État vide stylisé quand aucun document n'est chargé"""
    st.markdown("""
        <div style='text-align: center; padding: 4rem 2rem; background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); 
                    border-radius: 16px; margin: 2rem 0;'>
            <div style='font-size: 5rem; margin-bottom: 1rem;'>📭</div>
            <h2 style='color: #92400E; margin-bottom: 1rem;'>Aucun document chargé</h2>
            <p style='color: #78350F; font-size: 1.1rem; margin-bottom: 1.5rem;'>
                Pour commencer à poser des questions, veuillez d'abord uploader des documents 
                dans la section <strong>📄 Documents</strong>.
            </p>
            <div style='background: white; padding: 1rem; border-radius: 12px; display: inline-block; margin-top: 1rem;'>
                <p style='color: #1F2937; margin: 0;'>
                    👈 Utilisez la <strong>navigation dans la barre latérale</strong>
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def _display_database_info_compact(vector_store_manager: VectorStoreManager):
    """Affiche les informations de la base de manière compacte et élégante"""
    stats = vector_store_manager.get_stats()
    
    # Métriques en ligne
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Chunks", stats["total_chunks"], help="Nombre total de segments de texte")
    
    with col2:
        st.metric("📁 Documents", stats["total_sources"], help="Nombre de documents chargés")
    
    with col3:
        st.metric("🔍 Recherche", f"Top-{stats['top_k_results']}", help="Nombre de chunks récupérés par question")
    
    with col4:
        status_emoji = "✅" if stats["status"] == "ready" else "⚠️"
        status_text = "Prêt" if stats["status"] == "ready" else "En attente"
        st.metric("📡 Statut", f"{status_emoji} {status_text}")
    
    # Documents disponibles (collapsible)
    if stats["sources"]:
        with st.expander("📚 Documents disponibles", expanded=False):
            for idx, source in enumerate(stats["sources"], 1):
                st.markdown(f"`{idx}.` **{source}**")


def _display_chat_history_styled():
    """Affiche l'historique de conversation avec style amélioré"""
    if not st.session_state.chat_history:
        # Message de bienvenue stylisé
        st.markdown("""
            <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%); 
                        border-radius: 16px; margin: 2rem 0;'>
                <div style='font-size: 4rem; margin-bottom: 1rem;'>👋</div>
                <h2 style='color: #1F2937; margin-bottom: 1rem;'>Bienvenue !</h2>
                <p style='color: #6B7280; font-size: 1.1rem;'>
                    Posez votre première question ci-dessous pour commencer à explorer vos documents juridiques.
                </p>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # Afficher chaque message avec animations
    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
            
            # Afficher les sources avec design amélioré (pour les réponses assistant)
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                st.markdown("---")
                st.markdown("**📚 Sources utilisées :**")
                
                # Afficher sources avec badges
                sources_html = "<div style='display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;'>"
                for source in message["sources"]:
                    sources_html += f"""
                        <span style='background: #DBEAFE; color: #1E40AF; padding: 0.25rem 0.75rem; 
                                     border-radius: 12px; font-size: 0.85rem; font-weight: 500;'>
                            📄 {source}
                        </span>
                    """
                sources_html += "</div>"
                st.markdown(sources_html, unsafe_allow_html=True)
            
            # Timestamp stylisé
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
    """
    Traite la question de l'utilisateur et génère une réponse
    
    Args:
        question: Question de l'utilisateur
        llm_handler: Gestionnaire LLM
        conversation_manager: Gestionnaire de conversations
    """
    
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
    with st.chat_message("user", avatar="👤"):
        st.markdown(question)
        st.caption(f"🕒 {timestamp}")
    
    # Générer la réponse
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🤔 Recherche dans les documents..."):
            # Préparer l'historique pour le LLM (sans les métadonnées)
            chat_history_for_llm = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.chat_history[:-1]  # Exclure la dernière question
            ]
            
            # Générer la réponse
            try:
                response = llm_handler.generate_response(
                    question=question,
                    chat_history=chat_history_for_llm
                )
                
                # Afficher la réponse
                st.markdown(response["answer"])
                
                # Afficher les sources
                if response["sources"]:
                    st.markdown("---")
                    st.markdown("**📚 Sources utilisées :**")
                    
                    # Afficher sources avec badges
                    sources_html = "<div style='display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;'>"
                    for source in response["sources"]:
                        sources_html += f"""
                            <span style='background: #DBEAFE; color: #1E40AF; padding: 0.25rem 0.75rem; 
                                         border-radius: 12px; font-size: 0.85rem; font-weight: 500;'>
                                📄 {source}
                            </span>
                        """
                    sources_html += "</div>"
                    st.markdown(sources_html, unsafe_allow_html=True)
                    
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
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de la génération de la réponse: {e}")
                st.error(f"❌ Une erreur est survenue lors de la génération de la réponse: {str(e)}")
                
                # Retirer la question de l'historique en cas d'erreur
                st.session_state.chat_history.pop()
                st.session_state.message_count -= 1