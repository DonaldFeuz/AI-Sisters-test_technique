"""
Application principale Streamlit - RAG Legal Chatbot
Point d'entrée de l'application
"""
import sys
from pathlib import Path

# ✅ 1. D'ABORD : Ajouter le répertoire racine au PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# ✅ 2. ENSUITE : Importer les modules externes
import streamlit as st
from loguru import logger

# ✅ 3. ENFIN : Importer depuis src
from src.config.settings import (
    LOGS_DIR,
    APP_TITLE,
    APP_ICON
)
from src.utils.document_processor import DocumentProcessor
from src.utils.vector_store import VectorStoreManager
from src.utils.llm_handler import LLMHandler
from src.components.chat_interface import render_chat_interface
from src.components.document_manager import render_document_manager
from src.utils.conversation_manager import ConversationManager

# ✅ 4. Configuration du logging (après imports)
logger.remove()  # Supprimer le handler par défaut
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
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': f"# {APP_TITLE}\n\nChatbot RAG pour cabinet d'avocats"
        }
    )
    
    # CSS personnalisé (optionnel)
    _inject_custom_css()
    
    # Initialiser les composants (avec cache)
    vector_store_manager = _get_vector_store_manager()
    document_processor = _get_document_processor()
    llm_handler = _get_llm_handler(vector_store_manager)
    conversation_manager = _get_conversation_manager()
    
    # Sidebar de navigation
    with st.sidebar:
        st.title(f"{APP_ICON} {APP_TITLE}")
        st.markdown("---")
        
        # Initialiser la page par défaut dans session_state si elle n'existe pas
        if "page" not in st.session_state:
            st.session_state.page = "💬 Chat"
        
        # Sélection de page (lié à session_state)
        page = st.radio(
            "Navigation",
            options=["💬 Chat", "📄 Gestion des Documents"],
            index=0 if st.session_state.page == "💬 Chat" else 1,
            label_visibility="collapsed",
            key="page_selector"
        )
        
        # Mettre à jour session_state
        st.session_state.page = page
        
        st.markdown("---")
        
        # Informations
        _display_sidebar_info(vector_store_manager)
    
    # Afficher la page sélectionnée (utiliser session_state)
    if st.session_state.page == "💬 Chat":
        render_chat_interface(llm_handler, vector_store_manager, conversation_manager)
    elif st.session_state.page == "📄 Gestion des Documents":
        render_document_manager(vector_store_manager, document_processor)
    
    # Footer
    _display_footer()


@st.cache_resource
def _get_vector_store_manager() -> VectorStoreManager:
    """
    Initialise et cache le VectorStoreManager
    
    Le cache permet de ne créer qu'une seule instance
    qui sera réutilisée lors des reruns Streamlit
    """
    logger.info("🔧 Initialisation du VectorStoreManager...")
    return VectorStoreManager()


@st.cache_resource
def _get_document_processor() -> DocumentProcessor:
    """Initialise et cache le DocumentProcessor"""
    logger.info("🔧 Initialisation du DocumentProcessor...")
    return DocumentProcessor()


@st.cache_resource
def _get_llm_handler(_vector_store_manager: VectorStoreManager) -> LLMHandler:
    """
    Initialise et cache le LLMHandler
    
    Note: Le _ devant vector_store_manager indique à Streamlit
    de ne pas hasher ce paramètre (car c'est un objet déjà caché)
    """
    logger.info("🔧 Initialisation du LLMHandler...")
    return LLMHandler(_vector_store_manager)

@st.cache_resource
def _get_conversation_manager() -> ConversationManager:
    """Initialise et cache le ConversationManager"""
    logger.info("🔧 Initialisation du ConversationManager...")
    return ConversationManager()


def _display_sidebar_info(vector_store_manager: VectorStoreManager):
    """Affiche des informations dans la sidebar"""
    
    st.subheader("📊 État de la Base")
    
    stats = vector_store_manager.get_stats()
    
    # Métriques compactes
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Chunks", stats["total_chunks"])
    
    with col2:
        st.metric("Docs", stats["total_sources"])
    
    # Indicateur de statut
    if stats["status"] == "ready":
        st.success("✅ Prêt")
    elif stats["status"] == "empty":
        st.warning("⚠️ Vide")
    else:
        st.error("❌ Erreur")
    
    st.markdown("---")
    
    # Aide rapide
    with st.expander("❓ Aide Rapide"):
        st.markdown("""
        **Comment utiliser l'application :**
        
        1. **📄 Gestion des Documents**
           - Uploadez vos documents (.txt, .csv, .html)
           - Gérez la base vectorielle
        
        2. **💬 Chat**
           - Posez des questions sur vos documents
           - Recevez des réponses avec sources
        
        **Formats supportés :**
        - `.txt` - Fichiers texte
        - `.csv` - Tableaux CSV
        - `.html` - Pages HTML
        """)
    
    st.markdown("---")
    
    # À propos
    with st.expander("ℹ️ À Propos"):
        st.markdown(f"""
        **{APP_TITLE}**
        
        Application RAG (Retrieval-Augmented Generation) 
        pour le cabinet d'avocats Emilia Parenti.
        
        **Technologies :**
        - Streamlit
        - LangChain
        - OpenAI GPT
        - FAISS/ChromaDB
        
        **Version :** 1.0.0
        """)


def _inject_custom_css():
    """Injecte du CSS personnalisé (optionnel)"""
    st.markdown("""
        <style>
        /* Améliorer l'apparence des chat messages */
        .stChatMessage {
            padding: 1rem;
            border-radius: 0.5rem;
        }
        
        /* Styliser les métriques */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
            font-weight: bold;
        }
        
        /* Améliorer les expanders */
        .streamlit-expanderHeader {
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)


def _display_footer():
    """Affiche un footer en bas de page"""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8rem; padding: 1rem;'>
        Cabinet d'avocats Emilia Parenti | Paris, France | © 2025
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    try:
        logger.info("🚀 Démarrage de l'application RAG Legal Chatbot")
        main()
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        st.error(f"❌ Erreur fatale lors du démarrage de l'application: {e}")
        st.stop()