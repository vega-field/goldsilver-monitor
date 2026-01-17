import os
from datetime import datetime
from typing import Dict

class ObsidianAlert:
    def __init__(self, vault_path: str = None, notes_dir: str = "goldsilver-alerts"):
        self.vault_path = vault_path or os.environ.get("OBSIDIAN_VAULT_PATH")
        self.notes_dir = notes_dir

    def send(self, result: Dict):
        """簡易: Obsidian Vault に Markdown ファイルを作る"""
        if not self.vault_path:
            # vault が指定されていなければ stdout に出すだけ
            print("Alert result:", result)
            return

        os.makedirs(os.path.join(self.vault_path, self.notes_dir), exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"{timestamp}-goldsilver-fragility.md"
        path = os.path.join(self.vault_path, self.notes_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Gold-Silver Fragility Alert - {timestamp}\n\n")
            for k, v in result.items():
                f.write(f"- **{k}**: {v}\n")
        return path