# Multi-User Telegram Announcement Bot — Railway Deploy Guide

## Files (sab already ready hain)
- `announcement_bot.py` — main bot code
- `requirements.txt` — dependencies
- `Procfile` — Railway ko batata hai kaise run karna hai
- `runtime.txt` — Python version
- `.gitignore` — extra files push hone se rokta hai

---

## STEP 1: Bot Token lo
1. Telegram me [@BotFather](https://t.me/BotFather) open karo
2. `/newbot` bhejo, naam aur username do
3. Jo token milega (jaise `123456:ABC-xyz...`) usko copy kar lo

---

## STEP 2: Code GitHub pe daalo
1. [github.com](https://github.com) pe naya **repository** banao (private ya public, dono chalega)
2. Ye saari files (`announcement_bot.py`, `requirements.txt`, `Procfile`, `runtime.txt`, `.gitignore`) us repo me upload kar do
   - GitHub website se hi "Add file → Upload files" se drag-drop kar sakte ho, terminal ki zaroorat nahi

---

## STEP 3: Railway pe deploy karo
1. [railway.app](https://railway.app) pe jaake login karo (GitHub se login karna easy hai)
2. **New Project → Deploy from GitHub repo** choose karo
3. Apni bot wali repository select karo
4. Railway apne aap `requirements.txt` dekh ke sab install kar lega aur `Procfile` se bot start kar dega

---

## STEP 4: Environment Variable set karo
1. Railway project ke andar **Variables** tab kholo
2. Naya variable add karo:
   - Key: `BOT_TOKEN`
   - Value: (STEP 1 wala token paste karo)
3. Save karte hi Railway bot ko restart kar dega

---

## STEP 5: (Zaroori) Data permanent rakhne ke liye Volume lagao
Railway ka filesystem restart pe reset ho sakta hai, isliye database ko safe rakhne ke liye:
1. Railway project me **"+ New" → "Volume"** add karo
2. Mount path do: `/data`
3. Ek aur environment variable add karo:
   - Key: `DB_PATH`
   - Value: `/data/bot_data.db`
4. Redeploy karo

Ab tumhara data (users + unke groups) kabhi delete nahi hoga.

---

## STEP 6: Bot use karna shuru karo
1. Apne Telegram group me bot ko **Admin** bana ke add karo
2. Group ke andar `/addgroup` bhejo — group tumhare account se link ho jayega
3. Bot ki DM me `/mygroups` bhej ke check karo
4. Bot ki DM me `/announce` bhejo → message do → groups select karo (ya "Select All") → **Send Now**

---

## Deploy logs check karna ho
Railway project ke **"Deployments"** tab me jaake latest deployment kholo, wahan live logs dikhenge — agar bot start ho gaya to "Bot chalu ho gaya..." line dikhegi.

## Common Issues
| Problem | Fix |
|---|---|
| Bot reply nahi kar raha | `BOT_TOKEN` variable check karo, sahi copy hua ya nahi |
| `/addgroup` pe error | Bot ko group me pehle Admin banao |
| Restart pe groups list gayab | STEP 5 wala Volume + `DB_PATH` setup karo |
