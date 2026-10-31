#!/usr/bin/env python3
"""
Генератор тестовых данных для базы delivery_service.

Что делает:
  1. Создаёт с помощью numpy и pandas пользователей, магазины, товары, заказы,
     платежи, доставки и историю статусов.
  2. Либо загружает всё в MySQL (по умолчанию), либо сохраняет в CSV (--csv-only).

Примеры запуска:
  python generate_data.py --csv-only
  python generate_data.py --url "mysql+pymysql://root:пароль@localhost:3306/delivery_service" --truncate

Зависимости:
  pip install numpy pandas sqlalchemy pymysql
"""
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Настройки по умолчанию
# ----------------------------------------------------------------------------
N_CUSTOMERS = 800
N_COURIERS = 40
N_STORES = 15
PRODUCTS_PER_STORE = 20
N_ORDERS = 20000
DAYS = 180

# Итоговые статусы заказов и их доли
FINAL_STATUSES = ["delivered", "cancelled", "payment_failed", "rejected_by_store", "delivery_failed"]
FINAL_PROBS = [0.84, 0.07, 0.025, 0.035, 0.03]

FIRST_NAMES = ["Иван", "Пётр", "Алексей", "Дмитрий", "Сергей", "Андрей", "Максим", "Никита",
               "Анна", "Мария", "Елена", "Ольга", "Наталья", "Екатерина", "Дарья", "Ирина"]
LAST_NAMES = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев",
              "Соколов", "Михайлов", "Новиков", "Фёдоров", "Морозов", "Волков", "Алексеев"]
STREETS = ["Невский проспект", "Лиговский проспект", "ул. Савушкина", "Московский проспект",
           "ул. Рубинштейна", "Большой проспект", "проспект Просвещения", "ул. Типанова"]
PRODUCT_CATALOG = ["Хлеб", "Молоко", "Кефир", "Сыр", "Масло сливочное", "Яйца", "Курица охлаждённая",
                   "Рис", "Гречка", "Макароны", "Яблоки", "Бананы", "Помидоры", "Огурцы", "Картофель",
                   "Сок апельсиновый", "Вода минеральная", "Чай чёрный", "Кофе молотый", "Шоколад",
                   "Печенье", "Йогурт", "Творог", "Колбаса", "Пельмени", "Пицца замороженная",
                   "Мороженое", "Сметана", "Лук", "Морковь"]
PROMOS = [("WELCOME10", 10), ("LUNCH5", 5), ("FRIDAY15", 15), ("BIG20", 20), ("SPRING25", 25)]
PAYMENT_METHODS = ["card", "sbp", "apple_pay"]
VEHICLES = ["bike", "scooter", "foot", "car"]


# ----------------------------------------------------------------------------
# Справочники
# ----------------------------------------------------------------------------
def make_users(rng, n_customers, n_couriers, n_stores, end):
    """Пользователи: админ, сотрудники магазинов, курьеры, клиенты. Возвращает DataFrame и словарь id по ролям."""
    rows = []
    uid = 0

    def add(role, email=True):
        nonlocal uid
        uid += 1
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        created = end - timedelta(days=int(rng.integers(DAYS + 5, DAYS + 120)))
        rows.append({
            "id": uid,
            "role": role,
            "name": name,
            "phone": f"+7911{uid:07d}",
            "email": f"user{uid}@example.com" if email else None,
            "created_at": created,
        })
        return uid

    admin_id = add("admin")
    store_user_ids = [add("store") for _ in range(n_stores)]
    courier_user_ids = [add("courier", email=False) for _ in range(n_couriers)]
    customer_ids = [add("customer") for _ in range(n_customers)]

    # клиенты регистрируются в течение периода, поэтому даты у них разные
    users = pd.DataFrame(rows)
    mask = users["role"] == "customer"
    users.loc[mask, "created_at"] = [
        end - timedelta(days=int(rng.integers(0, DAYS + 60))) for _ in range(mask.sum())
    ]
    return users, admin_id, store_user_ids, courier_user_ids, customer_ids


def make_addresses(rng, customer_ids):
    rows = []
    aid = 0
    for uid in customer_ids:
        for _ in range(int(rng.choice([1, 2], p=[0.7, 0.3]))):
            aid += 1
            rows.append({
                "id": aid,
                "user_id": uid,
                "city": "Санкт-Петербург",
                "street": str(rng.choice(STREETS)),
                "house": str(int(rng.integers(1, 120))),
                "flat": str(int(rng.integers(1, 200))) if rng.random() < 0.9 else None,
                "lat": round(59.85 + rng.random() * 0.2, 6),
                "lon": round(30.15 + rng.random() * 0.3, 6),
            })
    return pd.DataFrame(rows)


def make_stores(rng, n_stores):
    rows = []
    for i in range(1, n_stores + 1):
        rows.append({
            "id": i,
            "name": f"Магазин «Продукты у дома №{i}»",
            "address": f"{rng.choice(STREETS)}, {int(rng.integers(1, 120))}",
            "work_hours": "09:00-22:00" if i % 3 else "08:00-23:00",
            "is_active": i != n_stores,  # один магазин закрыт, для разнообразия
        })
    return pd.DataFrame(rows)


def make_products(rng, n_stores, per_store):
    rows = []
    pid = 0
    for store_id in range(1, n_stores + 1):
        names = rng.choice(PRODUCT_CATALOG, size=per_store, replace=False)
        for name in names:
            pid += 1
            price = float(np.clip(rng.lognormal(mean=5.3, sigma=0.6), 40, 2500))
            rows.append({
                "id": pid,
                "store_id": store_id,
                "name": str(name),
                "price": round(price, 2),
                "is_available": bool(rng.random() > 0.05),
            })
    return pd.DataFrame(rows)


def make_promos():
    rows = []
    for i, (code, pct) in enumerate(PROMOS, start=1):
        rows.append({
            "id": i,
            "code": code,
            "discount_percent": pct,
            "valid_to": None,
            "usage_limit": None if i % 2 else 5000,
        })
    return pd.DataFrame(rows)


def make_couriers(rng, courier_user_ids):
    rows = []
    for i, uid in enumerate(courier_user_ids, start=1):
        rows.append({
            "id": i,
            "user_id": uid,
            "status": str(rng.choice(["free", "busy", "offline"], p=[0.4, 0.3, 0.3])),
            "vehicle_type": str(rng.choice(VEHICLES, p=[0.4, 0.3, 0.2, 0.1])),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Время создания заказов
# ----------------------------------------------------------------------------
def make_created_at(rng, n_orders, days, end):
    """Заказы растут к концу периода, в выходные их больше, пики в обед и вечером."""
    day_idx = np.arange(days)                       # 0 — самый давний день
    dates = [end - timedelta(days=int(days - 1 - d)) for d in day_idx]
    trend = 1 + 0.6 * day_idx / days                # рост спроса примерно на 60%
    weekend = np.array([1.3 if d.weekday() >= 5 else 1.0 for d in dates])
    day_w = trend * weekend
    day_w = day_w / day_w.sum()

    hours = np.arange(24)
    hour_w = (0.05
              + 1.0 * np.exp(-((hours - 13) ** 2) / (2 * 1.5 ** 2))   # обеденный пик
              + 1.4 * np.exp(-((hours - 19.5) ** 2) / (2 * 2.0 ** 2)))  # вечерний пик
    hour_w[:7] = 0.02
    hour_w = hour_w / hour_w.sum()

    chosen_days = rng.choice(day_idx, size=n_orders, p=day_w)
    chosen_hours = rng.choice(hours, size=n_orders, p=hour_w)
    result = []
    for d, h in zip(chosen_days, chosen_hours):
        base = dates[d].replace(hour=int(h), minute=0, second=0, microsecond=0)
        result.append(base + timedelta(minutes=int(rng.integers(0, 60)), seconds=int(rng.integers(0, 60))))
    result.sort()
    return result


# ----------------------------------------------------------------------------
# Основная симуляция заказов
# ----------------------------------------------------------------------------
def simulate_orders(rng, args, users_info, addresses, stores, products, promos, couriers):
    admin_id, store_user_ids, courier_user_ids, customer_ids = users_info
    end = args.end

    # вес активности клиентов и магазинов: небольшая доля даёт большую часть заказов
    cust_w = rng.gamma(0.6, size=len(customer_ids)) + 0.02
    cust_w /= cust_w.sum()
    store_w = rng.gamma(1.5, size=args.stores) + 0.2
    store_w /= store_w.sum()

    addr_by_user = addresses.groupby("user_id")["id"].apply(list).to_dict()
    prod_by_store = {s: g[["id", "price"]].to_records(index=False).tolist()
                     for s, g in products.groupby("store_id")}
    promo_pct = dict(zip(promos["id"], promos["discount_percent"]))
    n_couriers = len(couriers)
    courier_user = dict(zip(couriers["id"], couriers["user_id"]))

    created_list = make_created_at(rng, args.orders, args.days, end)

    orders, items, payments, deliveries, history = [], [], [], [], []
    pay_id = del_id = item_id = hist_id = 0

    def minutes(m):
        return timedelta(minutes=float(m))

    for order_id, created in enumerate(created_list, start=1):
        cust_id = customer_ids[rng.choice(len(customer_ids), p=cust_w)]
        store_id = int(rng.choice(np.arange(1, args.stores + 1), p=store_w))
        store_user = store_user_ids[store_id - 1]
        address_id = int(rng.choice(addr_by_user[cust_id]))

        # промокод: 22% заказов, у таких заказов в среднем больше позиций
        promo_id = int(rng.integers(1, len(promos) + 1)) if rng.random() < 0.22 else None
        mean_extra = 1.7 if promo_id else 1.1
        catalog = prod_by_store[store_id]
        n_items = int(np.clip(1 + rng.poisson(mean_extra), 1, min(6, len(catalog))))
        picked = rng.choice(len(catalog), size=n_items, replace=False)

        subtotal = 0.0
        for idx in picked:
            product_id, price = catalog[int(idx)]
            qty = int(rng.choice([1, 2, 3], p=[0.7, 0.22, 0.08]))
            item_id += 1
            items.append({"id": item_id, "order_id": order_id, "product_id": int(product_id),
                          "quantity": qty, "price_at_order": float(price)})
            subtotal += qty * float(price)
        discount = promo_pct[promo_id] if promo_id else 0
        total = round(subtotal * (1 - discount / 100), 2)

        final = str(rng.choice(FINAL_STATUSES, p=FINAL_PROBS))
        t = created
        status_log = []

        def move(old, new, delta_min, actor):
            nonlocal t, hist_id
            t = t + minutes(delta_min)
            hist_id += 1
            history.append({"id": hist_id, "order_id": order_id, "old_status": old,
                            "new_status": new, "changed_at": t, "changed_by": actor})

        # первая запись истории: заказ создан
        hist_id += 1
        history.append({"id": hist_id, "order_id": order_id, "old_status": None,
                        "new_status": "created", "changed_at": created, "changed_by": cust_id})

        def add_payment(status, paid_at):
            nonlocal pay_id
            pay_id += 1
            payments.append({"id": pay_id, "order_id": order_id,
                             "method": str(rng.choice(PAYMENT_METHODS, p=[0.6, 0.3, 0.1])),
                             "status": status, "amount": total,
                             "external_id": f"pay_{order_id}_{pay_id}", "paid_at": paid_at})

        # --- отмена до оплаты ---
        cancel_before_pay = final == "cancelled" and rng.random() < 0.45
        if cancel_before_pay:
            move("created", "cancelled", rng.uniform(1, 15), cust_id)
            orders.append((order_id, cust_id, store_id, address_id, promo_id, "cancelled", total, created))
            continue

        # --- оплата не прошла ---
        if final == "payment_failed":
            for _ in range(int(rng.integers(1, 4))):
                add_payment("failed", None)
            move("created", "payment_failed", rng.uniform(1, 5), None)
            orders.append((order_id, cust_id, store_id, address_id, promo_id, "payment_failed", total, created))
            continue

        # --- оплата прошла (иногда со второй попытки) ---
        prev = "created"
        if rng.random() < 0.08:
            add_payment("failed", None)
            move("created", "payment_failed", rng.uniform(1, 3), None)
            prev = "payment_failed"
        move(prev, "paid", rng.uniform(1, 4), None)
        add_payment("success", t)
        paid_idx = len(payments) - 1

        def refund():
            payments[paid_idx]["status"] = "refunded"

        # --- отмена после оплаты ---
        if final == "cancelled":
            stage = str(rng.choice(["paid", "accepted_by_store", "ready"], p=[0.4, 0.4, 0.2]))
            if stage != "paid":
                move("paid", "accepted_by_store", 1 + rng.exponential(2), store_user)
            if stage == "ready":
                move("accepted_by_store", "ready", 8 + rng.gamma(4, 2.5), store_user)
            move(stage, "cancelled", rng.uniform(1, 10), cust_id)
            refund()
            orders.append((order_id, cust_id, store_id, address_id, promo_id, "cancelled", total, created))
            continue

        # --- магазин отклонил (в 40% случаев просто не ответил за 10 минут) ---
        if final == "rejected_by_store":
            timeout = rng.random() < 0.4
            move("paid", "rejected_by_store", 10 if timeout else 1 + rng.exponential(3),
                 None if timeout else store_user)
            refund()
            orders.append((order_id, cust_id, store_id, address_id, promo_id, "rejected_by_store", total, created))
            continue

        # --- обычный путь ---
        move("paid", "accepted_by_store", 1 + rng.exponential(2), store_user)
        move("accepted_by_store", "ready", 8 + rng.gamma(4, 2.5), store_user)

        # назначение курьера; в 10% случаев первый курьер отказывается
        courier_id = int(rng.integers(1, n_couriers + 1))
        move("ready", "assigned_to_courier", 1 + rng.exponential(2), None)
        assigned_at = t
        if rng.random() < 0.10:
            del_id += 1
            deliveries.append({"id": del_id, "order_id": order_id, "courier_id": courier_id,
                               "assigned_at": assigned_at, "picked_up_at": None, "delivered_at": None})
            move("assigned_to_courier", "ready", rng.uniform(1, 4), courier_user[courier_id])
            courier_id = int(rng.integers(1, n_couriers + 1))
            move("ready", "assigned_to_courier", rng.uniform(1, 4), None)
            assigned_at = t

        move("assigned_to_courier", "in_delivery", 3 + rng.gamma(2, 2), courier_user[courier_id])
        picked_up_at = t
        # в вечерний час пик доставка идёт медленнее
        rush = 1.2 if 18 <= created.hour <= 20 else 1.0
        trip = (8 + rng.gamma(4, 4)) * rush

        del_id += 1
        if final == "delivery_failed":
            move("in_delivery", "delivery_failed", trip, courier_user[courier_id])
            deliveries.append({"id": del_id, "order_id": order_id, "courier_id": courier_id,
                               "assigned_at": assigned_at, "picked_up_at": picked_up_at, "delivered_at": None})
        else:
            move("in_delivery", "delivered", trip, courier_user[courier_id])
            deliveries.append({"id": del_id, "order_id": order_id, "courier_id": courier_id,
                               "assigned_at": assigned_at, "picked_up_at": picked_up_at, "delivered_at": t})
        orders.append((order_id, cust_id, store_id, address_id, promo_id, final, total, created))

    orders_df = pd.DataFrame(orders, columns=["id", "user_id", "store_id", "address_id",
                                              "promo_code_id", "status", "total_amount", "created_at"])
    orders_df["promo_code_id"] = orders_df["promo_code_id"].astype("Int64")
    history_df = pd.DataFrame(history)
    history_df["changed_by"] = history_df["changed_by"].astype("Int64")
    return (orders_df, pd.DataFrame(items), pd.DataFrame(payments),
            pd.DataFrame(deliveries), history_df)


# ----------------------------------------------------------------------------
# Проверка и вывод сводки
# ----------------------------------------------------------------------------
def check_integrity(t):
    """Простая проверка внешних ключей до загрузки в базу."""
    checks = [
        ("address", "user_id", "users"), ("product", "store_id", "store"),
        ("orders", "user_id", "users"), ("orders", "store_id", "store"),
        ("orders", "address_id", "address"), ("order_item", "order_id", "orders"),
        ("order_item", "product_id", "product"), ("payment", "order_id", "orders"),
        ("courier", "user_id", "users"), ("delivery", "order_id", "orders"),
        ("delivery", "courier_id", "courier"), ("order_status_history", "order_id", "orders"),
    ]
    for child, col, parent in checks:
        bad = ~t[child][col].isin(t[parent]["id"])
        assert not bad.any(), f"Нарушен внешний ключ: {child}.{col} -> {parent}.id"
    promos = t["orders"]["promo_code_id"].dropna()
    assert promos.isin(t["promo_code"]["id"]).all(), "Нарушен внешний ключ: orders.promo_code_id"
    print("Проверка внешних ключей: ок")


def print_summary(t):
    print("\nСтрок в таблицах:")
    for name, df in t.items():
        print(f"  {name:22s} {len(df):>8d}")
    print("\nСтатусы заказов:")
    print(t["orders"]["status"].value_counts().to_string())
    print(f"\nПериод заказов: {t['orders']['created_at'].min()} — {t['orders']['created_at'].max()}")


# ----------------------------------------------------------------------------
# Сохранение
# ----------------------------------------------------------------------------
LOAD_ORDER = ["users", "address", "store", "product", "promo_code", "courier",
              "orders", "order_item", "payment", "delivery", "order_status_history"]


def save_csv(tables, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name in LOAD_ORDER:
        tables[name].to_csv(folder / f"{name}.csv", index=False)
    print(f"CSV сохранены в папку: {folder.resolve()}")


def load_mysql(tables, url, truncate):
    from sqlalchemy import create_engine, text  # импорт здесь, чтобы режим --csv-only работал без SQLAlchemy

    engine = create_engine(url)
    if truncate:
        with engine.begin() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            for name in reversed(LOAD_ORDER):
                conn.execute(text(f"TRUNCATE TABLE `{name}`"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        print("Таблицы очищены")
    for name in LOAD_ORDER:
        tables[name].to_sql(name, engine, if_exists="append", index=False,
                            chunksize=2000, method="multi")
        print(f"Загружено: {name} ({len(tables[name])})")


# ----------------------------------------------------------------------------
# Точка входа
# ----------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Генератор тестовых данных для delivery_service")
    p.add_argument("--url", default="mysql+pymysql://root:password@localhost:3306/delivery_service",
                   help="строка подключения SQLAlchemy")
    p.add_argument("--csv-only", action="store_true", help="сохранить CSV и не подключаться к MySQL")
    p.add_argument("--csv-dir", default="data", help="папка для CSV")
    p.add_argument("--truncate", action="store_true", help="очистить таблицы перед загрузкой")
    p.add_argument("--orders", type=int, default=N_ORDERS)
    p.add_argument("--customers", type=int, default=N_CUSTOMERS)
    p.add_argument("--couriers", type=int, default=N_COURIERS)
    p.add_argument("--stores", type=int, default=N_STORES)
    p.add_argument("--days", type=int, default=DAYS)
    p.add_argument("--seed", type=int, default=42, help="seed для повторяемости результата")
    args = p.parse_args()
    args.end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

    rng = np.random.default_rng(args.seed)

    users, admin_id, store_uids, courier_uids, customer_ids = make_users(
        rng, args.customers, args.couriers, args.stores, args.end)
    addresses = make_addresses(rng, customer_ids)
    stores = make_stores(rng, args.stores)
    products = make_products(rng, args.stores, PRODUCTS_PER_STORE)
    promos = make_promos()
    couriers = make_couriers(rng, courier_uids)

    orders, items, payments, deliveries, history = simulate_orders(
        rng, args, (admin_id, store_uids, courier_uids, customer_ids),
        addresses, stores, products, promos, couriers)

    tables = {
        "users": users, "address": addresses, "store": stores, "product": products,
        "promo_code": promos, "courier": couriers, "orders": orders,
        "order_item": items, "payment": payments, "delivery": deliveries,
        "order_status_history": history,
    }

    check_integrity(tables)
    print_summary(tables)

    if args.csv_only:
        save_csv(tables, args.csv_dir)
    else:
        load_mysql(tables, args.url, args.truncate)


if __name__ == "__main__":
    main()
