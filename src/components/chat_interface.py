"""
Interface de chat avec design de la maquette - VERSION AMÉLIORÉE
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
    
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}
    
    # Layout principal: Chat + Info panel
    col_chat, col_info = st.columns([3, 1])
    
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
    
    # Conteneur de messages avec hauteur fixe et scroll
    chat_container = st.container(height=450)
    
    with chat_container:
        if not st.session_state.chat_history:
            _render_welcome_message()
        else:
            _render_messages(st.session_state.chat_history)
    
    # Espaceur
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    
    # Zone de saisie FIXÉE en bas
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
            <div style='margin-top: 2rem; display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; color: #D4AF37'>
                <div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 1rem 1.5rem; border-radius: 12px; max-width: 200px;'>
                    <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>🔍</div>
                    <strong>Recherche contextuelle</strong>
                    <p style='font-size: 0.85rem; margin: 0.5rem 0 0 0;'>Réponses basées sur vos documents</p>
                </div>
                <div style='background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); padding: 1rem 1.5rem; border-radius: 12px; max-width: 200px;'>
                    <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>🔒</div>
                    <strong>Totalement sécurisé</strong>
                    <p style='font-size: 0.85rem; margin: 0.5rem 0 0 0;'>Vos données restent privées</p>
                </div>
                <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 1rem 1.5rem; border-radius: 12px; max-width: 200px;'>
                    <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>⚡</div>
                    <strong>Réponses rapides</strong>
                    <p style='font-size: 0.85rem; margin: 0.5rem 0 0 0;'>IA optimisée pour le juridique</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def _render_messages(messages: List[Dict]):
    """Affiche les messages sous forme de bulles avec feedback"""
    for idx, msg in enumerate(messages):
        role = msg["role"]
        content = msg["content"]
        timestamp = msg.get("timestamp", "")
        msg_id = msg.get("id", f"{role}_{idx}")
        
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
            
            # Boutons de feedback
            _render_feedback_buttons(msg_id, idx)


def _render_feedback_buttons(msg_id: str, idx: int):
    """Affiche les boutons de feedback pour chaque message assistant"""
    col1, col2, col3, col4 = st.columns([1, 1, 1, 9])
    
    with col1:
        if st.button("👍", key=f"like_{msg_id}_{idx}", help="Réponse utile"):
            st.session_state.feedback[msg_id] = "positive"
            st.toast("✅ Merci pour votre retour !", icon="✅")
            logger.info(f"Feedback positif pour message {msg_id}")
    
    with col2:
        if st.button("👎", key=f"dislike_{msg_id}_{idx}", help="Réponse peu utile"):
            st.session_state.feedback[msg_id] = "negative"
            st.toast("📝 Nous prenons note de votre retour", icon="📝")
            logger.info(f"Feedback négatif pour message {msg_id}")
    
    with col3:
        if st.button("📋", key=f"copy_{msg_id}_{idx}", help="Copier la réponse"):
            st.toast("📋 Réponse copiée !", icon="📋")
    
    # Afficher le feedback actuel
    if msg_id in st.session_state.feedback:
        feedback_type = st.session_state.feedback[msg_id]
        icon = "✅" if feedback_type == "positive" else "📝"
        with col4:
            st.markdown(f"<small style='color: #666;'>{icon} Feedback enregistré</small>", 
                       unsafe_allow_html=True)


def _render_input_area(
    llm_handler: LLMHandler,
    vector_store_manager: VectorStoreManager,
    conversation_manager: ConversationManager
):
    """Zone de saisie optimisée"""
    
    # Vérifier si des documents sont chargés
    doc_count = vector_store_manager.get_document_count()
    
    if doc_count == 0:
        st.warning("⚠️ Aucun document chargé. Allez dans 'Gestion Documents' pour uploader des fichiers.", icon="⚠️")
        return
    
    # Container pour l'input fixé
    input_container = st.container()
    
    with input_container:
        # Créer un formulaire pour la touche Entrée
        with st.form(key="chat_form", clear_on_submit=True):
            col1, col2 = st.columns([9, 1])
        
            with col1:
                user_input = st.text_input(
                    "Message",
                    placeholder="💬 Posez votre question juridique... (Appuyez sur Entrée pour envoyer)",
                    key="user_input_field",
                    label_visibility="collapsed"
                )
            
            with col2:
                send_button = st.form_submit_button("➤", use_container_width=True, type="primary")
        
        # Traiter l'envoi (Entrée ou bouton)
        if send_button and user_input.strip():
            _handle_user_message(user_input, llm_handler, vector_store_manager, conversation_manager)
            st.rerun()


def _handle_user_message(
    user_input: str,
    llm_handler: LLMHandler,
    vector_store_manager: VectorStoreManager,
    conversation_manager: ConversationManager
):
    """Traite le message utilisateur avec gestion d'erreurs améliorée"""
    
    # Valider
    is_valid, error_msg = llm_handler.validate_question(user_input)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    # Ajouter le message utilisateur
    timestamp = datetime.now().strftime("%H:%M")
    msg_id = f"user_{datetime.now().timestamp()}"
    user_message = {
        "role": "user",
        "content": user_input,
        "timestamp": timestamp,
        "id": msg_id
    }
    st.session_state.chat_history.append(user_message)
    
    # Générer la réponse avec LOADING STATES améliorés
    try:
        with st.status("🔍 Traitement de votre question...", expanded=True) as status:
            st.write("📄 Recherche dans les documents...")
            
            # Simuler les étapes (vous pouvez adapter selon votre LLMHandler)
            import time
            time.sleep(0.5)
            
            st.write("🧠 Analyse contextuelle...")
            time.sleep(0.5)
            
            st.write("✍️ Génération de la réponse...")
            
            response = llm_handler.generate_response(
                question=user_input,
                chat_history=st.session_state.chat_history
            )
            
            st.write("✅ Réponse prête !")
            status.update(label="✅ Réponse générée avec succès !", state="complete")
        
        # Ajouter la réponse
        assistant_msg_id = f"assistant_{datetime.now().timestamp()}"
        assistant_message = {
            "role": "assistant",
            "content": response["answer"],
            "timestamp": datetime.now().strftime("%H:%M"),
            "sources": response.get("sources", []),
            "id": assistant_msg_id
        }
        st.session_state.chat_history.append(assistant_message)
        
        # Sauvegarder
        conversation_manager.save_conversation(
            st.session_state.current_conversation_id,
            st.session_state.chat_history
        )
        
        logger.info(f"✅ Réponse générée pour: {user_input[:50]}...")
        
    except Exception as e:
        error_type = type(e).__name__
        
        # Gestion d'erreurs spécifiques
        if "RateLimitError" in error_type or "rate" in str(e).lower():
            st.error("⏱️ Limite API atteinte. Veuillez patienter quelques instants...")
        elif "timeout" in str(e).lower():
            st.error("⌛ La requête a pris trop de temps. Réessayez avec une question plus courte.")
        elif "connection" in str(e).lower():
            st.error("🌐 Erreur de connexion. Vérifiez votre connexion internet.")
        else:
            st.error("❌ Une erreur s'est produite lors du traitement de votre question.")
        
        # Détails techniques en expander
        with st.expander("🔧 Détails techniques (pour débogage)"):
            st.code(f"Type d'erreur: {error_type}\n\nMessage: {str(e)}")
            st.markdown("**💡 Suggestions:**")
            st.markdown("- Vérifiez que vos documents sont bien chargés")
            st.markdown("- Essayez de reformuler votre question")
            st.markdown("- Contactez l'administrateur si le problème persiste")
        
        logger.error(f"❌ Erreur lors de la génération: {error_type} - {str(e)}")


def _render_info_panel(vector_store_manager: VectorStoreManager):
    """Panneau d'informations amélioré"""
    
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
    
    # Documents sources avec stats
    sources = vector_store_manager.get_all_sources()
    doc_count = len(sources)
    
    # Calculer les types de documents
    doc_types = {}
    for source in sources:
        ext = source.split('.')[-1].lower()
        doc_types[ext] = doc_types.get(ext, 0) + 1
    
    types_html = "<br>".join([f"<span style='font-size: 0.85rem;'>• {ext.upper()}: {count}</span>" 
                               for ext, count in doc_types.items()])
    
    st.markdown(f"""
        <div class="info-panel">
            <h3>📚 Documents sources</h3>
            <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                        padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <div style='font-size: 2rem; font-weight: bold; color: #2e7d32;'>{doc_count}</div>
                <div style='font-size: 0.9rem; color: #1b5e20;'>Documents actifs</div>
            </div>
            <ul style='list-style: none; padding: 0; margin: 0; color: #4b5563;'>
                <li style='padding: 0.5rem 0; border-bottom: 1px solid #eee;'>
                    🔒 Données sécurisées
                </li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # Tips pour meilleures questions
    with st.expander("💡 Conseils pour de meilleures réponses"):
        st.markdown("""
        **Posez des questions:**
        - ✅ Précises et contextualisées
        - ✅ En rapport avec vos documents
        - ✅ Une question à la fois
        
        **Exemples:**
        - "Quelles sont les conditions de résiliation ?"
        - "Résume les obligations du locataire"
        - "Quelle est la durée du préavis ?"
        """)