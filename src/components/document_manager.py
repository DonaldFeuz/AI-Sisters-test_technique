"""
Gestionnaire de documents - Page 2 avec design de la maquette
Cabinet Parenti - Assistant Juridique IA
"""
import streamlit as st
from pathlib import Path
from typing import List
from loguru import logger

from src.utils.vector_store import VectorStoreManager
from src.utils.document_processor import DocumentProcessor
from src.config.settings import UPLOAD_DIR, SUPPORTED_EXTENSIONS


def render_document_manager(
    vector_store_manager: VectorStoreManager,
    document_processor: DocumentProcessor
):
    """Render la page de gestion des documents (Page 2) avec design maquette"""
    
    # Header principal
    st.markdown("""
        <div class="main-header">
            <h1>📁 Gestion des Documents</h1>
            <p>Uploadez, gérez et vectorisez vos documents juridiques</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Section Upload + Stats
    col_upload, col_stats = st.columns([2, 1])
    
    with col_upload:
        _render_upload_section(vector_store_manager, document_processor)
    
    with col_stats:
        _render_stats_card(vector_store_manager)
    
    st.markdown("---")
    
    # Section Liste des documents
    st.markdown("### 📋 Documents indexés")
    _render_documents_list(vector_store_manager)
    
    st.markdown("---")
    
    # Pipeline de traitement
    _render_pipeline_section()


def _render_upload_section(
    vector_store_manager: VectorStoreManager,
    document_processor: DocumentProcessor
):
    """Section upload avec design maquette"""
    
    st.markdown("### 📤 Upload de documents")
    
    # Zone de drop
    st.markdown("""
        <div class="upload-zone">
            <div class="upload-icon">📂</div>
            <h4 style='color: #1e3a5f; margin: 0.5rem 0;'>Glissez-déposez vos fichiers ici</h4>
            <p style='color: #666; margin: 0.5rem 0;'>ou cliquez pour parcourir</p>
            <p style='color: #999; font-size: 0.85rem; margin-top: 1rem;'>
                Formats acceptés : .txt, .csv, .html
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Sélectionnez vos fichiers",
        type=[ext.replace(".", "") for ext in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
        key="file_uploader",
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) prêt(s) à être traité(s)")
        
        if st.button("🚀 Traiter et Vectoriser", type="primary", use_container_width=True):
            _handle_upload(uploaded_files, vector_store_manager, document_processor)


def _render_stats_card(vector_store_manager: VectorStoreManager):
    """Carte de statistiques (design maquette)"""
    
    sources = vector_store_manager.get_all_sources()
    doc_count = len(sources)
    
    st.markdown(f"""
        <div class="stat-card">
            <h2>📊 Statistiques</h2>
            <div class="number">{doc_count}</div>
            <p style='font-size: 1rem;'>Documents actifs</p>
            <hr style='margin: 1rem 0; border: none; border-top: 1px solid rgba(255,255,255,0.3);'>
            <p style='font-size: 0.9rem; opacity: 0.9;'>
                Indexation complète<br>
                Données sécurisées
            </p>
        </div>
    """, unsafe_allow_html=True)


def _handle_upload(
    uploaded_files,
    vector_store_manager: VectorStoreManager,
    document_processor: DocumentProcessor
):
    """Gère l'upload et la vectorisation automatique"""
    
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(uploaded_files)
    successful = 0
    
    for i, file in enumerate(uploaded_files):
        try:
            # Progression
            progress = (i + 1) / total
            progress_bar.progress(progress)
            status_text.info(f"⏳ Traitement de **{file.name}**... ({i + 1}/{total})")
            
            # Sauvegarder
            file_path = UPLOAD_DIR / file.name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            
            # Valider
            is_valid, error = document_processor.validate_file(file_path)
            if not is_valid:
                st.error(f"❌ {file.name}: {error}")
                file_path.unlink()
                continue
            
            # Traiter et vectoriser (automatique)
            chunks = document_processor.process_file(file_path)
            
            if chunks:
                vector_store_manager.add_documents(chunks)
                successful += 1
                logger.info(f"✅ {file.name} uploadé ({len(chunks)} chunks)")
            else:
                st.warning(f"⚠️ {file.name}: Aucun contenu")
                file_path.unlink()
        
        except Exception as e:
            logger.error(f"❌ Erreur avec {file.name}: {e}")
            st.error(f"❌ {file.name}: {str(e)}")
    
    # Finalisation
    progress_bar.empty()
    status_text.empty()
    
    if successful > 0:
        st.success(f"✅ {successful}/{total} document(s) uploadé(s) et vectorisé(s) avec succès!", icon="✅")
        st.balloons()
        st.rerun()
    else:
        st.error("❌ Aucun document n'a pu être uploadé.")


def _render_documents_list(vector_store_manager: VectorStoreManager):
    """Affiche la liste des documents avec design maquette"""
    
    sources = vector_store_manager.get_all_sources()
    
    if not sources:
        st.info("🔭 Aucun document chargé. Uploadez vos premiers documents ci-dessus.", icon="🔭")
        return
    
    # Filtres
    col_search, col_type, col_sort = st.columns(3)
    
    with col_search:
        search_term = st.text_input("🔍 Rechercher", placeholder="Nom du document...", key="search_doc")
    
    with col_type:
        filter_type = st.selectbox("Type", ["Tous les types", ".txt", ".csv", ".html"], key="filter_type")
    
    with col_sort:
        sort_by = st.selectbox("Trier par", ["Date (récent)", "Date (ancien)", "Nom", "Taille"], key="sort_by")
    
    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
    
    # Afficher les documents en grille (3 par ligne)
    filtered_sources = sources
    if filter_type != "Tous les types":
        filtered_sources = [s for s in sources if s.endswith(filter_type)]
    
    if search_term:
        filtered_sources = [s for s in filtered_sources if search_term.lower() in s.lower()]
    
    if not filtered_sources:
        st.warning("Aucun document ne correspond aux critères de recherche.")
        return
    
    # Affichage en grille
    for i in range(0, len(filtered_sources), 3):
        cols = st.columns(3)
        
        for j, col in enumerate(cols):
            if i + j < len(filtered_sources):
                source = filtered_sources[i + j]
                with col:
                    _render_document_card(source, vector_store_manager)
    
    # Bouton supprimer tout
    if sources:
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🗑️ Tout supprimer", use_container_width=True, key="delete_all"):
                if st.session_state.get("confirm_delete_all"):
                    _delete_all_documents(vector_store_manager)
                else:
                    st.session_state.confirm_delete_all = True
                    st.warning("⚠️ Cliquez à nouveau pour confirmer")


def _render_document_card(source: str, vector_store_manager: VectorStoreManager):
    """Affiche une card pour un document (design maquette)"""
    
    # Extension et icône
    extension = Path(source).suffix.lower()
    icon_map = {".txt": "📄", ".csv": "📊", ".html": "🌐"}
    icon = icon_map.get(extension, "📄")
    
    # Card
    st.markdown(f"""
        <div class="doc-card">
            <div class="doc-icon">{icon}</div>
            <div class="doc-name" title="{source}">{source}</div>
            <div class="doc-ext">{extension.upper().replace('.', '')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Boutons
    col_view, col_delete = st.columns(2)
    
    with col_view:
        if st.button("👁️", key=f"view_{source}", use_container_width=True, help="Visualiser"):
            st.info(f"Visualisation de {source}")
    
    with col_delete:
        if st.button("🗑️", key=f"del_{source}", use_container_width=True, help="Supprimer"):
            _delete_document(source, vector_store_manager)


def _delete_document(source: str, vector_store_manager: VectorStoreManager):
    """Supprime un document"""
    try:
        with st.spinner(f"Suppression de {source}..."):
            # Supprimer de la base vectorielle
            success = vector_store_manager.delete_document_by_source(source)
            
            if success:
                # Supprimer le fichier physique
                file_path = UPLOAD_DIR / source
                if file_path.exists():
                    file_path.unlink()
                
                st.success(f"✅ {source} supprimé!")
                logger.info(f"🗑️ Document supprimé: {source}")
                st.rerun()
            else:
                st.error(f"❌ Impossible de supprimer {source}")
    
    except Exception as e:
        logger.error(f"❌ Erreur suppression: {e}")
        st.error(f"❌ Erreur: {str(e)}")


def _delete_all_documents(vector_store_manager: VectorStoreManager):
    """Supprime tous les documents"""
    try:
        vector_store_manager.clear()
        # Supprimer les fichiers physiques
        for file in UPLOAD_DIR.glob("*"):
            if file.is_file():
                file.unlink()
        st.success("✅ Tous les documents supprimés!")
        st.session_state.confirm_delete_all = False
        logger.info("🗑️ Tous les documents supprimés")
        st.rerun()
    except Exception as e:
        logger.error(f"❌ Erreur suppression totale: {e}")
        st.error(f"❌ Erreur: {str(e)}")


def _render_pipeline_section():
    """Section pipeline de traitement (design maquette)"""
    
    st.markdown("### ⚙️ Pipeline de traitement")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="pipeline-step">
                <h4>1️⃣ Nettoyage</h4>
                <ul>
                    <li>✓ Suppression caractères spéciaux</li>
                    <li>✓ Normalisation du texte</li>
                    <li>✓ Extraction contenu pertinent</li>
                    <li>✓ Détection de l'encodage</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="pipeline-step">
                <h4>2️⃣ Chunking</h4>
                <ul>
                    <li>✓ Découpage intelligent</li>
                    <li>✓ Taille: 500 tokens</li>
                    <li>✓ Overlap: 50 tokens</li>
                    <li>✓ Préservation du contexte</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="pipeline-step">
                <h4>3️⃣ Vectorisation</h4>
                <ul>
                    <li>✓ Embeddings: text-ada-002</li>
                    <li>✓ Base: ChromaDB</li>
                    <li>✓ Indexation automatique</li>
                    <li>✓ Recherche sémantique</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)