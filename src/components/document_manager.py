"""
Gestionnaire de documents - Page 2 AMÉLIORÉE
Cabinet Parenti - Assistant Juridique IA
"""
import streamlit as st
from pathlib import Path
from typing import List
from loguru import logger
from datetime import datetime

from src.utils.vector_store import VectorStoreManager
from src.utils.document_processor import DocumentProcessor
from src.config.settings import UPLOAD_DIR, SUPPORTED_EXTENSIONS


@st.cache_data(ttl=300)
def get_document_stats(sources: List[str]) -> dict:
    """Cache les statistiques des documents (5 minutes)"""
    stats = {
        "total": len(sources),
        "by_type": {},
        "total_size": 0
    }
    
    for source in sources:
        ext = Path(source).suffix.lower()
        stats["by_type"][ext] = stats["by_type"].get(ext, 0) + 1
        
        # Calculer la taille si le fichier existe
        file_path = UPLOAD_DIR / source
        if file_path.exists():
            stats["total_size"] += file_path.stat().st_size
    
    return stats


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
    
    # Section Upload + Stats (responsive)
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
    """Section upload avec design maquette et glisser-déposer"""
    
    st.markdown("### 📤 Upload de documents")
    
    # Zone de drop améliorée
    st.markdown("""
        <div class="upload-zone">
            <div class="upload-icon">📂</div>
            <h4 style='color: #1e3a5f; margin: 0.5rem 0;'>Glissez-déposez vos fichiers ici</h4>
            <p style='color: #666; margin: 0.5rem 0;'>ou cliquez pour parcourir</p>
            <p style='color: #999; font-size: 0.85rem; margin-top: 1rem;'>
                Formats acceptés : <strong>.txt, .csv, .html</strong><br>
                Taille max : <strong>10 MB par fichier</strong>
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
        # Preview des fichiers uploadés
        st.success(f"✅ {len(uploaded_files)} fichier(s) prêt(s) à être traité(s)")
        
        with st.expander("📋 Aperçu des fichiers", expanded=True):
            for file in uploaded_files:
                file_size = file.size / 1024  # KB
                st.markdown(f"- **{file.name}** ({file_size:.1f} KB)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Traiter et Vectoriser", type="primary", use_container_width=True):
                _handle_upload(uploaded_files, vector_store_manager, document_processor)
        
        with col2:
            if st.button("🗑️ Annuler", use_container_width=True):
                st.rerun()


def _render_stats_card(vector_store_manager: VectorStoreManager):
    """Carte de statistiques améliorée avec cache"""
    
    sources = vector_store_manager.get_all_sources()
    stats = get_document_stats(sources)
    
    # Convertir la taille en format lisible
    size_mb = stats["total_size"] / (1024 * 1024)
    size_str = f"{size_mb:.2f} MB" if size_mb > 1 else f"{stats['total_size'] / 1024:.2f} KB"
    
    st.markdown(f"""
        <div class="stat-card">
            <h2>📊 Statistiques</h2>
            <div class="number">{stats['total']}</div>
            <p style='font-size: 1rem; margin-bottom: 1rem;'>Documents actifs</p>
            
            <div style='background: rgba(255,255,255,0.2); padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;'>
                <div style='font-size: 0.9rem; opacity: 0.9;'>
                    💾 Espace utilisé<br>
                    <strong style='font-size: 1.2rem;'>{size_str}</strong>
                </div>
            </div>
            
            <hr style='margin: 1rem 0; border: none; border-top: 1px solid rgba(255,255,255,0.3);'>
            <p style='font-size: 0.9rem; opacity: 0.9;'>
                ✅ Indexation complète<br>
                🔒 Données sécurisées<br>
                ⚡ Prêt pour recherche
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Types de documents (si présents)
    if stats["by_type"]:
        with st.expander("📊 Répartition par type"):
            for ext, count in stats["by_type"].items():
                percentage = (count / stats["total"]) * 100
                st.progress(percentage / 100, text=f"{ext.upper()}: {count} ({percentage:.0f}%)")


def _handle_upload(
    uploaded_files,
    vector_store_manager: VectorStoreManager,
    document_processor: DocumentProcessor
):
    """Gère l'upload avec gestion d'erreurs améliorée"""
    
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    progress_bar = st.progress(0)
    status_container = st.container()
    
    total = len(uploaded_files)
    successful = 0
    failed = []
    
    for i, file in enumerate(uploaded_files):
        try:
            # Progression
            progress = (i + 1) / total
            progress_bar.progress(progress)
            
            with status_container:
                st.info(f"⏳ Traitement de **{file.name}**... ({i + 1}/{total})")
            
            # Vérifier la taille du fichier (10 MB max)
            if file.size > 10 * 1024 * 1024:
                failed.append((file.name, "Fichier trop volumineux (> 10 MB)"))
                continue
            
            # Sauvegarder
            file_path = UPLOAD_DIR / file.name
            
            # Vérifier si le fichier existe déjà
            if file_path.exists():
                st.warning(f"⚠️ {file.name} existe déjà. Écrasement...")
            
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            
            # Valider
            is_valid, error = document_processor.validate_file(file_path)
            if not is_valid:
                failed.append((file.name, error))
                file_path.unlink()
                continue
            
            # Traiter et vectoriser (automatique)
            chunks = document_processor.process_file(file_path)
            
            if chunks:
                vector_store_manager.add_documents(chunks)
                successful += 1
                logger.info(f"✅ {file.name} uploadé ({len(chunks)} chunks)")
            else:
                failed.append((file.name, "Aucun contenu extractible"))
                file_path.unlink()
        
        except Exception as e:
            error_type = type(e).__name__
            failed.append((file.name, f"{error_type}: {str(e)}"))
            logger.error(f"❌ Erreur avec {file.name}: {e}")
    
    # Finalisation
    progress_bar.empty()
    status_container.empty()
    
    # Résumé des résultats
    if successful > 0:
        st.success(f"✅ {successful}/{total} document(s) uploadé(s) et vectorisé(s) avec succès!", icon="✅")
        st.balloons()
    
    if failed:
        with st.expander(f"⚠️ {len(failed)} échec(s) - Voir détails", expanded=(successful == 0)):
            for filename, error in failed:
                st.error(f"**{filename}**: {error}")
    
    if successful > 0:
        # Invalider le cache des stats
        get_document_stats.clear()
        st.rerun()


def _render_documents_list(vector_store_manager: VectorStoreManager):
    """Affiche la liste des documents avec filtres améliorés"""
    
    sources = vector_store_manager.get_all_sources()
    
    if not sources:
        st.info("🔭 Aucun document chargé. Uploadez vos premiers documents ci-dessus.", icon="🔭")
        return
    
    # Filtres avec colonnes responsive
    col_search, col_type, col_sort = st.columns([2, 1, 1])
    
    with col_search:
        search_term = st.text_input("🔍 Rechercher", placeholder="Nom du document...", key="search_doc")
    
    with col_type:
        # Types disponibles dynamiquement
        available_types = list(set([Path(s).suffix for s in sources]))
        filter_options = ["Tous"] + sorted(available_types)
        filter_type = st.selectbox("Type", filter_options, key="filter_type")
    
    with col_sort:
        sort_by = st.selectbox("Trier par", ["Nom (A-Z)", "Nom (Z-A)", "Type", "Date (récent)"], key="sort_by")
    
    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
    
    # Filtrer les documents
    filtered_sources = sources
    
    if filter_type != "Tous":
        filtered_sources = [s for s in filtered_sources if s.endswith(filter_type)]
    
    if search_term:
        filtered_sources = [s for s in filtered_sources if search_term.lower() in s.lower()]
    
    # Trier
    if sort_by == "Nom (A-Z)":
        filtered_sources = sorted(filtered_sources)
    elif sort_by == "Nom (Z-A)":
        filtered_sources = sorted(filtered_sources, reverse=True)
    elif sort_by == "Type":
        filtered_sources = sorted(filtered_sources, key=lambda x: Path(x).suffix)
    elif sort_by == "Date (récent)":
        # Trier par date de modification si possible
        filtered_sources = sorted(filtered_sources, 
                                 key=lambda x: (UPLOAD_DIR / x).stat().st_mtime if (UPLOAD_DIR / x).exists() else 0, 
                                 reverse=True)
    
    if not filtered_sources:
        st.warning(f"Aucun document ne correspond aux critères de recherche.")
        return
    
    # Affichage du nombre de résultats
    st.markdown(f"<p style='color: #666; font-size: 0.9rem;'>📊 {len(filtered_sources)} document(s) trouvé(s)</p>", 
                unsafe_allow_html=True)
    
    # Affichage en grille responsive (3 colonnes sur desktop, 1 sur mobile)
    for i in range(0, len(filtered_sources), 3):
        cols = st.columns([1, 1, 1])
        
        for j, col in enumerate(cols):
            if i + j < len(filtered_sources):
                source = filtered_sources[i + j]
                with col:
                    _render_document_card(source, vector_store_manager)
    
    # Actions globales
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🔄 Rafraîchir la liste", use_container_width=True):
            get_document_stats.clear()
            st.rerun()
    
    # Bouton supprimer tout (avec confirmation)
    if sources:
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.session_state.get("confirm_delete_all"):
                st.markdown("<p style='color: #d32f2f; text-align: center; font-weight: bold;'>⚠️ Confirmez la suppression</p>", 
                           unsafe_allow_html=True)
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Oui", use_container_width=True, type="primary"):
                        _delete_all_documents(vector_store_manager)
                with col_no:
                    if st.button("❌ Non", use_container_width=True):
                        st.session_state.confirm_delete_all = False
                        st.rerun()
            else:
                if st.button("🗑️ Tout supprimer", use_container_width=True, key="delete_all"):
                    st.session_state.confirm_delete_all = True
                    st.rerun()


def _render_document_card(source: str, vector_store_manager: VectorStoreManager):
    """Affiche une card pour un document avec infos améliorées"""
    
    # Extension et icône
    extension = Path(source).suffix.lower()
    icon_map = {".txt": "📄", ".csv": "📊", ".html": "🌐", ".pdf": "📕"}
    icon = icon_map.get(extension, "📄")
    
    # Infos du fichier
    file_path = UPLOAD_DIR / source
    file_size = ""
    file_date = ""
    
    if file_path.exists():
        size_kb = file_path.stat().st_size / 1024
        file_size = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"
        
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        file_date = mod_time.strftime("%d/%m/%Y")
    
    # Card avec hover effect
    st.markdown(f"""
        <div class="doc-card">
            <div class="doc-icon">{icon}</div>
            <div class="doc-name" title="{source}">{source[:30]}{'...' if len(source) > 30 else ''}</div>
            <div class="doc-ext">{extension.upper().replace('.', '')}</div>
            <div style='margin-top: 0.5rem; font-size: 0.75rem; color: #666;'>
                {file_size} • {file_date}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Boutons avec tooltips
    col_view, col_delete = st.columns(2)
    
    with col_view:
        if st.button("👁️", key=f"view_{source}", use_container_width=True, help="Prévisualiser"):
            _preview_document(source)
    
    with col_delete:
        if st.button("🗑️", key=f"del_{source}", use_container_width=True, help="Supprimer"):
            _delete_document(source, vector_store_manager)


def _preview_document(source: str):
    """Prévisualise un document dans un modal"""
    file_path = UPLOAD_DIR / source
    
    if not file_path.exists():
        st.error(f"❌ Fichier introuvable: {source}")
        return
    
    with st.expander(f"📄 Prévisualisation: {source}", expanded=True):
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Limiter la prévisualisation aux 1000 premiers caractères
            preview = content[:1000]
            if len(content) > 1000:
                preview += "\n\n... (contenu tronqué)"
            
            st.code(preview, language="text")
            st.caption(f"Taille totale: {len(content)} caractères")
        
        except Exception as e:
            st.error(f"❌ Impossible de prévisualiser: {str(e)}")


def _delete_document(source: str, vector_store_manager: VectorStoreManager):
    """Supprime un document avec confirmation"""
    try:
        with st.spinner(f"🗑️ Suppression de {source}..."):
            # Supprimer de la base vectorielle avec la bonne méthode
            success = vector_store_manager.delete_by_source(source)
            
            if success:
                # Supprimer le fichier physique
                file_path = UPLOAD_DIR / source
                if file_path.exists():
                    file_path.unlink()
                
                st.success(f"✅ {source} supprimé!")
                logger.info(f"🗑️ Document supprimé: {source}")
                
                # Invalider le cache
                get_document_stats.clear()
                st.rerun()
            else:
                st.error(f"❌ Impossible de supprimer {source}")
    
    except Exception as e:
        logger.error(f"❌ Erreur suppression: {e}")
        st.error(f"❌ Erreur: {str(e)}")


def _delete_all_documents(vector_store_manager: VectorStoreManager):
    """Supprime tous les documents"""
    try:
        with st.spinner("🗑️ Suppression de tous les documents..."):
            vector_store_manager.clear()
            
            # Supprimer les fichiers physiques
            deleted_count = 0
            for file in UPLOAD_DIR.glob("*"):
                if file.is_file():
                    file.unlink()
                    deleted_count += 1
            
            st.success(f"✅ {deleted_count} document(s) supprimé(s)!")
            st.session_state.confirm_delete_all = False
            logger.info(f"🗑️ Tous les documents supprimés ({deleted_count})")
            
            # Invalider le cache
            get_document_stats.clear()
            st.rerun()
    
    except Exception as e:
        logger.error(f"❌ Erreur suppression totale: {e}")
        st.error(f"❌ Erreur: {str(e)}")


def _render_pipeline_section():
    """Section pipeline de traitement (design maquette)"""
    
    st.markdown("### ⚙️ Pipeline de traitement")
    
    # Responsive: 3 colonnes sur desktop, 1 sur mobile
    cols = st.columns([1, 1, 1])
    
    with cols[0]:
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
    
    with cols[1]:
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
    
    with cols[2]:
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
