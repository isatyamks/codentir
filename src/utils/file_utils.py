import hashlib
import shutil
from pathlib import Path
from typing import Optional, List, Tuple
import mimetypes

from src.config import settings

def get_file_hash(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_extension(file_path: Path) -> str:
    return file_path.suffix.lower()

def get_file_type(file_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(file_path))
    
    if mime_type:
        if mime_type.startswith('text'):
            return 'text'
        elif mime_type.startswith('image'):
            return 'image'
        elif 'pdf' in mime_type:
            return 'pdf'
        elif 'word' in mime_type or 'document' in mime_type:
            return 'docx'
    
    extension = get_file_extension(file_path)
    if extension in ['.txt', '.md', '.markdown']:
        return 'text'
    elif extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
        return 'image'
    elif extension == '.pdf':
        return 'pdf'
    elif extension in ['.docx', '.doc']:
        return 'docx'
    
    return 'unknown'

def validate_file(file_path: Path) -> Tuple[bool, Optional[str]]:
    if not file_path.exists():
        return False, "File does not exist"
    
    if not file_path.is_file():
        return False, "Path is not a file"
    
    extension = get_file_extension(file_path)
    if extension not in settings.allowed_extensions_list:
        return False, f"File type {extension} not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
    
    file_size = file_path.stat().st_size
    if file_size > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        return False, f"File too large ({actual_mb:.2f}MB). Maximum: {max_mb:.2f}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None

def organize_upload(file_path: Path, original_name: Optional[str] = None) -> Path:
    file_type = get_file_type(file_path)
    
    type_dir_map = {
        'pdf': 'pdfs',
        'docx': 'docs',
        'text': 'text',
        'image': 'images',
    }
    
    subdir = type_dir_map.get(file_type, 'other')
    target_dir = settings.upload_path / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    
    filename = original_name or file_path.name
    target_path = target_dir / filename
    
    if target_path.exists():
        base_name = target_path.stem
        extension = target_path.suffix
        counter = 1
        while target_path.exists():
            target_path = target_dir / f"{base_name}_{counter}{extension}"
            counter += 1
    
    shutil.copy2(file_path, target_path)
    return target_path

def get_all_uploaded_files() -> List[Path]:
    all_files = []
    
    for pattern in ['**/*.txt', '**/*.md', '**/*.pdf', '**/*.docx', '**/*.png', '**/*.jpg', '**/*.jpeg']:
        all_files.extend(settings.upload_path.glob(pattern))
    
    return sorted(all_files)

def delete_file(file_path: Path) -> bool:
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception as e:
        return False

def clean_directory(directory: Path, pattern: str = "*") -> int:
    count = 0
    try:
        for item in directory.glob(pattern):
            if item.is_file():
                item.unlink()
                count += 1
            elif item.is_dir() and item.name != '.gitkeep':
                shutil.rmtree(item)
                count += 1
        return count
    except Exception as e:
        return count

def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def get_relative_path(file_path: Path, base_path: Optional[Path] = None) -> str:
    base = base_path or settings.base_dir
    try:
        return str(file_path.relative_to(base))
    except ValueError:
        return str(file_path)
