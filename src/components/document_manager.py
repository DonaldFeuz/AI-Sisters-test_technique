"""
Page Streamlit : Gestion des documents
"""
import streamlit as st
from pathlib import Path
from typing import List
from loguru import logger

from src.config.settings import UPLOAD_DIR, SUPPORTED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from src.utils.document_processor import DocumentProcessor
from src.utils.vector_store import VectorStoreManager


def render_document_manager(
    vector_store_manager: VectorStoreManager,
    document_processor: DocumentProcessor
):
    """
    Affiche la page de gestion des documents
    
    Args:
        vector_store_manager: Gestionnaire de la base vectorielle
        document_processor: Processeur de documents
    """
    st.title("📄 Gestion des Documents")
    st.markdown("---")
    
    # Afficher les statistiques de la base vectorielle
    _display_stats(vector_store_manager)
    
    st.markdown("---")
    
    # Section 1 : Upload de documents
    st.header("📤 Uploader des Documents")
    _upload_section(vector_store_manager, document_processor)
    
    st.markdown("---")
    
    # Section 2 : Liste des documents
    st.header("📚 Documents dans la Base")
    _documents_list_section(vector_store_manager)
    
    st.markdown("---")
    
    # Section 3 : Actions globales
    st.header("🔧 Actions Globales")
    _global_actions_section(vector_store_manager)


def _display_stats(vector_store_manager: VectorStoreManager):
    """Affiche les statistiques de la base vectorielle"""
    stats = vector_store_manager.get_stats()
    
    # Afficher dans des colonnes
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Chunks",
            value=stats["total_chunks"],
            help="Nombre total de morceaux de texte dans la base"
        )
    
    with col2:
        st.metric(
            label="📁 Documents",
            value=stats["total_sources"],
            help="Nombre de fichiers sources uploadés"
        )
    
    with col3:
        st.metric(
            label="🔧 Vector Store",
            value=stats["vector_store_type"].upper(),
            help="Type de base vectorielle utilisée"
        )
    
    with col4:
        status_emoji = "✅" if stats["status"] == "ready" else "⚠️"
        st.metric(
            label="📡 Statut",
            value=f"{status_emoji} {stats['status'].upper()}",
            help="État de la base vectorielle"
        )
    
    # Afficher les détails si la base contient des documents
    if stats["total_chunks"] > 0:
        with st.expander("ℹ️ Détails de la Configuration"):
            st.write(f"**Modèle d'embedding :** `{stats['embedding_model']}`")
            st.write(f"**Top-K résultats :** `{stats['top_k_results']}`")
            st.write(f"**Sources :** {', '.join(stats['sources']) if stats['sources'] else 'Aucune'}")


def _upload_section(
    vector_store_manager: VectorStoreManager,
    document_processor: DocumentProcessor
):
    """Section d'upload de documents"""
    
    # Informations sur les formats supportés
    st.info(
        f"📋 **Formats supportés :** {', '.join(SUPPORTED_EXTENSIONS)}\n\n"
        f"📏 **Taille maximale :** {MAX_UPLOAD_SIZE_MB} MB par fichier"
    )
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Sélectionnez un ou plusieurs fichiers",
        type=[ext.replace(".", "") for ext in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
        help="Vous pouvez sélectionner plusieurs fichiers à la fois"
    )
    
    if uploaded_files:
        st.write(f"📦 **{len(uploaded_files)} fichier(s) sélectionné(s)**")
        
        # Bouton pour traiter les fichiers
        if st.button("🚀 Traiter et Ajouter à la Base", type="primary", use_container_width=True):
            _process_uploaded_files(
                uploaded_files,
                vector_store_manager,
                document_processor
            )


def _process_uploaded_files(
    uploaded_files: List,
    vector_store_manager: VectorStoreManager,
    document_processor: DocumentProcessor
):
    """Traite et ajoute les fichiers uploadés à la base vectorielle"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(uploaded_files)
    total_chunks_added = 0
    success_count = 0
    error_count = 0
    
    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            # Mise à jour de la progression
            progress = (idx + 1) / total_files
            progress_bar.progress(progress)
            status_text.text(f"Traitement de {uploaded_file.name}... ({idx + 1}/{total_files})")
            
            # Sauvegarder temporairement le fichier
            file_path = UPLOAD_DIR / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            logger.info(f"📄 Fichier sauvegardé: {file_path}")
            
            # Valider le fichier
            is_valid, error_msg = document_processor.validate_file(
                file_path,
                max_size_mb=MAX_UPLOAD_SIZE_MB
            )
            
            if not is_valid:
                st.error(f"❌ **{uploaded_file.name}** : {error_msg}")
                error_count += 1
                continue
            
            # Traiter le fichier
            chunks = document_processor.process_file(file_path)
            
            if not chunks:
                st.warning(f"⚠️ **{uploaded_file.name}** : Aucun contenu extrait")
                error_count += 1
                continue
            
            # Ajouter à la base vectorielle
            num_added = vector_store_manager.add_documents(chunks)
            total_chunks_added += num_added
            success_count += 1
            
            st.success(
                f"✅ **{uploaded_file.name}** : {num_added} chunks ajoutés"
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de {uploaded_file.name}: {e}")
            st.error(f"❌ **{uploaded_file.name}** : Erreur - {str(e)}")
            error_count += 1
    
    # Finalisation
    progress_bar.progress(1.0)
    status_text.empty()
    
    # Résumé
    st.markdown("---")
    st.subheader("📊 Résumé du Traitement")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Succès", success_count)
    
    with col2:
        st.metric("❌ Erreurs", error_count)
    
    with col3:
        st.metric("📦 Chunks Ajoutés", total_chunks_added)
    
    if success_count > 0:
        st.balloons()
        st.success(
            f"🎉 **{success_count} document(s) traité(s) avec succès !** "
            f"Vous pouvez maintenant poser des questions dans la section Chat."
        )


def _documents_list_section(vector_store_manager: VectorStoreManager):
    """Affiche la liste des documents dans la base"""
    
    sources = vector_store_manager.get_all_sources()
    
    if not sources:
        st.info("📭 Aucun document dans la base. Uploadez des documents ci-dessus pour commencer.")
        return
    
    st.write(f"**{len(sources)} document(s) dans la base :**")
    
    # Afficher chaque document avec option de suppression
    for source in sources:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write(f"📄 **{source}**")
        
        with col2:
            # Bouton de suppression avec clé unique
            if st.button(
                "🗑️ Supprimer",
                key=f"delete_{source}",
                help=f"Supprimer {source} de la base"
            ):
                _delete_document(source, vector_store_manager)


def _delete_document(source_name: str, vector_store_manager: VectorStoreManager):
    """Supprime un document de la base vectorielle"""
    
    with st.spinner(f"Suppression de {source_name}..."):
        try:
            success = vector_store_manager.delete_by_source(source_name)
            
            if success:
                st.success(f"✅ **{source_name}** supprimé avec succès !")
                logger.info(f"✅ Document supprimé: {source_name}")
                
                # Rafraîchir la page pour mettre à jour l'affichage
                st.rerun()
            else:
                st.error(f"❌ Impossible de supprimer **{source_name}**")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression de {source_name}: {e}")
            st.error(f"❌ Erreur : {str(e)}")


def _global_actions_section(vector_store_manager: VectorStoreManager):
    """Actions globales sur la base vectorielle"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Rafraîchir les statistiques
        if st.button(
            "🔄 Rafraîchir les Statistiques",
            use_container_width=True,
            help="Recharge les statistiques de la base"
        ):
            st.rerun()
    
    with col2:
        # Vider complètement la base
        if st.button(
            "🗑️ Vider Complètement la Base",
            use_container_width=True,
            type="secondary",
            help="⚠️ Supprime TOUS les documents de la base (irréversible)"
        ):
            _confirm_clear_database(vector_store_manager)


def _confirm_clear_database(vector_store_manager: VectorStoreManager):
    """Dialogue de confirmation pour vider la base"""
    
    st.warning("⚠️ **Attention !** Cette action est irréversible.")
    
    # Utiliser un dialogue de confirmation
    confirm = st.checkbox(
        "Je confirme vouloir supprimer TOUS les documents de la base",
        key="confirm_clear"
    )
    
    if confirm:
        if st.button("✅ Confirmer la Suppression", type="primary"):
            with st.spinner("Suppression en cours..."):
                try:
                    vector_store_manager.clear()
                    st.success("✅ Base vectorielle vidée avec succès !")
                    logger.info("✅ Base vectorielle vidée")
                    
                    # Supprimer les fichiers uploadés
                    for file_path in UPLOAD_DIR.glob("*"):
                        if file_path.is_file():
                            file_path.unlink()
                    
                    st.balloons()
                    
                    # Rafraîchir la page
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"❌ Erreur lors du vidage de la base: {e}")
                    st.error(f"❌ Erreur : {str(e)}")