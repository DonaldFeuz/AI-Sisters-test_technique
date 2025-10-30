"""
Gestionnaire de l'historique des conversations
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger

from src.config.settings import DATA_DIR, CONVERSATIONS_DIR


class ConversationManager:
    """Gestionnaire pour sauvegarder et charger les conversations"""
    
    def __init__(self):
        self.conversations_dir = CONVERSATIONS_DIR
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ ConversationManager initialisé (dir: {self.conversations_dir})")
    
    def save_conversation(
        self, 
        conversation_id: str, 
        messages: List[Dict],
        title: Optional[str] = None
    ) -> bool:
        """
        Sauvegarde une conversation
        
        Args:
            conversation_id: ID unique de la conversation
            messages: Liste des messages
            title: Titre optionnel (sinon première question)
            
        Returns:
            True si succès
        """
        try:
            # Générer un titre si non fourni
            if not title and messages:
                first_user_msg = next(
                    (msg["content"] for msg in messages if msg["role"] == "user"), 
                    "Nouvelle conversation"
                )
                title = first_user_msg[:50] + ("..." if len(first_user_msg) > 50 else "")
            
            # Préparer les données
            conversation_data = {
                "id": conversation_id,
                "title": title or "Nouvelle conversation",
                "created_at": conversation_id.replace("conv_", "").replace("_", " "),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message_count": len(messages),
                "messages": messages
            }
            
            # Sauvegarder dans un fichier JSON
            file_path = self.conversations_dir / f"{conversation_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Conversation sauvegardée: {conversation_id} ({len(messages)} messages)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde de la conversation: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Charge une conversation
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Données de la conversation ou None
        """
        try:
            file_path = self.conversations_dir / f"{conversation_id}.json"
            
            if not file_path.exists():
                logger.warning(f"⚠️ Conversation introuvable: {conversation_id}")
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                conversation_data = json.load(f)
            
            logger.info(f"📂 Conversation chargée: {conversation_id}")
            return conversation_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de la conversation: {e}")
            return None
    
    def list_conversations(self) -> List[Dict]:
        """
        Liste toutes les conversations sauvegardées
        
        Returns:
            Liste des métadonnées des conversations (triées par date, plus récentes en premier)
        """
        try:
            conversations = []
            
            for file_path in self.conversations_dir.glob("conv_*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Extraire uniquement les métadonnées (pas les messages)
                    conversations.append({
                        "id": data["id"],
                        "title": data["title"],
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "message_count": data.get("message_count", 0)
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de lire {file_path.name}: {e}")
            
            # Trier par date de mise à jour (plus récent en premier)
            conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            
            logger.info(f"📋 {len(conversations)} conversations trouvées")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du listage des conversations: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Supprime une conversation
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            True si succès
        """
        try:
            file_path = self.conversations_dir / f"{conversation_id}.json"
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️ Conversation supprimée: {conversation_id}")
                return True
            else:
                logger.warning(f"⚠️ Conversation introuvable: {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression: {e}")
            return False
    
    def generate_conversation_id(self) -> str:
        """
        Génère un ID unique pour une nouvelle conversation
        
        Returns:
            ID au format conv_YYYYMMDD_HHMMSS
        """
        return f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"