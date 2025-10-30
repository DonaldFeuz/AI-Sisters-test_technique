"""
Application principale Streamlit - RAG Legal Chatbot
Version avec maquette professionnelle intégrée
Cabinet Parenti - Assistant Juridique IA
"""
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from loguru import logger

from src.config.settings import LOGS_DIR, APP_TITLE, APP_ICON
from src.utils.document_processor import DocumentProcessor
from src.utils.vector_store import VectorStoreManager
from src.utils.llm_handler import LLMHandler
from src.components.chat_interface import render_chat_interface
from src.components.document_manager import render_document_manager
from src.utils.conversation_manager import ConversationManager

# Configuration du logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    LOGS_DIR / "app_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)


def main():
    """Point d'entrée principal de l'application"""
    
    # Configuration de la page
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS de la maquette
    _inject_mockup_css()
    
    # Initialiser les composants (avec cache)
    vector_store_manager = _get_vector_store_manager()
    document_processor = _get_document_processor()
    llm_handler = _get_llm_handler(vector_store_manager)
    conversation_manager = _get_conversation_manager()
    
    # Initialiser la page
    if "page" not in st.session_state:
        st.session_state.page = "chat"
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        _render_sidebar(conversation_manager, vector_store_manager)
    
    # ========== CONTENU PRINCIPAL ==========
    if st.session_state.page == "chat":
        render_chat_interface(llm_handler, vector_store_manager, conversation_manager)
    elif st.session_state.page == "documents":
        render_document_manager(vector_store_manager, document_processor)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem; font-size: 0.85rem;'>
            🔒 Cabinet Parenti - Données confidentielles et sécurisées | Version 1.0 | © 2025
        </div>
    """, unsafe_allow_html=True)


def _render_sidebar(conversation_manager: ConversationManager, vector_store_manager: VectorStoreManager):
    """Render la sidebar avec le design de la maquette"""
    
    # Header de la sidebar
    st.markdown("""
        <div class="sidebar-header">
            <h2 style='color: white; margin: 0; font-size: 1.5rem;'>⚖️ Cabinet Parenti</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
    
    
    # Bouton Chat
    if st.button("💬 Interface Chat", key="nav_chat", use_container_width=True,
                 type="primary" if st.session_state.page == "chat" else "secondary"):
        st.session_state.page = "chat"
        st.rerun()
    
    # Bouton Documents
    if st.button("📁 Gestion Documents", key="nav_docs", use_container_width=True,
                 type="primary" if st.session_state.page == "documents" else "secondary"):
        st.session_state.page = "documents"
        st.rerun()
    
    st.markdown("<div style='margin: 1.5rem 0; border-top: 1px solid rgba(255,255,255,0.2);'></div>", 
                unsafe_allow_html=True)
    
    # Contenu spécifique selon la page
    if st.session_state.page == "chat":
        _render_chat_sidebar(conversation_manager)
    else:
        _render_documents_sidebar(vector_store_manager)


def _render_chat_sidebar(conversation_manager: ConversationManager):
    """Sidebar pour la page Chat"""
    
    st.markdown("<h3 style='color: white; font-size: 0.95rem; margin-bottom: 1rem;'>📝 Historique</h3>", 
                unsafe_allow_html=True)
    
    # Bouton nouvelle conversation
    if st.button("➕ Nouvelle conversation", key="new_conv", use_container_width=True,
                 help="Créer une nouvelle conversation"):
        if st.session_state.get("chat_history"):
            conversation_manager.save_conversation(
                st.session_state.current_conversation_id,
                st.session_state.chat_history
            )
        new_id = conversation_manager.generate_conversation_id()
        st.session_state.current_conversation_id = new_id
        st.session_state.chat_history = []
        logger.info(f"✨ Nouvelle conversation: {new_id}")
        st.rerun()
    
    st.markdown("<h4 style='color: rgba(255,255,255,0.9); font-size: 0.85rem; margin: 1rem 0 0.5rem 0;'>Conversations récentes</h4>", 
                unsafe_allow_html=True)
    
    # Historique
    conversations = conversation_manager.list_conversations()
    
    if not conversations:
        st.markdown("<p style='color: rgba(255,255,255,0.6); font-size: 0.85rem;'>Aucune conversation</p>", 
                    unsafe_allow_html=True)
    else:
        for conv in conversations[:5]:
            is_current = conv["id"] == st.session_state.get("current_conversation_id", "")
            
            button_label = f"📄 {conv['title'][:25]}..."
            if st.button(
                button_label,
                key=f"load_{conv['id']}",
                use_container_width=True,
                disabled=is_current,
                help=f"{conv['message_count']} messages"
            ):
                _load_conversation(conversation_manager, conv["id"])
                st.rerun()


def _render_documents_sidebar(vector_store_manager: VectorStoreManager):
    """Sidebar pour la page Documents"""
    
    st.markdown("<h3 style='color: white; font-size: 0.95rem; margin-bottom: 1rem;'>📊 Statistiques</h3>", 
                unsafe_allow_html=True)
    
    # Calculer les stats
    sources = vector_store_manager.get_all_sources()
    doc_count = len(sources)
    
    # Afficher les métriques
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; color: white;'>
            <div style='margin-bottom: 0.75rem;'>
                <div style='font-size: 0.85rem; opacity: 0.8;'>Documents</div>
                <div style='font-size: 1.75rem; font-weight: bold;'>{doc_count}</div>
            </div>
            <div style='border-top: 1px solid rgba(255,255,255,0.2); padding-top: 0.75rem; font-size: 0.85rem; opacity: 0.9;'>
                Dernière mise à jour: Aujourd'hui
            </div>
        </div>
    """, unsafe_allow_html=True)


def _load_conversation(conversation_manager: ConversationManager, conversation_id: str):
    """Charge une conversation"""
    conversation_data = conversation_manager.load_conversation(conversation_id)
    
    if conversation_data:
        st.session_state.current_conversation_id = conversation_id
        st.session_state.chat_history = conversation_data["messages"]
        st.session_state.message_count = len(conversation_data["messages"])
        logger.info(f"📂 Conversation chargée: {conversation_id}")


@st.cache_resource
def _get_vector_store_manager() -> VectorStoreManager:
    """Initialise et cache le VectorStoreManager"""
    logger.info("🔧 Initialisation du VectorStoreManager...")
    return VectorStoreManager()


@st.cache_resource
def _get_document_processor() -> DocumentProcessor:
    """Initialise et cache le DocumentProcessor"""
    logger.info("🔧 Initialisation du DocumentProcessor...")
    return DocumentProcessor()


@st.cache_resource
def _get_llm_handler(_vector_store_manager: VectorStoreManager) -> LLMHandler:
    """Initialise et cache le LLMHandler"""
    logger.info("🔧 Initialisation du LLMHandler...")
    return LLMHandler(_vector_store_manager)


@st.cache_resource
def _get_conversation_manager() -> ConversationManager:
    """Initialise et cache le ConversationManager"""
    logger.info("🔧 Initialisation du ConversationManager...")
    return ConversationManager()


def _inject_mockup_css():
    """CSS exact de la maquette"""
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* ===== GLOBAL ===== */
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e3a5f 0%, #2d5a8c 100%);
        }
        
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        
        [data-testid="stSidebar"] .stButton button {
            background: rgba(255,255,255,0.1);
            border: none;
            color: white !important;
            transition: all 0.3s;
            font-weight: 500;
        }
        
        [data-testid="stSidebar"] .stButton button:hover {
            background: rgba(255,255,255,0.2);
            transform: translateX(5px);
        }
        
        [data-testid="stSidebar"] .stButton button[kind="primary"] {
            background: rgba(255,255,255,0.25);
            border-left: 4px solid #4CAF50;
        }
        
        /* ===== MAIN CONTENT ===== */
        .main {
            background: #fafafa;
             max-width: 1400px;
             margin: 0 auto;
        }
        
        /* Fixer la hauteur de la page sans scroll */
        .main .block-container {
            max-height: 100vh;
            overflow: hidden;
            max-width: 70%;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Fixer le header */
        .main-header {
            position: sticky;
            top: 0;
            z-index: 10;
        }

        /* Ajuster la zone de chat pour remplir l'espace disponible */
        .message-container {
            max-height: calc(100vh - 400px);
            overflow-y: auto;
        }
        
        /* Zone de saisie style ChatGPT */
        .chat-input-container {
            background: white;
            border-radius: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            border: 1px solid #e5e7eb;
            transition: all 0.2s;
        }

        .chat-input-container:focus-within {
            border-color: #3b82f6;
            box-shadow: 0 4px 16px rgba(59,130,246,0.2);
        }

        /* Supprimer les styles par défaut de Streamlit */
        [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
        }

        .stTextInput > div > div {
            border: none !important;
        }
        
        /* ===== HEADER ===== */
        .main-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8c 100%);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .main-header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }
        
        .main-header p {
            opacity: 0.9;
            font-size: 1rem;
            margin: 0;
        }
        
        /* ===== CHAT MESSAGES ===== */
        .message-container {
            display: flex;
            margin: 1rem 0;
            animation: slideIn 0.3s ease-out;
        }
        
        .user-message {
            justify-content: flex-end;
        }
        
        .assistant-message {
            justify-content: flex-start;
        }
        
        .message-bubble {
            max-width: 70%;
            padding: 1rem 1.25rem;
            border-radius: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            animation: bubblePop 0.3s ease-out;
        }
        
        .user-bubble {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .assistant-bubble {
            background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
            color: #111827;
            border-bottom-left-radius: 4px;
        }
        
        .message-header {
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .message-content {
            line-height: 1.6;
        }
        
        .message-time {
            font-size: 0.75rem;
            opacity: 0.7;
            margin-top: 0.5rem;
            text-align: right;
        }
        
        /* ===== INFO PANEL ===== */
        .info-panel {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
        }
        
        .info-panel h3 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            color: #1e3a5f;
            font-weight: 600;
        }
        
        .info-box {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid #1976d2;
        }
        
        .info-box strong {
            color: #1e3a5f !important;
        }

        .info-box small {
            color: #4b5563 !important;
        }
        
        /* ===== DOCUMENT CARDS ===== */
        .doc-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        }
        
        .doc-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            border-color: #1976d2;
        }
        
        .doc-icon {
            font-size: 3rem;
            margin-bottom: 0.75rem;
        }
        
        .doc-name {
            font-weight: 600;
            color: #111827;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .doc-ext {
            display: inline-block;
            background: #1976d2;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        /* ===== UPLOAD ZONE ===== */
        .upload-zone {
            border: 3px dashed #1976d2;
            border-radius: 12px;
            padding: 3rem;
            text-align: center;
            background: #f8f9fa;
            transition: all 0.3s;
        }
        
        .upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        /* ===== STAT CARD ===== */
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .stat-card h2 {
            font-size: 1.3rem;
            margin-bottom: 0.5rem;
            opacity: 0.9;
        }
        
        .stat-card .number {
            font-size: 3rem;
            font-weight: bold;
            margin: 1rem 0;
        }
        
        /* ===== PIPELINE ===== */
        .pipeline-step {
            background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
        }
        
        .pipeline-step h4 {
            font-size: 1.2rem;
            margin-bottom: 1rem;
            color: #1e3a5f;
            font-weight: 600;
        }
        
        .pipeline-step ul {
            list-style: none;
            text-align: left;
            color: #666;
            padding: 0;
        }
        
        .pipeline-step li {
            padding: 0.3rem 0;
            font-size: 0.9rem;
        }
        
        /* ===== BUTTONS ===== */
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
        }
        
        /* ===== ANIMATIONS ===== */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes bubblePop {
            0% {
                transform: scale(0.9);
            }
            50% {
                transform: scale(1.02);
            }
            100% {
                transform: scale(1);
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* ===== HIDE STREAMLIT ELEMENTS ===== */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        logger.info("🚀 Démarrage de l'application RAG Legal Chatbot")
        main()
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        st.error(f"❌ Erreur: {e}")
        st.stop()