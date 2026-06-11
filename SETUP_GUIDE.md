# 🎤 Toastmasters Pune South East — Setup Guide (Supabase Edition)
## Zero Google Cloud. No JSON keys. Just sign up and go.

---

## What You Need
- A browser (no software to install yet)
- A GitHub account (free) — github.com
- About 20 minutes

---

## STEP 1 — Create Your Supabase Project (5 min)

1. Go to **supabase.com** → click **Start your project** → sign in with your Gmail.

2. Click **New project** → fill in:
   - **Name:** `toastmasters-pse`
   - **Database Password:** choose something strong (save it somewhere safe)
   - **Region:** pick `Southeast Asia (Singapore)` — closest to Pune
   - Click **Create new project** — wait ~1 minute for it to spin up.

3. Once ready, go to **Project Settings** (gear icon, bottom left) → **API**.

4. Copy and save these two values — you'll need them shortly:
   - **Project URL** — looks like `https://abcdefghij.supabase.co`
   - **anon / public key** — a long JWT string starting with `eyJ...`

---

## STEP 2 — Create the Database Tables (2 min)

1. In your Supabase project, click **SQL Editor** (left sidebar) → **New query**.

2. Open the file `supabase_setup.sql` from this project folder.

3. Copy the **entire contents** and paste it into the SQL Editor.

4. Click **Run** (or press Ctrl+Enter).

   You should see: *"Success. No rows returned."*

5. Click **Table Editor** in the left sidebar — you should see 7 tables:
   `members`, `attendance`, `guests`, `today_speakers`, `feedback`, `votes`, `meeting_config`

---

## STEP 3 — Add Your Club Members (5 min)

1. In Supabase → **Table Editor** → click the **members** table.

2. Click **Insert row** for each member. Fill in:

   | Column    | Example            | Notes                          |
   |-----------|--------------------|--------------------------------|
   | name      | Priya Sharma       | Full name                      |
   | email     | priya@gmail.com    | Must match what they'll type   |
   | phone     | 9876543210         | No spaces or dashes            |
   | join_date | 2024-01-15         | YYYY-MM-DD format              |
   | active    | true               | Toggle on                      |

   > **Important:** Phone numbers must be stored without spaces, dashes, or +91.  
   > Members can type either their email OR phone to check in — both work.

3. Add all active club members. You can always add more later.

---

## STEP 4 — Configure the App Secrets

1. In the project folder, open `.streamlit/secrets.toml.template`.

2. **Copy** that file and **rename the copy** to `.streamlit/secrets.toml`  
   (remove the `.template` part).

3. Open `secrets.toml` and fill in:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "eyJhbGc...your-full-anon-key..."
   ADMIN_PASSWORD = "PickAStrongPassword!"
   ```
   Use the URL and anon key you copied in Step 1.

---

## STEP 5 — Test Locally (Optional but Recommended)

```bash
# Install Python 3.10+ if you haven't already
pip install -r requirements.txt
streamlit run app.py
```

- Visit `http://localhost:8501` → you should see the welcome screen
- Try checking in with a member's email or phone
- Visit `http://localhost:8501/?admin=1` → admin panel

---

## STEP 6 — Push to GitHub

1. Create a new **private** repository on github.com  
   (private keeps your secrets template away from public view)

2. In your project folder, run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/toastmasters-pse.git
   git push -u origin main
   ```

   > The `.gitignore` already excludes `secrets.toml` — it will NOT be pushed.

---

## STEP 7 — Deploy on Streamlit Cloud (Free)

1. Go to **share.streamlit.io** → sign in with GitHub → **New app**.

2. Select:
   - **Repository:** your repo
   - **Branch:** `main`
   - **Main file path:** `app.py`

3. Click **Advanced settings** → click the **Secrets** tab.

4. Paste the contents of your `secrets.toml` file here:
   ```toml
   SUPABASE_URL = "https://..."
   SUPABASE_KEY = "eyJ..."
   ADMIN_PASSWORD = "YourPassword"
   ```

5. Click **Save** → then **Deploy!**

6. Wait ~2 minutes → you'll get a live URL like:
   `https://toastmasters-pse.streamlit.app`

---

## STEP 8 — Generate Your QR Code

1. Go to **qr-code-generator.com**
2. Enter your Streamlit app URL
3. Download → print on A4 or A5 → place at the entrance!

For the admin panel, your URL is: `https://your-app.streamlit.app/?admin=1`  
Bookmark this on your phone — you won't want to type it each time.

---

## Using the App on Meeting Day

### Before the Meeting (SAA — you)
1. Open `your-url/?admin=1` on your phone
2. Enter admin password
3. Go to **Today's Roles** tab
4. Enter all speakers, evaluators, role players → **Save Speakers**
5. Confirm **Voting is CLOSED** (default)

### During the Meeting
- Members & guests scan the QR code at the entrance
- Members: instant check-in with email or phone
- Guests: fill in a quick 3-field form
- Everyone can submit feedback for each speaker throughout the meeting

### End of Meeting (SAA)
1. Admin panel → **Voting Control** tab
2. Click **🔓 Open Voting**
3. Announce to members: "Voting is now open — use your phones!"
4. Members see the voting section unlock instantly
5. After a few minutes → click **🔒 Close Voting**
6. See the live tally in the same tab

---

## Viewing Your Data

All data lives in Supabase → **Table Editor**. You can:
- Browse any table like a spreadsheet
- Filter, sort, search
- Click **Export** (CSV) on any table to download to Excel

| Table            | What's in it                          |
|------------------|---------------------------------------|
| `members`        | Your club roster                      |
| `attendance`     | Who attended, with timestamps         |
| `guests`         | New visitor leads + referral source   |
| `today_speakers` | Today's meeting roles (reset each day)|
| `feedback`       | All speaker feedback                  |
| `votes`          | Every vote cast with timestamps       |
| `meeting_config` | Voting open/closed switch             |

---

## Troubleshooting

**"Could not load meeting data"**  
→ Check your SUPABASE_URL and SUPABASE_KEY in secrets. Make sure there are no extra spaces.

**Member not being recognized**  
→ Check their row in the `members` table. Phone must have no spaces/dashes. Email must match exactly (case-insensitive).

**SQL Editor gave an error on setup**  
→ Run each `create table` block separately if one fails.

**Streamlit Cloud showing old version**  
→ Go to your app dashboard → click the three dots → **Reboot app**.

---

## File Structure

```
tm_supabase/
├── app.py                          ← Main app, Supabase client, all DB functions
├── requirements.txt                ← supabase, streamlit, pandas only
├── supabase_setup.sql              ← Run once in Supabase SQL Editor
├── pages/
│   ├── _login.py                   ← QR landing + guest form
│   ├── _dashboard.py               ← Feedback & voting dashboard
│   └── _admin.py                   ← SAA admin panel
└── .streamlit/
    ├── config.toml                 ← Maroon + navy theme
    └── secrets.toml.template       ← Copy → rename → fill in
```

---

*Built for Toastmasters Pune South East — Where Leaders Are Made* 🎤
