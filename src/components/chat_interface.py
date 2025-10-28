"""
Page Streamlit : Interface de chat avec RAG
"""
import streamlit as st
from typing import List, Dict
from datetime import datetime
from loguru import logger

from src.utils.llm_handler import LLMHandler
from src.utils.vector_store import VectorStoreManager


def render_chat_interface(
    llm_handler: LLMHandler,
    vector_store_manager: VectorStoreManager
):
    """
    Affiche l'interface de chat
    
    Args:
        llm_handler: Gestionnaire LLM
        vector_store_manager: Gestionnaire de base vectorielle
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
    _initialize_chat_history()
    
    # Sidebar avec options
    _render_sidebar(llm_handler)
    
    # Afficher l'historique de conversation
    _display_chat_history()
    
    # Zone de saisie utilisateur
    _render_chat_input(llm_handler)


def _display_empty_state():
    """Affiche un message si aucun document n'est chargé"""
    st.info(
        "📭 **Aucun document chargé dans la base.**\n\n"
        "Pour commencer à poser des questions, veuillez d'abord uploader "
        "des documents dans la section **📄 Gestion des Documents**."
    )
    
    # Bouton pour aller vers la page de gestion
    if st.button("📄 Aller à la Gestion des Documents", type="primary"):
        st.switch_page("src/components/document_manager.py")


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


def _initialize_chat_history():
    """Initialise l'historique de conversation dans st.session_state"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        logger.info("💬 Historique de conversation initialisé")
    
    if "message_count" not in st.session_state:
        st.session_state.message_count = 0


def _render_sidebar(llm_handler: LLMHandler):
    """Affiche la sidebar avec options et informations"""
    with st.sidebar:
        st.header("⚙️ Options")
        
        # Bouton pour nouvelle conversation
        if st.button("🆕 Nouvelle Conversation", use_container_width=True):
            _clear_chat_history()
            st.rerun()
        
        st.markdown("---")
        
        # Compteur de messages
        st.metric(
            "📨 Messages dans la conversation",
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


def _render_chat_input(llm_handler: LLMHandler):
    """Zone de saisie pour les questions utilisateur"""
    
    # Input utilisateur
    user_question = st.chat_input(
        "Posez votre question sur les documents juridiques...",
        key="chat_input"
    )
    
    if user_question:
        _process_user_question(user_question, llm_handler)


def _process_user_question(question: str, llm_handler: LLMHandler):
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
    
    logger.info(
        f"💬 Question traitée: '{question[:50]}...' | "
        f"Réponse: {len(response['answer'])} caractères | "
        f"Sources: {len(response['sources'])}"
    )


def _clear_chat_history():
    """Efface l'historique de conversation"""
    st.session_state.chat_history = []
    st.session_state.message_count = 0
    logger.info("🗑️ Historique de conversation effacé")


def _export_conversation():
    """Exporte la conversation en format texte (bonus)"""
    if not st.session_state.chat_history:
        st.warning("⚠️ Aucune conversation à exporter")
        return
    
    # Générer le contenu
    export_content = "# Conversation - RAG Legal Chatbot\n\n"
    export_content += f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    export_content += "---\n\n"
    
    for idx, message in enumerate(st.session_state.chat_history, 1):
        role = "👤 Utilisateur" if message["role"] == "user" else "🤖 Assistant"
        export_content += f"## Message {idx} - {role}\n\n"
        export_content += f"{message['content']}\n\n"
        
        if message["role"] == "assistant" and "sources" in message:
            export_content += "**Sources :**\n"
            for source in message["sources"]:
                export_content += f"- {source}\n"
            export_content += "\n"
        
        export_content += f"*{message.get('timestamp', '')}*\n\n"
        export_content += "---\n\n"
    
    return export_content


# Fonction bonus pour la sidebar (export)
def render_export_button():
    """Affiche un bouton d'export dans la sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("💾 Export")
        
        if st.button("📥 Exporter la Conversation", use_container_width=True):
            if st.session_state.get("chat_history"):
                export_content = _export_conversation()
                
                st.download_button(
                    label="📄 Télécharger (TXT)",
                    data=export_content,
                    file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Aucune conversation à exporter")