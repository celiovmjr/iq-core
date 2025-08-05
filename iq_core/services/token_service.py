from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict
from cryptography.fernet import Fernet
import hashlib


@dataclass
class TokenManager:
    """
    Manages encrypted token storage per email using Fernet and MD5-hashed filenames.

    Gerencia armazenamento criptografado de tokens por e-mail usando Fernet e nomes de arquivos em hash MD5.
    """

    directory: str = ".tokens"
    keyfile: str = ".token_key"

    _tokens: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _fernet: Fernet = field(init=False, repr=False)
    _dir_path: Path = field(init=False, repr=False)
    _key_path: Path = field(init=False, repr=False)
    _index: dict[str, str] = field(
        default_factory=dict, init=False, repr=False
    )  # md5 -> email

    def __post_init__(self) -> None:
        self._dir_path = Path(self.directory)
        self._key_path = Path(self.keyfile)
        self._dir_path.mkdir(parents=True, exist_ok=True)

        self._fernet = Fernet(self._load_or_create_key())
        self._tokens = self._load_all_tokens()

    def _load_or_create_key(self) -> bytes:
        """
        Load Fernet key from file, or generate and persist a new one.
        Carrega a chave Fernet do arquivo ou gera e salva uma nova.
        """
        if self._key_path.exists():
            return self._key_path.read_bytes()

        key = Fernet.generate_key()
        self._key_path.write_bytes(key)
        return key

    def _email_hash(self, email: str) -> str:
        """
        Create lowercase MD5 hash of email.
        Gera hash MD5 (minúsculo) do e-mail.
        """
        return hashlib.md5(email.strip().lower().encode()).hexdigest()

    def _token_file(self, email: str) -> Path:
        """
        Return full path for the token file based on hashed email.
        Retorna o caminho do arquivo do token com base no hash do e-mail.
        """
        return self._dir_path / self._email_hash(email)

    def _load_token_from_file(self, path: Path) -> str | None:
        try:
            encrypted = path.read_bytes()
            return self._fernet.decrypt(encrypted).decode("utf-8")
        except Exception:
            return None

    def _load_all_tokens(self) -> dict[str, str]:
        """
        Load all stored tokens from the directory.
        Carrega todos os tokens armazenados no diretório.
        """
        tokens: dict[str, str] = {}
        for file in self._dir_path.glob("*"):
            if not file.is_file():
                continue

            token = self._load_token_from_file(file)
            if token:
                hashed = file.name
                self._index[hashed] = ""  # preenchido dinamicamente ao usar set_token()
                tokens[hashed] = token

        return tokens

    def _save_token(self, email: str, token: str) -> None:
        path = self._token_file(email)
        encrypted = self._fernet.encrypt(token.encode("utf-8"))
        path.write_bytes(encrypted)

    def _delete_token(self, email: str) -> None:
        path = self._token_file(email)
        if path.exists():
            path.unlink()

    @property
    def tokens(self) -> dict[str, str]:
        """
        Return a copy of all stored tokens, keyed by original emails.
        Retorna uma cópia dos tokens armazenados, com e-mails como chave.
        """
        return {
            email: self._tokens[hash_]
            for hash_, email in self._index.items()
            if hash_ in self._tokens
        }

    def get_token(self, email: str) -> str | None:
        """
        Get the token for the given email, or None if not found.
        Retorna o token para o e-mail fornecido, ou None se não encontrado.
        """
        hash_ = self._email_hash(email)
        return self._tokens.get(hash_)

    def set_token(self, email: str, token: str) -> None:
        """
        Store or update the token for an email.
        Armazena ou atualiza o token para um e-mail.
        """
        hash_ = self._email_hash(email)
        self._tokens[hash_] = token
        self._index[hash_] = email
        self._save_token(email, token)

    def remove_token(self, email: str) -> None:
        """
        Remove the token for an email, if it exists.
        Remove o token para um e-mail, se existir.
        """
        hash_ = self._email_hash(email)
        if self._tokens.pop(hash_, None) is not None:
            self._index.pop(hash_, None)
            self._delete_token(email)
