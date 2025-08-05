from __future__ import annotations

import re
import math
from datetime import datetime, timedelta
from typing import Union, ClassVar
from dataclasses import dataclass, field
from ..exceptions import InvalidTargetTime, ValidationError


@dataclass(frozen=True)
class Duration:
    """
    🇧🇷 Classe imutável para representar durações em minutos, com parsing flexível
    de strings (ex: "1h30m", "45s") e suporte a operações aritméticas e comparações.

    🇺🇸 Immutable class representing durations in minutes, with flexible string parsing
    (e.g. "1h30m", "45s") and support for arithmetic operations and comparisons.

    Atributos:
    - _raw_value (float | str): valor inicial (minutos ou string a ser parseada)
    - _minutes (float): duração interna em minutos

    Internamente, a duração é armazenada em minutos como float.
    """

    _raw_value: Union[float, str] = field(default=0.0, repr=False)
    _minutes: float = field(init=False, repr=True)

    _time_pattern: ClassVar[re.Pattern] = re.compile(r"(\d+)([smhd]?)", re.IGNORECASE)

    def __post_init__(self) -> None:
        """🇧🇷 Inicializa a duração convertendo _raw_value para minutos, validando valores negativos.

        🇺🇸 Initializes the duration by converting _raw_value to minutes, validating non-negative values.

        Raises:
            ValidationError: se o valor calculado for negativo
        """
        minutes = self._parse(self._raw_value) if isinstance(self._raw_value, str) else float(self._raw_value)
        if minutes < 0:
            raise ValidationError("Duration must be non-negative")
        object.__setattr__(self, "_minutes", minutes)

    def _parse(self, value: str) -> float:
        """🇧🇷 Converte string para minutos, aceitando s,m,h,d.

        🇺🇸 Parses a string into minutes, supporting s,m,h,d units.

        Args:
            value (str): string representando duração (ex: "1h30m", "45s")

        Returns:
            float: duração em minutos

        Raises:
            ValidationError: se o formato ou unidade forem inválidos
        """
        matches = self._time_pattern.findall(value.strip().lower())
        if not matches:
            raise ValidationError(f"Invalid duration format: '{value}'")

        total = 0.0
        for amount_str, unit in matches:
            amount = int(amount_str)
            match unit:
                case "s":
                    total += amount / 60
                case "m" | "":
                    total += amount
                case "h":
                    total += amount * 60
                case "d":
                    total += amount * 1440
                case _:
                    raise ValidationError(f"Invalid duration unit: '{unit}'")
        return total

    def add(self, value: Union[int, float, str]) -> Duration:
        """🇧🇷 Retorna nova duração adicionando valor dado.

        🇺🇸 Returns new Duration adding the given value.

        Args:
            value (int | float | str): valor a adicionar (minutos ou string)

        Returns:
            Duration: nova instância com o valor somado

        Raises:
            ValidationError: se o resultado for negativo
        """
        return self + value

    def sub(self, value: Union[int, float, str]) -> Duration:
        """🇧🇷 Retorna nova duração subtraindo valor dado.

        🇺🇸 Returns new Duration subtracting the given value.

        Args:
            value (int | float | str): valor a subtrair (minutos ou string)

        Returns:
            Duration: nova instância com o valor subtraído

        Raises:
            ValidationError: se o resultado for negativo
        """
        return self - value

    def minutes(self) -> int:
        """🇧🇷 Retorna duração em minutos arredondada para cima.

        🇺🇸 Returns duration in minutes rounded up.

        Returns:
            int: minutos arredondados para cima
        """
        return math.ceil(self._minutes)

    def seconds(self) -> float:
        """🇧🇷 Retorna duração em segundos.

        🇺🇸 Returns duration in seconds.

        Returns:
            float: duração em segundos
        """
        return self._minutes * 60

    def ms(self) -> float:
        """🇧🇷 Retorna duração em milissegundos.

        🇺🇸 Returns duration in milliseconds.

        Returns:
            float: duração em milissegundos
        """
        return self.seconds() * 1000

    def timestamp(self) -> int:
        """🇧🇷 Retorna timestamp UNIX para o instante atual + duração.

        🇺🇸 Returns UNIX timestamp for now plus the duration.

        Returns:
            int: timestamp UNIX futuro
        """
        return int((datetime.now() + timedelta(minutes=self._minutes)).timestamp())

    def until(self, target_time: str) -> Duration:
        """🇧🇷 Retorna duração até horário futuro "HH:MM".

        🇺🇸 Returns duration until future time "HH:MM".

        Args:
            target_time (str): horário alvo no formato "HH:MM"

        Returns:
            Duration: duração até o horário alvo

        Raises:
            InvalidTargetTime: se o formato for inválido ou horário já passou
        """
        try:
            now = datetime.now().replace(second=0, microsecond=0)
            target = datetime.strptime(target_time, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        except ValueError as e:
            raise InvalidTargetTime(f"Invalid format for target time: {target_time!r}") from e

        if target < now:
            raise InvalidTargetTime(f"Target time {target_time!r} is in the past.")

        return Duration((target - now).total_seconds() / 60)

    # Operadores aritméticos

    def __add__(self, other: Union[Duration, int, float, str]) -> Duration:
        """
        🇧🇷 Soma esta duração com outra Duration, número (minutos) ou string.

        🇺🇸 Adds this duration with another Duration, number (minutes), or string.

        Raises:
            ValidationError: se a duração resultante for negativa
        """
        if isinstance(other, Duration):
            new_minutes = self._minutes + other._minutes
        elif isinstance(other, str):
            new_minutes = self._minutes + self._parse(other)
        elif isinstance(other, (int, float)):
            new_minutes = self._minutes + float(other)
        else:
            return NotImplemented

        if new_minutes < 0:
            raise ValidationError("Resulting duration must be non-negative")

        return Duration(new_minutes)

    def __radd__(self, other: Union[int, float, str]) -> Duration:
        """🇧🇷 Suporta a + Duration.

        🇺🇸 Supports number + Duration.
        """
        return self.__add__(other)

    def __sub__(self, other: Union[Duration, int, float, str]) -> Duration:
        """
        🇧🇷 Subtrai outra duração, número (minutos) ou string desta duração.

        🇺🇸 Subtracts another duration, number (minutes), or string from this duration.

        Raises:
            ValidationError: se a duração resultante for negativa
        """
        if isinstance(other, Duration):
            new_minutes = self._minutes - other._minutes
        elif isinstance(other, str):
            new_minutes = self._minutes - self._parse(other)
        elif isinstance(other, (int, float)):
            new_minutes = self._minutes - float(other)
        else:
            return NotImplemented

        if new_minutes < 0:
            raise ValidationError("Resulting duration must be non-negative")

        return Duration(new_minutes)

    def __rsub__(self, other: Union[int, float, str]) -> Duration:
        """
        🇧🇷 Suporta número - Duration ou string - Duration.

        🇺🇸 Supports number - Duration or string - Duration.

        Raises:
            ValidationError: se a duração resultante for negativa
        """
        if isinstance(other, (int, float)):
            new_minutes = float(other) - self._minutes
        elif isinstance(other, str):
            new_minutes = self._parse(other) - self._minutes
        else:
            return NotImplemented

        if new_minutes < 0:
            raise ValidationError("Resulting duration must be non-negative")

        return Duration(new_minutes)

    # Operadores de comparação

    def __eq__(self, other: object) -> bool:
        """
        🇧🇷 Verifica igualdade com outra Duration ou número (minutos).

        🇺🇸 Checks equality with another Duration or number (minutes).
        """
        if isinstance(other, Duration):
            return math.isclose(self._minutes, other._minutes)
        if isinstance(other, (int, float)):
            return math.isclose(self._minutes, float(other))
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        """
        🇧🇷 Verifica desigualdade com outra Duration ou número.

        🇺🇸 Checks inequality with another Duration or number.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __lt__(self, other: Union[Duration, int, float]) -> bool:
        """
        🇧🇷 Menor que outra Duration ou número.

        🇺🇸 Less than another Duration or number.
        """
        if isinstance(other, Duration):
            return self._minutes < other._minutes
        if isinstance(other, (int, float)):
            return self._minutes < float(other)
        return NotImplemented

    def __le__(self, other: Union[Duration, int, float]) -> bool:
        """
        🇧🇷 Menor ou igual a outra Duration ou número.

        🇺🇸 Less than or equal to another Duration or number.
        """
        if isinstance(other, Duration):
            return self._minutes <= other._minutes
        if isinstance(other, (int, float)):
            return self._minutes <= float(other)
        return NotImplemented

    def __gt__(self, other: Union[Duration, int, float]) -> bool:
        """
        🇧🇷 Maior que outra Duration ou número.

        🇺🇸 Greater than another Duration or number.
        """
        if isinstance(other, Duration):
            return self._minutes > other._minutes
        if isinstance(other, (int, float)):
            return self._minutes > float(other)
        return NotImplemented

    def __ge__(self, other: Union[Duration, int, float]) -> bool:
        """
        🇧🇷 Maior ou igual a outra Duration ou número.

        🇺🇸 Greater than or equal to another Duration or number.
        """
        if isinstance(other, Duration):
            return self._minutes >= other._minutes
        if isinstance(other, (int, float)):
            return self._minutes >= float(other)
        return NotImplemented

    def __repr__(self) -> str:
        """🇧🇷 Representação amigável para debug.

        🇺🇸 Friendly debug representation.
        """
        return f"<Duration: {self._minutes:.2f} min>"
