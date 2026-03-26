"""Runtime context for node execution."""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class RunContext:
    """
    Context object passed to nodes during execution.
    
    Provides access to:
    - run_id: Unique identifier for this run
    - project_id: Project ID for this run
    - api_keys: Dictionary of API keys (key_name -> decrypted value)
    - project_system_prompt: Optional system prompt from the project
    - secrets: Key-value store for sensitive data (API keys, etc.) - deprecated, use api_keys
    - metadata: Additional runtime metadata
    """
    
    run_id: str
    project_id: Optional[int] = None
    api_keys: Dict[str, str] = field(default_factory=dict)
    project_system_prompt: Optional[str] = None
    secrets: Dict[str, str] = field(default_factory=dict)  # Deprecated, use api_keys
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value by key (deprecated, use get_api_key)."""
        return self.secrets.get(key, default)
    
    def get_api_key(self, key_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get an API key by name."""
        return self.api_keys.get(key_name, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value by key."""
        return self.metadata.get(key, default)

