"""
utils.py
Ortak yardimci fonksiyonlar: proje yollari, JSON okuma/yazma, zaman damgasi.
Tum dosya yollari pathlib ile yonetilir. Boylece Windows/Linux/macOS uyumludur.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Proje kok dizini (bu dosya src/ altinda oldugundan bir ust klasor)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Sik kullanilan klasor yollari
DATA_DIR = PROJECT_ROOT / "data"
DEMO_ENV_DIR = PROJECT_ROOT / "demo_environment"
MAILBOX_DIR = DEMO_ENV_DIR / "fake_mailbox"
DESKTOP_DIR = DEMO_ENV_DIR / "fake_desktops"
LOGS_DIR = DEMO_ENV_DIR / "fake_logs"


def project_path(*parts: str) -> Path:
    """Proje kokune gore mutlak yol uretir. Ornek: project_path('data', 'users.json')."""
    return PROJECT_ROOT.joinpath(*parts)


def read_json(path: str | Path, default: Any = None) -> Any:
    """
    JSON dosyasini guvenli okur. Dosya yoksa veya bozuksa 'default' doner.
    """
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default if default is not None else {}


def write_json(path: str | Path, data: Any) -> bool:
    """
    Veriyi JSON olarak yazar. Gerekirse ust klasorleri olusturur.
    Basarili olursa True doner.
    """
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def append_jsonl(path: str | Path, record: dict) -> bool:
    """
    Tek satirlik JSON kaydini (.jsonl) dosyanin sonuna ekler.
    Audit log icin kullanilir.
    """
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def read_jsonl(path: str | Path) -> list[dict]:
    """
    .jsonl dosyasini satir satir okuyup liste doner. Dosya yoksa bos liste.
    """
    path = Path(path)
    records: list[dict] = []
    if not path.exists():
        return records
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return records
    return records


def now_str() -> str:
    """Su anki zamani 'YYYY-MM-DD HH:MM:SS' formatinda doner."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_within(base_dir: Path, target: Path) -> bool:
    """
    Guvenlik kontrolu: 'target' yolunun 'base_dir' icinde kaldigini dogrular.
    Fake klasorler disina cikan hicbir dosya islemine izin verilmez.
    """
    try:
        target.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False
