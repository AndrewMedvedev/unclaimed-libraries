# Unclaimed Libraries

[![Python Version](https://img.shields.io/badge/python-≥3.13-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CLI](https://img.shields.io/badge/CLI-unclib-orange)]()

**Unclaimed Libraries** – это CLI‑инструмент для поиска неиспользуемых зависимостей в Python‑проектах.
Он анализирует pyproject.toml, просматривает все импорты в коде, отфильтровывает стандартную библиотеку и локальные модули, а также обращается к PyPI, чтобы пропустить пакеты, предназначенные только для разработки (линтеры, тестовые фреймворки, CLI‑утилиты и т.д.).

## ✨ Возможности

- ✅ **Точное обнаружение** – обрабатывает `import`, `from ... import`, динамические импорты (`importlib.import_module`, `__import__`).

- 🧠 **Умная фильтрация** – автоматически игнорирует:
    - модули стандартной библиотеки Python
    - локальные модули/пакеты (включая namespace packages)
    - пакеты для разработки (линтеры, тесты, статические анализаторы, CLI‑помощники) – используя классификаторы PyPI.

## 📦 Установка

```bash
pip install unclaimed-libraries
```

Or using uv:

```bash
uv add unclaimed-libraries
```

## 🚀 Использование


```bash
# Анализ текущей папки
unclib

# Анализ конкретного проекта
unclib /path/to/myproject

# Исключить дополнительные каталоги
unclib . --exclude legacy scripts
```


## 🙋 Как внести вклад

Приветствуются issues и pull request’ы!
Пожалуйста, сначала создайте issue для обсуждения значительных изменений.


**Распространяется под лицензией MIT. Подробности в файле LICENSE.**
