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
    
    # CSS personnalisé
    _inject_custom_css()
    
    # Initialiser les composants (avec cache)
    vector_store_manager = _get_vector_store_manager()
    document_processor = _get_document_processor()
    llm_handler = _get_llm_handler(vector_store_manager)
    conversation_manager = _get_conversation_manager()
    
    # ========== SIDEBAR SIMPLIFIÉE ==========
    with st.sidebar:
        # Logo et titre
        st.markdown("""
            <div style='text-align: center; padding: 1.5rem 0; margin-bottom: 2rem;'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>💼</div>
                <h2 style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>
                    Parenti Legal AI
                </h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation principale
        st.markdown("""
            <div style='margin-bottom: 1rem;'>
                <p style='color: rgba(255,255,255,0.7); font-size: 0.75rem; text-transform: uppercase; 
                          letter-spacing: 1px; font-weight: 600; margin-bottom: 1rem;'>
                    Navigation
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Initialiser la page par défaut
        if "page" not in st.session_state:
            st.session_state.page = "💬 Chat"
        
        # Boutons de navigation stylisés
        if st.button("💬 Chat", key="nav_chat", use_container_width=True, 
                     type="primary" if st.session_state.page == "💬 Chat" else "secondary"):
            st.session_state.page = "💬 Chat"
            st.rerun()
        
        if st.button("📄 Documents", key="nav_docs", use_container_width=True,
                     type="primary" if st.session_state.page == "📄 Documents" else "secondary"):
            st.session_state.page = "📄 Documents"
            st.rerun()
        
        st.markdown("---")
        
        # Historique des conversations
        st.markdown("""
            <div style='margin: 2rem 0 1rem 0;'>
                <p style='color: rgba(255,255,255,0.7); font-size: 0.75rem; text-transform: uppercase; 
                          letter-spacing: 1px; font-weight: 600;'>
                    📚 Historique
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        _display_conversation_history_sidebar(conversation_manager)
        
        # Spacer pour pousser "Paramètres" en bas
        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Paramètres en bas
        if st.button("⚙️ Paramètres", key="nav_settings", use_container_width=True):
            st.session_state.show_settings = not st.session_state.get("show_settings", False)
    
    # Afficher la page sélectionnée
    if st.session_state.page == "💬 Chat":
        render_chat_interface(llm_handler, vector_store_manager, conversation_manager)
    elif st.session_state.page == "📄 Documents":
        render_document_manager(vector_store_manager, document_processor)
    
    # Modal des paramètres (optionnel)
    if st.session_state.get("show_settings", False):
        _display_settings_modal(llm_handler)
    
    # Footer
    _display_footer()


def _display_conversation_history_sidebar(conversation_manager: ConversationManager):
    """
    Affiche l'historique des conversations dans la sidebar (version simplifiée)
    """
    conversations = conversation_manager.list_conversations()
    
    if not conversations:
        st.markdown("""
            <p style='color: rgba(255,255,255,0.5); font-size: 0.9rem; text-align: center; 
                      padding: 1rem; font-style: italic;'>
                Aucune conversation
            </p>
        """, unsafe_allow_html=True)
        return
    
    # Afficher les 5 conversations les plus récentes
    for conv in conversations[:5]:
        # Vérifier si c'est la conversation courante
        is_current = conv["id"] == st.session_state.get("current_conversation_id", "")
        
        # Style différent si conversation courante
        if is_current:
            bg_color = "rgba(255, 255, 255, 0.15)"
            text_color = "white"
            border = "2px solid rgba(255, 255, 255, 0.3)"
        else:
            bg_color = "rgba(255, 255, 255, 0.05)"
            text_color = "rgba(255, 255, 255, 0.9)"
            border = "1px solid rgba(255, 255, 255, 0.1)"
        
        # Créer un bouton stylisé pour chaque conversation
        col1, col2 = st.columns([5, 1])
        
        with col1:
            if st.button(
                f"{conv['title'][:35]}...",
                key=f"load_conv_{conv['id']}",
                use_container_width=True,
                help=f"{conv['message_count']} messages • {conv['updated_at']}",
                disabled=is_current
            ):
                _load_conversation_from_sidebar(conversation_manager, conv["id"])
                st.rerun()
        
        with col2:
            if not is_current:  # Ne pas permettre de supprimer la conversation courante
                if st.button("🗑️", key=f"del_conv_{conv['id']}", help="Supprimer"):
                    if conversation_manager.delete_conversation(conv["id"]):
                        st.rerun()


def _load_conversation_from_sidebar(conversation_manager: ConversationManager, conversation_id: str):
    """Charge une conversation depuis la sidebar"""
    # Sauvegarder la conversation courante si modifiée
    if st.session_state.get("conversation_modified", False):
        conversation_manager.save_conversation(
            st.session_state.current_conversation_id,
            st.session_state.chat_history
        )
    
    # Charger la conversation
    conversation_data = conversation_manager.load_conversation(conversation_id)
    
    if conversation_data:
        st.session_state.current_conversation_id = conversation_id
        st.session_state.chat_history = conversation_data["messages"]
        st.session_state.message_count = len(conversation_data["messages"])
        st.session_state.conversation_modified = False
        logger.info(f"📂 Conversation chargée depuis sidebar: {conversation_id}")


def _display_settings_modal(llm_handler: LLMHandler):
    """Affiche un modal avec les paramètres (optionnel)"""
    with st.expander("⚙️ Paramètres du Modèle", expanded=True):
        from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, MAX_TOKENS, TOP_K_RESULTS
        
        st.markdown("### 🤖 Configuration LLM")
        st.write(f"**Modèle :** `{LLM_MODEL}`")
        st.write(f"**Température :** `{LLM_TEMPERATURE}`")
        st.write(f"**Max Tokens :** `{MAX_TOKENS}`")
        st.write(f"**Top-K Résultats :** `{TOP_K_RESULTS}`")
        
        st.markdown("---")
        
        st.markdown("### 📋 Prompt Système")
        st.code(llm_handler.get_system_prompt(), language="text")


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
    """Injecte du CSS personnalisé"""
    st.markdown("""
        <style>
        /* ===== SIDEBAR SIMPLIFIÉE ===== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1E3A8A 0%, #1E40AF 100%);
            padding: 1rem 0.75rem;
        }
        
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p {
            color: white !important;
        }
        
        /* Boutons de navigation dans sidebar */
        [data-testid="stSidebar"] .stButton button {
            width: 100%;
            background: rgba(255, 255, 255, 0.08);
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 0.75rem 1rem;
            font-weight: 500;
            font-size: 1rem;
            text-align: left;
            transition: all 0.2s ease;
            margin-bottom: 0.5rem;
        }
        
        [data-testid="stSidebar"] .stButton button:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
            transform: translateX(4px);
        }
        
        /* Bouton primaire (page active) */
        [data-testid="stSidebar"] .stButton button[kind="primary"] {
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid white;
            font-weight: 600;
        }
        
        [data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateX(0);
        }
        
        /* Supprimer les marges par défaut */
        [data-testid="stSidebar"] .element-container {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Historique des conversations - style liste */
        [data-testid="stSidebar"] .stButton button[key^="load_conv_"] {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 0.6rem 0.8rem;
            font-size: 0.9rem;
            margin-bottom: 0.4rem;
        }
        
        [data-testid="stSidebar"] .stButton button[key^="load_conv_"]:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(2px);
        }
        
        /* Bouton supprimer dans historique */
        [data-testid="stSidebar"] .stButton button[key^="del_conv_"] {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 0.4rem;
            font-size: 0.9rem;
        }
        
        [data-testid="stSidebar"] .stButton button[key^="del_conv_"]:hover {
            background: rgba(239, 68, 68, 0.4);
            border-color: rgba(239, 68, 68, 0.5);
        }
        
        /* Dividers dans sidebar */
        [data-testid="stSidebar"] hr {
            border: none;
            height: 1px;
            background: rgba(255, 255, 255, 0.15);
            margin: 1.5rem 0;
        }
        
        /* Sections de titre (Navigation, Historique) */
        [data-testid="stSidebar"] .stMarkdown p {
            margin: 0 !important;
        }
        
        /* ===== RESTE DU CSS (inchangé) ===== */
        /* ... (garder tout le reste du CSS précédent) ... */
        
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