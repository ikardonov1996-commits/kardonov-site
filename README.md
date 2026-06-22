# KARDONOV — Human × AI Studio

Одностраничный сайт-лендинг. Чистый HTML/CSS/JS + минимальный Node-сервер для отдачи статики.

## Структура

```
kardonov-site/
├── public/
│   ├── index.html          # сам сайт
│   └── kardonov-hero.webp  # изображение героя (мозг)
├── server.js               # zero-dependency статический сервер (слушает process.env.PORT)
├── package.json            # start: node server.js
├── railway.json            # конфиг Railway (Nixpacks)
├── .gitignore
├── DEPLOY.md               # пошаговая инструкция (в т.ч. для Claude Code)
└── README.md
```

## Локальный запуск

```bash
npm start
# открыть http://localhost:3000
```

Зависимостей нет — `server.js` использует только встроенные модули Node (`http`, `fs`, `path`). Node 18+.

## Деплой

Подробно — в `DEPLOY.md`: GitHub + Railway, через Claude Code или вручную.

## Что осталось сделать к продакшену (необязательно)

- `og:image` для красивых превью в мессенджерах/соцсетях (сейчас OG-теги есть, картинки превью нет).
- `favicon.ico` / `favicon.svg`.
- `rel="canonical"` на финальный домен.
- Подключить реальную отправку формы (сейчас форма ничего не отправляет — нужен бэкенд: Telegram-бот или email).
