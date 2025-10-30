"""
Application principale Streamlit - RAG Legal Chatbot
Version AMÉLIORÉE avec design responsive et optimisations
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
    
    # CSS optimisé
    _inject_optimized_css()
    
    # Initialiser les composants (avec cache)
    vector_store_manager = _get_vector_store_manager()
    document_processor = _get_document_processor()
    llm_handler = _get_llm_handler(vector_store_manager)
    conversation_manager = _get_conversation_manager()
    
    # Initialiser la page
    if "page" not in st.session_state:
        st.session_state.page = "chat"
    
    # Contenu du header selon la page
    if st.session_state.page == "chat":
        page_title = "💬 Assistant Juridique IA"
        page_subtitle = "Posez vos questions sur les documents du cabinet en toute confidentialité"
    else:
        page_title = "📁 Gestion des Documents"
        page_subtitle = "Uploadez, gérez et vectorisez vos documents juridiques"
    
    # ========== HEADER FIXE GLOBAL ==========
    st.markdown(f"""
    <div class="global-header">
        <div class="logo-section">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="font-size: 2rem;">⚖️</div>
                <div>
                    <div style="font-size: 1.2rem; font-weight: 700; margin: 0;">Cabinet Parenti</div>
                    <div style="font-size: 0.8rem; opacity: 0.8; margin: 0;">Assistant IA Juridique</div>
                </div>
            </div>
        </div>
        <div class="content-section">
            <div style="width: 100%;">
                <h1 style="font-size: 1.5rem; margin: 0 0 0.25rem 0;">{page_title}</h1>
                <p style="font-size: 0.85rem; margin: 0; opacity: 0.9;">{page_subtitle}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
            🔒 Cabinet Parenti - Données confidentielles et sécurisées | Version 2.0 | © 2025
        </div>
    """, unsafe_allow_html=True)


def _render_sidebar(conversation_manager: ConversationManager, vector_store_manager: VectorStoreManager):
    """Render la sidebar avec navigation et contenu contextuel"""
    
    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
    
    # ========== NAVIGATION ==========
    if st.button("💬 Interface Chat", key="nav_chat", use_container_width=True,
                 type="primary" if st.session_state.page == "chat" else "secondary"):
        st.session_state.page = "chat"
        st.rerun()
    
    if st.button("📁 Gestion Documents", key="nav_docs", use_container_width=True,
                 type="primary" if st.session_state.page == "documents" else "secondary"):
        st.session_state.page = "documents"
        st.rerun()
    
    st.markdown("<div style='margin: 1.5rem 0; border-top: 1px solid rgba(255,255,255,0.2);'></div>", 
                unsafe_allow_html=True)
    
    # ========== CONTENU CONTEXTUEL ==========
    if st.session_state.page == "chat":
        _render_chat_sidebar(conversation_manager)
    else:
        _render_documents_sidebar(vector_store_manager)


def _render_chat_sidebar(conversation_manager: ConversationManager):
    """Sidebar pour la page Chat"""
    
    st.markdown("<h3 style='color: white; font-size: 0.95rem; margin-bottom: 1rem;'>📝 Historique</h3>", 
                unsafe_allow_html=True)
    
    # Bouton nouvelle conversation
    if st.button("➕ Nouvelle conversation", key="new_conv", use_container_width=True):
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
    
    # Historique des conversations
    conversations = conversation_manager.list_conversations()
    
    if not conversations:
        st.markdown("<p style='color: rgba(255,255,255,0.6); font-size: 0.85rem;'>Aucune conversation</p>", 
                    unsafe_allow_html=True)
    else:
        for conv in conversations[:10]:
            is_current = conv["id"] == st.session_state.get("current_conversation_id", "")
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                button_label = f"📝 {conv['title'][:20]}..."
                if st.button(button_label, key=f"load_{conv['id']}", use_container_width=True, 
                        disabled=is_current):
                    _load_conversation(conversation_manager, conv["id"])
            
            with col2:
                if st.button("🗑️", key=f"del_conv_{conv['id']}", help="Supprimer"):
                    success = conversation_manager.delete_conversation(conv["id"])
                    if success:
                        if is_current:
                            new_id = conversation_manager.generate_conversation_id()
                            st.session_state.current_conversation_id = new_id
                            st.session_state.chat_history = []
                        st.success(f"✅ Conversation supprimée")
                        st.rerun()


def _render_documents_sidebar(vector_store_manager: VectorStoreManager):
    """Sidebar pour la page Documents avec statistiques"""
    
    st.markdown("<h3 style='color: white; font-size: 0.95rem; margin-bottom: 1rem;'>📊 Statistiques</h3>", 
                unsafe_allow_html=True)
    
    # Calculer les stats
    sources = vector_store_manager.get_all_sources()
    doc_count = len(sources)
    
    # Types de documents
    doc_types = {}
    for source in sources:
        ext = Path(source).suffix.lower()
        doc_types[ext] = doc_types.get(ext, 0) + 1
    
    # Afficher les métriques principales
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; color: white;'>
            <div style='margin-bottom: 0.75rem;'>
                <div style='font-size: 0.85rem; opacity: 0.8;'>Documents actifs</div>
                <div style='font-size: 1.75rem; font-weight: bold;'>{doc_count}</div>
            </div>
            <div style='border-top: 1px solid rgba(255,255,255,0.2); padding-top: 0.75rem; font-size: 0.85rem; opacity: 0.9;'>
                Dernière mise à jour:<br>
                <strong>Aujourd'hui</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Répartition par type
    if doc_types:
        st.markdown("<h4 style='color: rgba(255,255,255,0.9); font-size: 0.85rem; margin: 1rem 0 0.5rem 0;'>Par type de fichier</h4>", 
                    unsafe_allow_html=True)
        
        for ext, count in sorted(doc_types.items()):
            percentage = (count / doc_count) * 100
            st.markdown(f"""
                <div style='margin-bottom: 0.5rem;'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.25rem;'>
                        <span>{ext.upper()}</span>
                        <span>{count} ({percentage:.0f}%)</span>
                    </div>
                    <div style='background: rgba(255,255,255,0.2); height: 6px; border-radius: 3px; overflow: hidden;'>
                        <div style='background: linear-gradient(90deg, #4CAF50 0%, #81C784 100%); width: {percentage}%; height: 100%;'></div>
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
        st.rerun()


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


def _inject_optimized_css():
    """CSS optimisé et nettoyé - utilise le système natif de Streamlit"""
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* ===== GLOBAL ===== */
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        /* ===== HEADER GLOBAL FIXE ===== */
        .global-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8c 100%);
            color: white;
            z-index: 1002;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
        }

        .global-header .logo-section {
            width: 336px;
            min-width: 280px;
            max-width: 336px;
            padding: 1rem 1.5rem;
            background: linear-gradient(135deg, #1a2f4a 0%, #234567 100%);
            border-right: 2px solid rgba(255,255,255,0.2);
        }

        .global-header .content-section {
            flex: 1;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
        }

        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e3a5f 0%, #2d5a8c 100%);
            padding-top: 1px !important;
            top: 125px !important;  /* 👈 AJOUTE CETTE LIGNE - position Y fixe depuis le haut */
            height: calc(100vh - 80px) !important; 
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem !important;
        }

        [data-testid="stSidebar"] * {
            color: white !important;
        }

        /* Bouton collapse natif Streamlit - Style personnalisé */
        [data-testid="stSidebarCollapsedControl"] {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8c 100%) !important;
            color: white !important;
            border-radius: 0 8px 8px 0 !important;
            top: 100px !important;
            z-index: 1003 !important;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.2) !important;
            transition: all 0.3s ease !important;
        }

        [data-testid="stSidebarCollapsedControl"]:hover {
            background: linear-gradient(135deg, #2d5a8c 0%, #3a6ba5 100%) !important;
            transform: translateX(3px) !important;
        }

        [data-testid="stSidebarCollapsedControl"] svg {
            color: #4FC3F7 !important;
            width: 24px !important;
            height: 24px !important;
        }

        /* Boutons de navigation sidebar */
        [data-testid="stSidebar"] .stButton button {
            background: rgba(255,255,255,0.1);
            border: none;
            color: white !important;
            transition: all 0.3s;
            font-weight: 500;
            border-radius: 8px;
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
        
        .main .block-container {
            max-width: 85%;
            padding: 2rem;
            padding-top: 110px;
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
        
        .upload-zone:hover {
            border-color: #1565c0;
            background: #e3f2fd;
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
        
        /* ===== INPUT STYLING ===== */
        .stTextInput input {
            border: 2px solid #e5e7eb !important;
            border-radius: 12px !important;
            padding: 0.75rem 1rem !important;
            transition: all 0.3s !important;
        }
        
        .stTextInput input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
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
        
        /* ===== RESPONSIVE DESIGN ===== */
        @media (max-width: 768px) {
            .global-header .logo-section {
                width: 200px;
                min-width: 180px;
                padding: 0.75rem 1rem;
            }
            
            .global-header .logo-section > div > div:first-child {
                font-size: 1.5rem;
            }
            
            .global-header .content-section {
                padding: 0.75rem 1rem;
            }
            
            .main .block-container {
                max-width: 100%;
                padding: 1rem;
                padding-top: 100px;
            }
            
            .message-bubble {
                max-width: 90%;
                padding: 0.75rem 1rem;
            }
            
            .doc-card {
                padding: 1rem;
            }
            
            .upload-zone {
                padding: 2rem 1rem;
            }
            
            .stat-card {
                padding: 1.5rem;
            }
            
            .pipeline-step {
                padding: 1rem;
                margin-bottom: 1rem;
            }
            
            .info-panel {
                padding: 1rem;
            }
        }
        
        @media (max-width: 480px) {
            .global-header .logo-section {
                width: 150px;
                min-width: 150px;
            }
            
            .global-header .logo-section > div > div {
                font-size: 0.9rem !important;
            }
            
            .global-header .content-section h1 {
                font-size: 1.1rem !important;
            }
            
            .message-bubble {
                max-width: 95%;
                font-size: 0.9rem;
            }
            
            .stat-card .number {
                font-size: 2rem;
            }
        }
        
        /* ===== HIDE STREAMLIT DEFAULT ELEMENTS ===== */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* ===== TOAST NOTIFICATIONS ===== */
        .stToast {
            background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
            color: white;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        logger.info("🚀 Démarrage de l'application RAG Legal Chatbot v2.0")
        main()
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        st.error(f"❌ Erreur: {e}")
        st.stop()