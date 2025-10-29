"""
Interface de chat avec design de la maquette
Cabinet Parenti - Assistant Juridique IA
"""
import streamlit as st
from typing import Dict, List
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
    """Render l'interface de chat (Page 1) avec le design de la maquette"""
    
    # Initialiser la conversation si nécessaire
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = conversation_manager.generate_conversation_id()
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Header principal
    st.markdown("""
        <div class="main-header">
            <h1>💬 Assistant Juridique IA</h1>
            <p>Posez vos questions sur les documents du cabinet en toute confidentialité</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Layout principal: Chat + Info panel
    col_chat, col_info = st.columns([2, 1])
    
    with col_chat:
        _render_chat_area(llm_handler, vector_store_manager, conversation_manager)
    
    with col_info:
        _render_info_panel(vector_store_manager)


def _render_chat_area(
    llm_handler: LLMHandler,
    vector_store_manager: VectorStoreManager,
    conversation_manager: ConversationManager
):
    """Zone de chat principale"""
    
    st.markdown("### 🗨️ Conversation")
    
    # Conteneur de messages avec hauteur fixe
    chat_container = st.container(height=450)
    
    with chat_container:
        if not st.session_state.chat_history:
            _render_welcome_message()
        else:
            _render_messages(st.session_state.chat_history)
    
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Zone de saisie
    _render_input_area(llm_handler, vector_store_manager, conversation_manager)


def _render_welcome_message():
    """Message de bienvenue"""
    st.markdown("""
        <div style='text-align: center; padding: 3rem 1rem;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>📚</div>
            <h2 style='color: #1e3a5f;'>Bienvenue dans votre assistant juridique</h2>
            <p style='color: #64748b; max-width: 500px; margin: 1rem auto;'>
                Commencez par poser une question sur vos documents juridiques.
                Les réponses sont basées exclusivement sur les documents que vous avez uploadés.
            </p>
        </div>
    """, unsafe_allow_html=True)


def _render_messages(messages: List[Dict]):
    """Affiche les messages sous forme de bulles (design maquette)"""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        timestamp = msg.get("timestamp", "")
        
        if role == "user":
            # Message utilisateur (à droite, bleu)
            st.markdown(f"""
                <div class="message-container user-message">
                    <div class="message-bubble user-bubble">
                        <div class="message-header">👤 Vous</div>
                        <div class="message-content">{content}</div>
                        <div class="message-time">{timestamp}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Message assistant (à gauche, gris)
            sources = msg.get("sources", [])
            sources_html = ""
            if sources:
                sources_html = "<br><br><strong style='font-size: 0.9rem;'>📚 Sources:</strong><br>"
                sources_html += "<br>".join([f"<span style='font-size: 0.85rem;'>• {s}</span>" for s in sources])
            
            st.markdown(f"""
                <div class="message-container assistant-message">
                    <div class="message-bubble assistant-bubble">
                        <div class="message-header">🤖 Assistant</div>
                        <div class="message-content">{content}{sources_html}</div>
                        <div class="message-time">{timestamp}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)


def _render_input_area(
    llm_handler: LLMHandler,
    vector_store_manager: VectorStoreManager,
    conversation_manager: ConversationManager
):
    """Zone de saisie avec design maquette"""
    
    # Vérifier si des documents sont chargés
    doc_count = vector_store_manager.get_document_count()
    
    if doc_count == 0:
        st.warning("⚠️ Aucun document chargé. Allez dans 'Gestion Documents' pour uploader des fichiers.", icon="⚠️")
        return
    
    # Input
    user_input = st.text_area(
        "Votre question :",
        placeholder="Ex: Quelles sont les clauses essentielles d'un contrat de prestation de service ?",
        height=100,
        key="user_input"
    )
    
    # Boutons
    col_send, col_clear = st.columns([3, 1])
    
    with col_send:
        send_button = st.button("📤 Envoyer", type="primary", use_container_width=True)
    
    with col_clear:
        clear_button = st.button("🗑️ Effacer", use_container_width=True)
    
    # Traiter l'envoi
    if send_button and user_input.strip():
        _handle_user_message(user_input, llm_handler, conversation_manager)
        st.rerun()
    
    # Traiter l'effacement
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()


def _handle_user_message(
    user_input: str,
    llm_handler: LLMHandler,
    conversation_manager: ConversationManager
):
    """Traite le message utilisateur"""
    
    # Valider
    is_valid, error_msg = llm_handler.validate_question(user_input)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    # Ajouter le message utilisateur
    timestamp = datetime.now().strftime("%H:%M")
    user_message = {
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    }
    st.session_state.chat_history.append(user_message)
    
    # Générer la réponse
    with st.spinner("🔍 Recherche dans les documents..."):
        try:
            response = llm_handler.generate_response(
                question=user_input,
                chat_history=st.session_state.chat_history
            )
            
            # Ajouter la réponse
            assistant_message = {
                "role": "assistant",
                "content": response["answer"],
                "timestamp": datetime.now().strftime("%H:%M"),
                "sources": response.get("sources", [])
            }
            st.session_state.chat_history.append(assistant_message)
            
            # Sauvegarder
            conversation_manager.save_conversation(
                st.session_state.current_conversation_id,
                st.session_state.chat_history
            )
            
            logger.info(f"✅ Réponse générée")
            
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            st.error(f"❌ Erreur: {str(e)}")


def _render_info_panel(vector_store_manager: VectorStoreManager):
    """Panneau d'informations (design maquette)"""
    
    # Informations RAG
    st.markdown("""
        <div class="info-panel">
            <h3>ℹ️ Informations</h3>
            <div class="info-box">
                <strong>Mode RAG actif</strong><br>
                <small>Les réponses sont basées exclusivement sur les documents du cabinet.</small>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Documents sources
    sources = vector_store_manager.get_all_sources()
    doc_count = len(sources)
    
    st.markdown(f"""
        <div class="info-panel">
            <h3>📚 Documents sources</h3>
            <ul style='list-style: none; padding: 0; margin: 0;'>
                <li style='padding: 0.5rem 0; border-bottom: 1px solid #eee;'>
                    ✅ {doc_count} documents actifs
                </li>
                <li style='padding: 0.5rem 0; border-bottom: 1px solid #eee;'>
                    🔒 Données sécurisées
                </li>
                <li style='padding: 0.5rem 0;'>
                    📊 Indexation complète
                </li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # Configuration
    st.markdown("""
        <div class="info-panel">
            <h3>⚡ Configuration</h3>
        </div>
    """, unsafe_allow_html=True)
    
    model_choice = st.selectbox(
        "Modèle IA",
        ["GPT-4", "Claude Sonnet", "Mistral Large"],
        index=1,
        key="model_choice"
    )
    
    num_sources = st.slider(
        "Nombre de sources",
        min_value=1,
        max_value=10,
        value=3,
        key="num_sources"
    )
    
    temperature = st.slider(
        "Température",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        key="temperature"
    )