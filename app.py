"""Scrap Bazaar: sell household scrap to the highest offer. Pure Python (Streamlit + SQLite)."""
import hmac
import os
import re
import sqlite3
import time

import streamlit as st

DB_PATH = os.environ.get("SCRAP_DB", "scrap.db")
SEED = [
    ("📰", "Old newspapers and magazines", 40, "kg", 200),
    ("🔌", "Copper wire and cables", 6, "kg", 2500),
    ("🥘", "Aluminium utensils", 8, "kg", 700),
    ("🌀", "Broken fans and mixers", 5, "pcs", 600),
    ("📦", "Cardboard boxes", 25, "kg", 250),
    ("💻", "Old laptops and phones", 4, "pcs", 1500),
]

st.set_page_config(page_title="Scrap Bazaar", page_icon="♻️", layout="centered")


# ---------- database ----------
def run(sql, *args):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(sql, args)


def query(sql, *args):
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        return con.execute(sql, args).fetchall()


def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.executescript(
            """
            create table if not exists items(
                id integer primary key autoincrement, emoji text, name text,
                qty real, unit text, min_price integer, sold_to text, sold_price integer);
            create table if not exists offers(
                id integer primary key autoincrement, item_id integer,
                name text, contact text, price integer, ts integer);
            """
        )
        if con.execute("select count(*) from items").fetchone()[0] == 0:
            con.executemany(
                "insert into items(emoji, name, qty, unit, min_price) values (?,?,?,?,?)", SEED
            )


# ---------- helpers ----------
def inr(n):
    s = str(int(n))
    if len(s) > 3:
        s = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", s[:-3]) + "," + s[-3:]
    return "₹" + s


def seller_password():
    pw = os.environ.get("SELLER_PASSWORD")
    if pw:
        return pw
    try:
        return st.secrets.get("SELLER_PASSWORD")
    except Exception:
        return None


def qty_text(it):
    q = it["qty"]
    return f"{q:g} {it['unit']}"


# ---------- seller login (sidebar) ----------
with st.sidebar:
    st.subheader("Seller")
    secret = seller_password()
    if st.session_state.get("seller"):
        st.write("You’re logged in as the seller.")
        if st.button("Log out"):
            st.session_state["seller"] = False
            st.rerun()
    elif not secret:
        st.caption("Set a SELLER_PASSWORD to turn on seller tools.")
    else:
        pw = st.text_input("Password", type="password")
        if st.button("Log in"):
            if hmac.compare_digest(pw.encode(), secret.encode()):
                st.session_state["seller"] = True
                st.rerun()
            else:
                st.error("Wrong password.")

seller = st.session_state.get("seller", False)
init_db()

# ---------- header ----------
st.title("Turn what’s lying around into cash.")
st.write("Pick an item, check the quantity, and send your best offer. The highest offer wins.")
if msg := st.session_state.pop("flash", None):
    st.success(msg)

# ---------- seller: add item ----------
if seller:
    with st.expander("Add an item"):
        with st.form("add_item", clear_on_submit=True):
            c1, c2 = st.columns([1, 3])
            emoji = c1.text_input("Emoji", value="📦")
            name = c2.text_input("Item name")
            c3, c4, c5 = st.columns(3)
            qty = c3.number_input("Quantity", min_value=0.0, step=1.0, value=1.0)
            unit = c4.text_input("Unit", value="kg")
            min_price = c5.number_input("Starting price (₹)", min_value=0, step=50, value=100)
            if st.form_submit_button("Add to the list"):
                if not name.strip() or qty <= 0 or min_price <= 0:
                    st.error("Add a name, a quantity and a starting price above zero.")
                else:
                    run(
                        "insert into items(emoji, name, qty, unit, min_price) values (?,?,?,?,?)",
                        emoji.strip() or "📦", name.strip(), qty, unit.strip() or "pcs", int(min_price),
                    )
                    st.session_state["flash"] = "Item added."
                    st.rerun()

# ---------- items ----------
st.divider()
items = query("select * from items order by (sold_to is not null), id desc")
if not items:
    st.info("Nothing is listed right now. Check back soon!")

for it in items:
    offers = query("select * from offers where item_id=? order by price desc, ts", it["id"])
    best = offers[0] if offers else None
    need = best["price"] + 1 if best else it["min_price"]

    with st.container(border=True):
        st.subheader(f"{it['emoji']}  {it['name']}")
        st.caption(f"Quantity: {qty_text(it)}  ·  Starts at {inr(it['min_price'])}")

        if it["sold_to"]:
            st.success(f"Sold to {it['sold_to']} for {inr(it['sold_price'])}")
        else:
            if best:
                st.info(
                    f"Best offer so far: **{inr(best['price'])}** from {best['name']} "
                    f"({len(offers)} offer{'s' if len(offers) > 1 else ''})"
                )
            else:
                st.info("No offers yet. Be the first to make one!")

            with st.form(f"offer_{it['id']}", clear_on_submit=True, border=False):
                c1, c2 = st.columns(2)
                buyer = c1.text_input("Your name")
                price = c2.number_input(
                    "Your offer for the whole lot (₹)", min_value=0, step=50, value=int(need),
                    key=f"price_{it['id']}_{need}",
                )
                contact = st.text_input("Your phone or email (only the seller sees this)")
                if st.form_submit_button("Place my offer"):
                    if not buyer.strip():
                        st.error("Enter your name so the seller knows who you are.")
                    elif not contact.strip():
                        st.error("Enter a phone number or email so the seller can reach you.")
                    elif price < need:
                        st.error(f"Your offer must be at least {inr(need)} to beat the best offer.")
                    else:
                        run(
                            "insert into offers(item_id, name, contact, price, ts) values (?,?,?,?,?)",
                            it["id"], buyer.strip(), contact.strip(), int(price), int(time.time()),
                        )
                        st.session_state["flash"] = f"Offer placed: {inr(price)}"
                        st.rerun()

        if seller:
            with st.expander(f"Seller view: {len(offers)} offer(s)"):
                if offers:
                    st.dataframe(
                        [{"Name": o["name"], "Contact": o["contact"], "Offer": inr(o["price"])} for o in offers],
                        hide_index=True, use_container_width=True,
                    )
                if best and not it["sold_to"]:
                    if st.button("Sell to best offer", key=f"sell_{it['id']}", type="primary"):
                        run("update items set sold_to=?, sold_price=? where id=?",
                            best["name"], best["price"], it["id"])
                        st.session_state["flash"] = f"Sold to {best['name']}."
                        st.rerun()
                with st.popover("Remove item"):
                    st.write("Remove this item and all its offers?")
                    if st.button("Yes, remove", key=f"del_{it['id']}"):
                        run("delete from offers where item_id=?", it["id"])
                        run("delete from items where id=?", it["id"])
                        st.rerun()

st.caption("Offers are made directly between you and the seller.")
