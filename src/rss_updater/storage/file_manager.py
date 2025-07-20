"""File management for blog storage."""

import json
import shutil
from pathlib import Path
from typing import Dict


class FileManager:
    """Handles file operations for blog storage."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
    
    def load_data(self) -> Dict:
        """Load blog states from JSON file."""
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in storage file {self.storage_path}: {e}")
            self._create_backup()
            return {}
        except Exception as e:
            print(f"Warning: Failed to load storage file {self.storage_path}: {e}")
            return {}
    
    def save_data(self, data: Dict) -> None:
        """Save data to JSON file with automatic backup."""
        # Create backup before writing if file exists
        if self.storage_path.exists():
            backup_path = self.storage_path.with_suffix('.json.bak')
            shutil.copy2(self.storage_path, backup_path)
        
        try:
            # Write to temporary file first, then rename for atomic operation
            temp_path = self.storage_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.rename(self.storage_path)
            
        except Exception as e:
            print(f"Error saving storage file: {e}")
            # Clean up temporary file if it exists
            temp_path = self.storage_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    def _create_backup(self) -> None:
        """Create backup of corrupted storage file."""
        if self.storage_path.exists():
            backup_path = self.storage_path.with_suffix('.backup')
            shutil.copy2(self.storage_path, backup_path)
            print(f"Created backup of corrupted storage file: {backup_path}")