# 🚀 IQ Core - Advanced Trading Library

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/Version-1.0.11-green.svg)](https://github.com/itmanagersupport/iq-core)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/Architecture-DDD-purple.svg)](https://en.wikipedia.org/wiki/Domain-driven_design)

*🇧🇷 Biblioteca Python avançada para trading automatizado na IQ Option*  
*🇺🇸 Advanced Python library for automated trading on IQ Option*

</div>

---

## 📋 Índice | Table of Contents

- [🌟 Visão Geral | Overview](#-visão-geral--overview)
- [🏗️ Arquitetura | Architecture](#️-arquitetura--architecture)
- [⚡ Início Rápido | Quick Start](#-início-rápido--quick-start)
- [📚 Entidades | Entities](#-entidades--entities)
- [🔧 Serviços | Services](#-serviços--services)
- [🌐 WebSocket Client](#-websocket-client)
- [⚠️ Exceções | Exceptions](#️-exceções--exceptions)
- [📖 Referência da API | API Reference](#-referência-da-api--api-reference)

---

## 🌟 Visão Geral | Overview

### 🇧🇷 Português

**IQ Core** é uma biblioteca Python moderna para trading automatizado na IQ Option, construída com arquitetura orientada ao domínio (DDD). Oferece uma interface limpa e robusta para desenvolvedores criarem sistemas de trading profissionais.

#### ✨ Características Principais

- 🏗️ **Arquitetura DDD**: Código organizado e maintível
- 🔄 **Suporte Assíncrono**: Performance otimizada com asyncio
- 🛡️ **Type Safety**: Totalmente tipada com Python 3.10+
- 🌐 **WebSocket Real-time**: Comunicação em tempo real
- 📊 **Multi-Asset Trading**: Binary, Digital, Blitz e Forex
- 🔐 **Segurança**: Tokens criptografados e gerenciamento seguro
- 📈 **Gestão de Risco**: Stop-win, stop-loss e controle de exposição

### 🇺🇸 English

**IQ Core** is a modern Python library for automated trading on IQ Option, built with Domain-Driven Design (DDD) architecture. It provides a clean and robust interface for developers to create professional trading systems.

#### ✨ Key Features

- 🏗️ **DDD Architecture**: Organized and maintainable code
- 🔄 **Async Support**: Optimized performance with asyncio
- 🛡️ **Type Safety**: Fully typed with Python 3.10+
- 🌐 **Real-time WebSocket**: Real-time communication
- 📊 **Multi-Asset Trading**: Binary, Digital, Blitz, and Forex
- 🔐 **Security**: Encrypted tokens and secure management
- 📈 **Risk Management**: Stop-win, stop-loss, and exposure control

---

## 🏗️ Arquitetura | Architecture

```
iq_core/
├── 📝 anotations/          # Decorators and utilities
│   ├── connection.py       # Network error handling
│   └── time.py            # Time measurement decorator
├── 🏛️ entities/            # Domain entities
│   ├── account.py         # Account and AccountType
│   ├── candle.py          # Candle data structure
│   ├── candle_stream.py   # Real-time candle stream
│   ├── duration.py        # Duration with flexible parsing
│   ├── instrument.py      # Trading instruments
│   ├── message.py         # WebSocket message protocol
│   ├── profile.py         # User profile
│   ├── signal.py          # Trading signals
│   └── trade_result.py    # Trade execution results
├── ⚠️ exceptions/          # Custom exceptions
│   ├── authentication_error.py
│   ├── connection_error.py
│   ├── iqoption_error.py
│   ├── time_error.py
│   ├── trading_error.py
│   └── validation_error.py
├── 🔧 services/            # Business logic services
│   ├── interfaces/        # Service interfaces
│   ├── account_service.py # Account management
│   ├── auth_service.py    # Authentication
│   ├── binary_trade_service.py    # Binary options
│   ├── blitz_trade_service.py     # Blitz options
│   ├── candle_service.py          # Candle data
│   ├── cotation_service.py        # Price quotations
│   ├── digital_trade_service.py   # Digital options
│   ├── forex_trade_service.py     # Forex trading
│   ├── instrument_resolver.py     # Instrument resolution
│   ├── instrument_service.py      # Instrument management
│   ├── token_service.py           # Token management
│   ├── trade_mood_service.py      # Trader sentiment
│   └── trading_manager_service.py # Risk management
└── 🌐 websocket/           # WebSocket communication
    └── client.py          # WebSocket client
```

---

## ⚡ Início Rápido | Quick Start

### 📦 Instalação | Installation

```bash
pip install iq-core
```

### 🚀 Uso Básico | Basic Usage

#### 🇧🇷 Exemplo Simples

```python
import asyncio
from decimal import Decimal
from iq_core import AuthService, InstrumentService, BinaryTradeService
from iq_core.entities import Signal, Direction, Duration, SignalType

async def exemplo_simples():
    # Autenticação
    auth = AuthService()
    ws, profile = await auth.login("seu_email@exemplo.com", "sua_senha")
    
    # Buscar EUR/USD
    instrument_service = InstrumentService(ws)
    eurusd = await instrument_service.fetch(filter_by="EURUSD")
    
    if eurusd:
        # Criar sinal de trading
        signal = Signal(
            instrument=eurusd,
            balance_id=profile.balance_id,
            direction=Direction.CALL,
            amount=Decimal("10.00"),
            expiration=Duration("5m"),
            type=SignalType.BINARY
        )
        
        # Executar trade
        binary_service = BinaryTradeService(ws, profile)
        trade_id = await binary_service.open_trade(signal)
        print(f"Trade aberto: {trade_id}")
    
    await ws.close()

asyncio.run(exemplo_simples())
```

#### 🇺🇸 Simple Example

```python
import asyncio
from decimal import Decimal
from iq_core import AuthService, InstrumentService, BinaryTradeService
from iq_core.entities import Signal, Direction, Duration, SignalType

async def simple_example():
    # Authentication
    auth = AuthService()
    ws, profile = await auth.login("your_email@example.com", "your_password")
    
    # Search EUR/USD
    instrument_service = InstrumentService(ws)
    eurusd = await instrument_service.fetch(filter_by="EURUSD")
    
    if eurusd:
        # Create trading signal
        signal = Signal(
            instrument=eurusd,
            balance_id=profile.balance_id,
            direction=Direction.CALL,
            amount=Decimal("10.00"),
            expiration=Duration("5m"),
            type=SignalType.BINARY
        )
        
        # Execute trade
        binary_service = BinaryTradeService(ws, profile)
        trade_id = await binary_service.open_trade(signal)
        print(f"Trade opened: {trade_id}")
    
    await ws.close()

asyncio.run(simple_example())
```

---

## 📚 Entidades | Entities

### 🏛️ Modelos de Domínio | Domain Models

#### 📊 Instrument | Instrumento

```python
from iq_core.entities import Instrument, InstrumentType, MarketType

# Propriedades disponíveis
instrument = Instrument(
    id=1,
    name="EUR/USD",
    symbol="EURUSD",
    group_id=1,
    market=MarketType.FOREX,
    type=[InstrumentType.BINARY, InstrumentType.DIGITAL],
    is_enabled=True,
    is_suspended=False,
    trading=TradingInfo(...)  # Informações de trading
)

# Verificar se pode ser negociado
if instrument.is_tradable():
    print("Disponível para trading")

# Verificar se está aberto
if instrument.is_open:
    print("Mercado aberto")
```

#### 💰 Account | Conta

```python
from iq_core.entities import Account, AccountType

# Tipos de conta disponíveis
AccountType.REAL        # Conta real
AccountType.TOURNAMENT  # Torneio
AccountType.PRACTICE    # Conta demo
AccountType.BTC         # Bitcoin
AccountType.ETH         # Ethereum

# Exemplo de conta
account = Account(
    id=12345,
    type=AccountType.PRACTICE,
    amount=10000.0,
    currency="USD",
    is_fiat=True,
    is_marginal=False
)
```

#### ⏱️ Duration | Duração

```python
from iq_core.entities import Duration

# Formas flexíveis de criar durações
duration1 = Duration("5m")        # 5 minutos
duration2 = Duration("1h30m")     # 1 hora e 30 minutos
duration3 = Duration("45s")       # 45 segundos
duration4 = Duration(300)         # 300 minutos

# Operações aritméticas
total = duration1 + duration2     # Soma
remaining = duration3 - "15s"     # Subtração
doubled = duration1 * 2           # Multiplicação

# Conversões
print(f"Minutos: {duration1.minutes()}")
print(f"Segundos: {duration1.seconds()}")
print(f"Milissegundos: {duration1.ms()}")
print(f"Timestamp: {duration1.timestamp()}")

# Até um horário específico
until_close = Duration().until("17:30")

# Comparações
if duration1 > duration2:
    print("Duration1 é maior")
```

#### 📈 Signal | Sinal

```python
from iq_core.entities import Signal, Direction, SignalType
from decimal import Decimal

# Direções disponíveis
Direction.CALL  # Alta
Direction.PUT   # Baixa

# Tipos de sinal
SignalType.BINARY   # Opções binárias
SignalType.DIGITAL  # Opções digitais
SignalType.BLITZ    # Opções blitz
SignalType.FOREX    # Forex

# Criar sinal
signal = Signal(
    instrument=instrument,
    balance_id=12345,
    direction=Direction.CALL,
    amount=Decimal("25.00"),
    expiration=Duration("5m"),
    type=SignalType.BINARY
)
```

#### 📊 Candle | Vela

```python
from iq_core.entities import Candle, CandleStream
from datetime import datetime

# Vela histórica
candle = Candle(
    open=1.1234,
    close=1.1245,
    high=1.1250,
    low=1.1230,
    bid=1.1244,
    ask=1.1246,
    volume=1500.0,
    from_time=datetime.now(),
    to_time=datetime.now(),
    size=300  # 5 minutos em segundos
)

# Vela em tempo real (stream)
candle_stream = CandleStream(
    active_id=1,
    size=300,
    at=1234567890,
    from_time=datetime.now(),
    to_time=datetime.now(),
    id=123,
    open=1.1234,
    close=1.1245,
    min=1.1230,
    max=1.1250,
    ask=1.1246,
    bid=1.1244,
    volume=1500.0,
    phase=None
)
```

#### 👤 Profile | Perfil

```python
from iq_core.entities import Profile

# Perfil do usuário
profile = Profile(
    id=12345,
    name="João Silva",
    email="joao@exemplo.com",
    currency="USD",
    _balance_id=67890,
    is_activated=True,
    balances=[],  # Lista de contas
    nickname="trader123"
)

# Propriedades úteis
print(f"Saldo atual: ${profile.balance}")
print(f"ID da conta ativa: {profile.balance_id}")

# Acessar serviço de conta
account_service = profile.account
```

#### 📊 TradeResult | Resultado do Trade

```python
from iq_core.entities import TradeResult, TradeStatus, TradeResultType

# Status do trade
TradeStatus.OPEN      # Aberto
TradeStatus.CLOSED    # Fechado
TradeStatus.PENDING   # Pendente
TradeStatus.CANCELED  # Cancelado

# Resultado do trade
TradeResultType.WIN    # Vitória
TradeResultType.LOOSE  # Derrota
TradeResultType.DRAW   # Empate

# Exemplo de resultado
result = TradeResult(
    id=123,
    status=TradeStatus.CLOSED,
    result=TradeResultType.WIN,
    invest=Decimal("10.00"),
    profit=Decimal("8.00"),
    pnl=8.0,
    open=1.1234,
    close=1.1245,
    open_time=1234567890,
    close_time=1234567950,
    instrument_type=InstrumentType.BINARY
)

# Verificar se ganhou
if result.is_win:
    print("Trade vencedor!")

# Duração em segundos
duration = result.duration_seconds
```

---

## 🔧 Serviços | Services

### 🔐 AuthService | Serviço de Autenticação

```python
from iq_core import AuthService

async def autenticacao():
    auth = AuthService()
    
    # Login (com cache automático de token)
    ws, profile = await auth.login("email@exemplo.com", "senha")
    
    print(f"Usuário: {profile.name}")
    print(f"Saldo: ${profile.balance}")
    
    # Verificar se está autenticado
    if auth.is_authenticated:
        print("Autenticado com sucesso")
    
    # Token atual
    token = auth.token
    
    # Logout
    await auth.logout()

# Com context manager (recomendado)
async def auth_context():
    async with AuthService().context() as auth:
        ws, profile = await auth.login("email", "senha")
        # Trabalhar aqui
        # Logout automático
```

### 🏦 AccountService | Serviço de Conta

```python
from iq_core import AccountService
from iq_core.entities import AccountType

async def gerenciar_contas():
    # Assumindo ws e profile inicializados
    account_service = AccountService(ws, profile)
    
    # Carregar saldos
    await account_service.load_balances()
    
    # Obter conta ativa
    active = account_service.active_account()
    print(f"Conta ativa: {active.type} - ${active.amount}")
    
    # Listar todas as contas
    all_accounts = account_service.accounts()
    for account in all_accounts:
        print(f"{account.type}: ${account.amount}")
    
    # Obter conta específica por ID
    specific_account = account_service.accounts(balance_id=12345)
    
    # Trocar conta ativa
    await account_service.switch_active_account(AccountType.REAL)
```

### 🔍 InstrumentService | Serviço de Instrumentos

```python
from iq_core import InstrumentService

async def buscar_instrumentos():
    service = InstrumentService(ws)
    
    # Buscar todos os instrumentos
    all_instruments = await service.fetch()
    
    # Buscar instrumento específico
    eurusd = await service.fetch(filter_by="EURUSD")
    
    # Buscar por ID
    instrument_by_id = await service.fetch(filter_by=1)
    
    # Busca avançada
    forex_instruments = await service.fetch(
        groups=["forex"],
        types=["binary-option", "digital-option"],
        only_open=True,
        limit=10,
        offset=0,
        otc=False  # Excluir OTC
    )
    
    # Grupos disponíveis: forex, equity, commodity, index, crypto, etc.
    # Tipos disponíveis: binary-option, turbo-option, blitz-option, digital-option
    
    for instrument in forex_instruments:
        print(f"{instrument.name}: Lucro {instrument.trading.profit}")
        print(f"Aberto: {instrument.is_open}")
        print(f"Negociável: {instrument.is_tradable()}")
```

### 📊 CandleService | Serviço de Velas

```python
from iq_core import CandleService
from datetime import datetime, timedelta

async def analisar_velas():
    candle_service = CandleService(ws)
    
    # Obter velas históricas
    candles = await candle_service.get_candles(
        active_id=1,      # ID do ativo
        quantity=50,      # Quantidade de velas
        size=300,         # Tamanho em segundos (5 min)
        from_time=datetime.now() - timedelta(hours=4)
    )
    
    if candles:
        print(f"Obtidas {len(candles)} velas")
        last_candle = candles[-1]
        print(f"Última vela: {last_candle.close}")
    
    # Stream de velas em tempo real
    async for live_candle in candle_service.stream(active_id=1, size=60):
        print(f"Nova vela: O:{live_candle.open} C:{live_candle.close}")
        print(f"Volume: {live_candle.volume}")
        break  # Para o exemplo
```

### 💹 Serviços de Trading | Trading Services

#### 🎯 BinaryTradeService | Opções Binárias

```python
from iq_core import BinaryTradeService
from iq_core.entities import Signal, Direction, Duration, SignalType
from decimal import Decimal

async def trading_binario():
    binary_service = BinaryTradeService(ws, profile)
    
    # Criar sinal
    signal = Signal(
        instrument=eurusd,
        balance_id=profile.balance_id,
        direction=Direction.CALL,
        amount=Decimal("10.00"),
        expiration=Duration("5m"),
        type=SignalType.BINARY
    )
    
    # Abrir trade
    trade_id = await binary_service.open_trade(signal)
    print(f"Trade binário aberto: {trade_id}")
    
    # Verificar status
    is_closed, result = await binary_service.trade_status(trade_id)
    if is_closed and result:
        print(f"Resultado: {result.result}")
        print(f"Lucro: ${result.profit}")
```

#### 💎 DigitalTradeService | Opções Digitais

```python
from iq_core import DigitalTradeService

async def trading_digital():
    digital_service = DigitalTradeService(ws, profile)
    
    signal = Signal(
        instrument=btc_instrument,
        balance_id=profile.balance_id,
        direction=Direction.PUT,
        amount=Decimal("25.00"),
        expiration=Duration("15m"),
        type=SignalType.DIGITAL
    )
    
    try:
        trade_id = await digital_service.open_trade(signal)
        print(f"Trade digital aberto: {trade_id}")
        
        # Verificar resultado
        is_closed, result = await digital_service.trade_status(trade_id)
        
    except TradingError as e:
        print(f"Erro: {e}")
```

#### ⚡ BlitzTradeService | Opções Blitz

```python
from iq_core import BlitzTradeService

async def trading_blitz():
    blitz_service = BlitzTradeService(ws, profile)
    
    # Trade rápido de 30 segundos
    signal = Signal(
        instrument=gold_instrument,
        balance_id=profile.balance_id,
        direction=Direction.CALL,
        amount=Decimal("5.00"),
        expiration=Duration("30s"),
        type=SignalType.BLITZ
    )
    
    trade_id = await blitz_service.open_trade(signal)
    print(f"Trade Blitz aberto: {trade_id}")
```

#### 💱 ForexTradeService | Forex

```python
from iq_core import ForexTradeService

async def trading_forex():
    forex_service = ForexTradeService(ws)
    
    signal = Signal(
        instrument=eurusd,
        balance_id=profile.balance_id,
        direction=Direction.CALL,
        amount=Decimal("100.00"),
        expiration=Duration("1h"),
        type=SignalType.FOREX
    )
    
    # Abrir posição
    trade_id = await forex_service.open_trade(signal)
    
    # Fechar posição
    closed = await forex_service.close_trade(trade_id)
    
    # Status da posição
    status = await forex_service.trade_status(trade_id)
```

### 🎯 TradingManagerService | Gerenciador de Trading

```python
from iq_core import TradingManagerService, BinaryTradeService, DigitalTradeService

async def gerenciamento_avancado():
    # Configurar serviços
    services = {
        SignalType.BINARY: BinaryTradeService(ws, profile),
        SignalType.DIGITAL: DigitalTradeService(ws, profile),
    }
    
    # Criar gerenciador
    async with TradingManagerService(
        start_balance=1000.0,      # Saldo inicial
        stop_win_percent=20.0,     # Stop win 20%
        stop_loss_percent=10.0,    # Stop loss 10%
        services=services,
        max_open_trades=3          # Máx 3 trades simultâneos
    ) as manager:
        
        # Callback para trades finalizados
        async def on_trade_finished(result, mgr):
            print(f"Trade finalizado: {result.result}")
            print(f"Saldo: ${mgr.balance}")
            print(mgr.summary())
        
        manager.register(on_trade_finished)
        
        # Propriedades úteis
        print(f"Saldo inicial: ${manager.start_balance}")
        print(f"Saldo atual: ${manager.balance}")
        print(f"Lucro: ${manager.profit}")
        print(f"Stop win: ${manager.stop_win}")
        print(f"Stop loss: ${manager.stop_loss}")
        print(f"Total operações: {manager.total_operations}")
        print(f"Vitórias: {manager.total_wins}")
        print(f"Derrotas: {manager.total_losses}")
        print(f"Empates: {manager.total_draws}")
        print(f"% Ganho: {manager.gain_percent}")
        print(f"% Perda: {manager.loss_percent}")
        
        # Verificações
        if manager.can_trade():
            print("Pode operar")
        
        if manager.is_limit_reached():
            print("Limite atingido")
        
        if manager.instrument_limit_reached(instrument_id=1):
            print("Limite do instrumento atingido")
        
        # Executar sinal
        result = await manager.execute(signal)
        
        # Relatório
        print(manager.summary())
```

### 📊 TraderMoodService | Humor do Trader

```python
from iq_core import TraderMoodService

async def analisar_sentimento():
    mood_service = TraderMoodService(ws)
    
    # Monitorar humor para EUR/USD (ID=1)
    async for mood_value in mood_service.subscribe(instrument_id=1):
        print(f"Humor dos traders: {mood_value}%")
        
        # Estratégia baseada no sentimento
        if mood_value > 70:
            print("Traders muito otimistas - considerar PUT")
        elif mood_value < 30:
            print("Traders muito pessimistas - considerar CALL")
        else:
            print("Sentimento neutro")
        
        # Parar após primeira leitura (exemplo)
        break
```

### 💰 CotationService | Serviço de Cotação

```python
from iq_core import CotationService

async def obter_cotacao():
    cotation_service = CotationService(ws)
    
    # Gerar cotação para EUR/USD
    cotation = await cotation_service.generate(active_id=1, size=300)
    
    if cotation:
        print(f"Cotação gerada: {cotation}")
    else:
        print("Não foi possível obter cotação")
```

### 🔧 TokenManager | Gerenciador de Tokens

```python
from iq_core import TokenManager

# Criar gerenciador
token_manager = TokenManager(
    directory=".tokens",    # Diretório dos tokens
    keyfile=".token_key"   # Arquivo da chave
)

# Salvar token
token_manager.set_token("email@exemplo.com", "token_secreto")

# Obter token
token = token_manager.get_token("email@exemplo.com")

# Remover token
token_manager.remove_token("email@exemplo.com")

# Listar todos os tokens
all_tokens = token_manager.tokens
```

---

## 🌐 WebSocket Client

### 🔌 Cliente WebSocket Avançado

```python
from iq_core.websocket import WebSocketClient
from iq_core.entities import Message

async def websocket_avancado():
    ws = WebSocketClient()
    
    # Conectar
    await ws.connect("seu_token_ssid")
    
    # Enviar mensagem personalizada
    response = await ws.request({
        "name": "get-candles",
        "version": "2.0",
        "body": {
            "active_id": 1,
            "size": 300,
            "count": 10,
            "to": ws.current_server_time()
        }
    })
    
    # Subscrever eventos
    await ws.subscribe(
        name="candle-generated",
        version="2.0",
        params={"routingFilters": {"active_id": 1, "size": 300}}
    )
    
    # Callback para eventos
    @ws.handle("candle-generated")
    async def on_candle(data):
        print(f"Nova vela: {data}")
    
    # Aguardar evento com condição
    candle_data = await ws.wait_for(
        name="candle-generated",
        condition=lambda data: data.get("close", 0) > 1.1200,
        timeout=60.0
    )
    
    # Tempo do servidor
    server_time = ws.current_server_time()      # Milissegundos
    server_time_s = ws.current_server_time(ms=False)  # Segundos
    
    # Tempo local da conexão
    local_time = ws.local_time()
    
    # Calcular expiração
    expiration, index = ws.get_expiration(duration=5)  # 5 minutos
    
    # Cancelar subscrição
    await ws.unsubscribe(
        name="candle-generated",
        params={"routingFilters": {"active_id": 1, "size": 300}}
    )
    
    # Remover callback
    ws.off("candle-generated", on_candle)
    
    await ws.close()
```

### 📨 Entidade Message

```python
from iq_core.entities import Message, MessageType

# Criar mensagens
send_msg = Message.send(
    request_id=123,
    msg={"name": "get-profile", "version": "1.0", "body": {}}
)

subscribe_msg = Message.subscribe(
    sid=456,
    name="candle-generated",
    version="2.0",
    params={"routingFilters": {"active_id": 1}}
)

unsubscribe_msg = Message.unsubscribe(
    sid=456,
    name="candle-generated",
    version="2.0"
)

set_options_msg = Message.set_options(
    request_id=789,
    send_results=True
)

auth_msg = Message.authenticate(ssid="token_here")

# Converter para dicionário
msg_dict = send_msg.to_dict()

# Criar a partir de dicionário
msg_from_dict = Message.from_dict(msg_dict)

# Representação em string
print(str(send_msg))  # JSON formatado
```

---

## ⚠️ Exceções | Exceptions

### 🛡️ Hierarquia de Exceções

```python
from iq_core.exceptions import (
    IQOptionError,           # Exceção base
    AuthenticationError,     # Erro de autenticação
    ConnectionError,         # Erro de conexão
    NetworkUnavailableError, # Rede indisponível
    TradingError,           # Erro de trading
    ValidationError,        # Erro de validação
    InvalidTargetTime       # Tempo alvo inválido
)

async def tratamento_erros():
    try:
        auth = AuthService()
        ws, profile = await auth.login("email", "senha")
        
    except AuthenticationError as e:
        print(f"Falha na autenticação: {e}")
        
    except NetworkUnavailableError as e:
        print(f"Problema de rede: {e}")
        
    except TradingError as e:
        print(f"Erro no trading: {e}")
        
    except ValidationError as e:
        print(f"Dados inválidos: {e}")
        
    except InvalidTargetTime as e:
        print(f"Tempo inválido: {e}")
        
    except ConnectionError as e:
        print(f"Erro de conexão: {e}")
        
    except IQOptionError as e:
        print(f"Erro geral da IQ Option: {e}")
        
    except Exception as e:
        print(f"Erro inesperado: {e}")
```

---

## 📖 Referência da API | API Reference

### 🔧 Decoradores | Decorators

#### `@measure_time`
```python
from iq_core.anotations import measure_time

@measure_time
async def minha_funcao():
    # Função será cronometrada automaticamente
    pass
```

#### `@handle_network_errors`
```python
from iq_core.anotations import handle_network_errors

@handle_network_errors
async def operacao_rede():
    # Erros de rede serão tratados automaticamente
    pass
```

### 🏛️ Classes Principais | Core Classes

#### Duration
- `Duration(value)` - Criar duração (string ou número)
- `.minutes()` - Converter para minutos (int)
- `.seconds()` - Converter para segundos (float)
- `.ms()` - Converter para milissegundos (float)
- `.timestamp()` - Timestamp futuro (int)
- `.until(time)` - Duração até horário "HH:MM"
- `.add(value)` - Adicionar valor
- `.sub(value)` - Subtrair valor
- Operadores: `+`, `-`, `*`, `==`, `!=`, `<`, `<=`, `>`, `>=`

#### Signal
- `Signal(instrument, balance_id, direction, amount, expiration, type)`
- Validação automática de parâmetros
- Tipos: BINARY, DIGITAL, BLITZ, FOREX
- Direções: CALL, PUT

#### Instrument
- `.is_tradable()` - Verificar se pode ser negociado
- `.is_open` - Propriedade de status de abertura
- `.trading` - Informações de trading (TradingInfo)

### 🔧 API dos Serviços | Services API

#### AuthService
- `login(email, password)` - Autenticar usuário
- `logout()` - Desconectar
- `context()` - Context manager
- `.token` - Token atual
- `.is_authenticated` - Status de autenticação

#### InstrumentService
- `fetch(**filters)` - Buscar instrumentos
- Filtros disponíveis:
  - `filter_by`: ID ou símbolo específico
  - `limit`: Limitar resultados
  - `offset`: Paginação
  - `otc`: Incluir/excluir OTC
  - `groups`: Lista de grupos
  - `types`: Lista de tipos
  - `only_open`: Apenas abertos

#### CandleService
- `get_candles(active_id, quantity, size, from_time)` - Dados históricos
- `stream(active_id, size)` - Stream em tempo real

#### Trading Services
- `open_trade(signal)` - Abrir operação
- `trade_status(trade_id)` - Status da operação
- `close_trade(trade_id)` - Fechar operação (Forex)

#### TradingManagerService
- `execute(signal)` - Executar com gestão de risco
- `register(callback)` - Registrar callback
- `unregister(callback)` - Remover callback
- `can_trade()` - Verificar se pode operar
- `is_limit_reached()` - Verificar limites
- `instrument_limit_reached(id)` - Limite por instrumento
- `close()` - Fechar gerenciador
- Propriedades: `balance`, `profit`, `total_operations`, etc.

#### WebSocketClient
- `connect(ssid)` - Conectar
- `subscribe(name, version, params)` - Subscrever
- `unsubscribe(name, version, params)` - Cancelar subscrição
- `request(msg, name)` - Requisição
- `send(msg)` - Enviar mensagem
- `receive(name, request_id, timeout)` - Receber resposta
- `handle(name)` - Decorator para callbacks
- `on(name, callback)` - Registrar callback
- `off(name, callback)` - Remover callback
- `wait_for(name, condition, timeout)` - Aguardar evento
- `current_server_time(ms)` - Tempo do servidor
- `local_time()` - Tempo local da conexão
- `get_expiration(duration)` - Calcular expiração
- `close()` - Fechar conexão

---

## 🚀 Dicas de Performance | Performance Tips

### 🇧🇷 Otimizações

1. **Use Context Managers**: Sempre use `async with` para gerenciar recursos
2. **Reutilize Conexões**: Mantenha a conexão WebSocket ativa
3. **Async/Await**: Aproveite a concorrência com asyncio
4. **Cache de Tokens**: Tokens são automaticamente cacheados
5. **Gestão de Memória**: Limite histórico de dados em memória

### 🇺🇸 Optimizations

1. **Use Context Managers**: Always use `async with` to manage resources
2. **Reuse Connections**: Keep WebSocket connection alive
3. **Async/Await**: Leverage concurrency with asyncio
4. **Token Caching**: Tokens are automatically cached
5. **Memory Management**: Limit historical data in memory

---

## 🛡️ Segurança | Security

### 🇧🇷 Melhores Práticas

- ✅ Tokens são criptografados automaticamente
- ✅ Use variáveis de ambiente para credenciais
- ✅ Implemente rate limiting
- ✅ Monitore logs de erro
- ✅ Use HTTPS apenas

### 🇺🇸 Best Practices

- ✅ Tokens are automatically encrypted
- ✅ Use environment variables for credentials
- ✅ Implement rate limiting
- ✅ Monitor error logs
- ✅ Use HTTPS only

---

## 📝 License | Licença

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing | Contribuindo

### 🇧🇷 Como Contribuir

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

### 🇺🇸 How to Contribute

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📞 Support | Suporte

- 📧 Email: profissional.celiojunior@outlook.com
- 🐛 Issues: [GitHub Issues](https://github.com/itmanagersupport/iq-core/issues)
- 📖 Documentation: [GitHub Wiki](https://github.com/itmanagersupport/iq-core/wiki)

---

<div align="center">

**🇧🇷 Feito com ❤️ para a comunidade de trading**  
**🇺🇸 Made with ❤️ for the trading community**

⭐ **Se este projeto foi útil, considere dar uma estrela!**  
⭐ **If this project was helpful, consider giving it a star!**

</div>