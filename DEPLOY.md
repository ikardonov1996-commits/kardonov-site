# DEPLOY — инструкция (для Claude Code или вручную)

Цель: выложить сайт на **GitHub** и задеплоить на **Railway** так, чтобы он открывался по публичному URL.

---

## Как использовать с Claude Code

1. Распакуй этот пак в пустую папку.
2. Открой папку в терминале и запусти `claude` (Claude Code).
3. Вставь Claude Code такой запрос:

> Я хочу выложить этот статический сайт на GitHub и задеплоить на Railway.
> Следуй инструкции из файла DEPLOY.md по шагам. Перед `gh` и `railway` проверь,
> что CLI установлены и я авторизован; если нет — подскажи команды. Имя репозитория:
> `kardonov-site` (public). После деплоя сгенерируй публичный домен Railway и дай мне ссылку.

Claude Code выполнит шаги ниже сам. Ниже — те же команды, если хочешь вручную.

---

## Предварительно (один раз)

- **Node 18+**: `node -v`
- **Git**: `git --version`
- **GitHub CLI** `gh`: установка — https://cli.github.com . Логин: `gh auth login`
- **Railway CLI**: `npm i -g @railway/cli` . Логин: `railway login`

---

## Шаг 1. Git + GitHub

```bash
# в корне распакованной папки
git init
git add .
git commit -m "KARDONOV site: initial"

# создать репозиторий на GitHub и запушить (нужен залогиненный gh)
gh repo create kardonov-site --public --source=. --remote=origin --push
```

Если `gh` нет — создай пустой репозиторий на github.com вручную и:

```bash
git branch -M main
git remote add origin https://github.com/<твой-логин>/kardonov-site.git
git push -u origin main
```

## Шаг 2. Деплой на Railway

### Вариант A — через CLI (быстрее)

```bash
railway login          # откроет браузер для авторизации
railway init           # создать новый проект (выбери имя, напр. kardonov-site)
railway up             # собрать и задеплоить текущую папку
railway domain         # сгенерировать публичный домен → вернёт ссылку вида *.up.railway.app
```

Готово — открывай ссылку из `railway domain`.

### Вариант B — через дашборд (из GitHub-репозитория)

1. Зайди на https://railway.app → **New Project** → **Deploy from GitHub repo**.
2. Выбери репозиторий `kardonov-site`.
3. Railway сам определит Node, выполнит `npm install` (зависимостей нет) и `npm start`.
4. В настройках сервиса → **Settings → Networking → Generate Domain** — получишь публичный URL.

---

## Как Railway это запускает

- Railway (Nixpacks) видит `package.json`, ставит Node, запускает `npm start` → `node server.js`.
- `server.js` слушает `process.env.PORT` (Railway подставляет порт сам) и отдаёт файлы из `public/`.
- Конфиг продублирован в `railway.json` (`startCommand: node server.js`).

## Обновление сайта потом

```bash
git add .
git commit -m "update"
git push
```

- Если Railway подключён к GitHub-репозиторию (Вариант B) — задеплоит автоматически на каждый push.
- Если деплоил через `railway up` (Вариант A) — повтори `railway up` после пуша.

## Форма → Telegram (отправка заявок)

Форма на сайте отправляет заявки в Telegram через серверный эндпоинт `POST /api/lead`
(в `server.js`). Токен бота хранится **только на сервере** в переменных окружения —
в клиентский код он не попадает.

### 1. Создать бота и узнать токен

1. В Telegram напиши **@BotFather** → `/newbot` → задай имя и username.
2. BotFather пришлёт **токен** вида `123456789:AAE...` — это `TELEGRAM_BOT_TOKEN`.

### 2. Узнать chat_id (куда слать заявки)

1. Открой своего нового бота и нажми **Start** (отправь ему любое сообщение).
2. Узнай свой id одним из способов:
   - напиши боту **@userinfobot** — он пришлёт твой `id` (это и есть `TELEGRAM_CHAT_ID`); **или**
   - открой в браузере `https://api.telegram.org/bot<ТОКЕН>/getUpdates` и найди
     `"chat":{"id":...}` — это число (для лички — положительное, для группы — со знаком `-`).
3. Чтобы слать в **группу**: добавь бота в группу, отправь там сообщение и возьми
   отрицательный `chat.id` из `getUpdates`.

### 3. Задать переменные в Railway

Railway → твой сервис → вкладка **Variables** → добавь:

```
TELEGRAM_BOT_TOKEN = 123456789:AAE...
TELEGRAM_CHAT_ID   = 987654321
```

Сохрани — Railway передеплоит сервис сам. Готово: заявки с формы будут приходить в Telegram.

### Проверка

- Заполни форму на сайте (телефон **или** ник) и отправь — должно прийти сообщение в Telegram.
- Локально:
  ```bash
  TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... npm start
  curl -X POST http://localhost:3000/api/lead \
    -H 'Content-Type: application/json' \
    -d '{"phone":"+79001234567","method":"Telegram","comment":"тест"}'
  ```
- Если переменные не заданы — эндпоинт вернёт `503 not_configured`, а в логах будет предупреждение
  (сама заявка при этом логируется в консоль, чтобы не потерялась).

---

## Свой домен (опционально)

Railway → сервис → **Settings → Networking → Custom Domain** → добавь домен и пропиши CNAME у регистратора по подсказке Railway.

---

## Частые проблемы

- **Белая страница / 404**: проверь, что `index.html` и `kardonov-hero.webp` лежат в `public/`.
- **Картинка не грузится**: путь в `index.html` должен быть `src="kardonov-hero.webp"` (относительный), файл — в `public/`.
- **Приложение падает на старте**: убедись, что не захардкожен порт — сервер обязан слушать `process.env.PORT`.
- **`gh`/`railway` не найдены**: установи CLI (ссылки выше) и авторизуйся.
