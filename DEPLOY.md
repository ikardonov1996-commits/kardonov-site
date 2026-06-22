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

## Свой домен (опционально)

Railway → сервис → **Settings → Networking → Custom Domain** → добавь домен и пропиши CNAME у регистратора по подсказке Railway.

---

## Частые проблемы

- **Белая страница / 404**: проверь, что `index.html` и `kardonov-hero.webp` лежат в `public/`.
- **Картинка не грузится**: путь в `index.html` должен быть `src="kardonov-hero.webp"` (относительный), файл — в `public/`.
- **Приложение падает на старте**: убедись, что не захардкожен порт — сервер обязан слушать `process.env.PORT`.
- **`gh`/`railway` не найдены**: установи CLI (ссылки выше) и авторизуйся.
