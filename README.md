# Scrap Bazaar

A minimal web app for selling household scrap. Buyers see each item's quantity
and starting price and place an offer. The seller sees every offer, with the
buyer's contact details, and sells to the highest one. Written entirely in
Python with [Streamlit](https://streamlit.io) and SQLite.

## Run it

```bash
pip install -r requirements.txt
export SELLER_PASSWORD="choose-a-password"   # Windows: set SELLER_PASSWORD=...
streamlit run app.py
```

Open the link Streamlit prints. Log in from the sidebar with your password to
add items, see offers and contacts, mark items sold, or remove them. Buyers
never need an account, and buyers' contact details are only shown to you.

No phone number is stored in the code. Buyers enter their own phone or email
when they place an offer.

## Deploy for free (Streamlit Community Cloud)

1. Push this folder to a GitHub repository.
2. On https://share.streamlit.io choose the repository and `app.py`.
3. In Advanced settings, add a secret: `SELLER_PASSWORD = "choose-a-password"`.

Note: the free cloud resets its disk when the app restarts, so offers can be
lost. For permanent storage, run the app on a host with a persistent disk
(set `SCRAP_DB` to a file on that disk) or swap SQLite for a hosted database.

## Files

- `app.py`: the whole app
- `requirements.txt`: Python dependency
- `.streamlit/config.toml`: colours and font for the minimal look
- `.gitignore`: keeps the database and secrets out of Git
- `LICENSE`: MIT (replace `<your name>`)
