-- Сервис доставки заказов: схема базы данных (MySQL 8)
-- Порядок создания таблиц учитывает внешние ключи: сначала родители, потом потомки.

CREATE DATABASE IF NOT EXISTS delivery_service
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE delivery_service;

-- ---------------------------------------------------------
-- Пользователи (клиенты, курьеры, сотрудники магазинов, админы)
-- ---------------------------------------------------------
CREATE TABLE users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    role        ENUM('customer', 'courier', 'store', 'admin') NOT NULL,
    name        VARCHAR(100) NOT NULL,
    phone       VARCHAR(20)  NOT NULL UNIQUE,
    email       VARCHAR(100) UNIQUE,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Адреса пользователей
-- ---------------------------------------------------------
CREATE TABLE address (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT           NOT NULL,
    city     VARCHAR(100)  NOT NULL,
    street   VARCHAR(150)  NOT NULL,
    house    VARCHAR(20)   NOT NULL,
    flat     VARCHAR(20),
    lat      DECIMAL(9, 6),
    lon      DECIMAL(9, 6),
    CONSTRAINT fk_address_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Магазины
-- ---------------------------------------------------------
CREATE TABLE store (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    address     VARCHAR(255) NOT NULL,
    work_hours  VARCHAR(50),
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Товары магазинов
-- ---------------------------------------------------------
CREATE TABLE product (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    store_id      INT            NOT NULL,
    name          VARCHAR(150)   NOT NULL,
    price         DECIMAL(10, 2) NOT NULL,
    is_available  BOOLEAN        NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_product_store FOREIGN KEY (store_id) REFERENCES store (id)
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Промокоды
-- ---------------------------------------------------------
CREATE TABLE promo_code (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    code              VARCHAR(30)      NOT NULL UNIQUE,
    discount_percent  TINYINT UNSIGNED NOT NULL,
    valid_to          DATE,
    usage_limit       INT
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Заказы
-- Таблица называется orders, потому что order это зарезервированное слово SQL
-- ---------------------------------------------------------
CREATE TABLE orders (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT            NOT NULL,
    store_id       INT            NOT NULL,
    address_id     INT            NOT NULL,
    promo_code_id  INT,
    status         ENUM(
                       'created',
                       'paid',
                       'payment_failed',
                       'accepted_by_store',
                       'rejected_by_store',
                       'ready',
                       'assigned_to_courier',
                       'in_delivery',
                       'delivered',
                       'delivery_failed',
                       'cancelled'
                   ) NOT NULL DEFAULT 'created',
    total_amount   DECIMAL(10, 2) NOT NULL,
    created_at     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_user    FOREIGN KEY (user_id)       REFERENCES users (id),
    CONSTRAINT fk_orders_store   FOREIGN KEY (store_id)      REFERENCES store (id),
    CONSTRAINT fk_orders_address FOREIGN KEY (address_id)    REFERENCES address (id),
    CONSTRAINT fk_orders_promo   FOREIGN KEY (promo_code_id) REFERENCES promo_code (id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_created_at (created_at)
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Позиции заказа
-- price_at_order хранит цену на момент покупки: цена товара потом может измениться
-- ---------------------------------------------------------
CREATE TABLE order_item (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    order_id        INT            NOT NULL,
    product_id      INT            NOT NULL,
    quantity        INT            NOT NULL,
    price_at_order  DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_item_order   FOREIGN KEY (order_id)   REFERENCES orders (id),
    CONSTRAINT fk_item_product FOREIGN KEY (product_id) REFERENCES product (id)
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Платежи (у одного заказа может быть несколько попыток оплаты)
-- ---------------------------------------------------------
CREATE TABLE payment (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    order_id     INT            NOT NULL,
    method       VARCHAR(30)    NOT NULL,
    status       ENUM('pending', 'success', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
    amount       DECIMAL(10, 2) NOT NULL,
    external_id  VARCHAR(100),
    paid_at      DATETIME,
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES orders (id)
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Курьеры
-- ---------------------------------------------------------
CREATE TABLE courier (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL UNIQUE,
    status        ENUM('free', 'busy', 'offline') NOT NULL DEFAULT 'offline',
    vehicle_type  VARCHAR(30),
    CONSTRAINT fk_courier_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- Доставки (одна строка на каждое назначение курьера:
-- если курьер отказался, появляется новая строка)
-- ---------------------------------------------------------
CREATE TABLE delivery (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    order_id      INT      NOT NULL,
    courier_id    INT      NOT NULL,
    assigned_at   DATETIME NOT NULL,
    picked_up_at  DATETIME,
    delivered_at  DATETIME,
    CONSTRAINT fk_delivery_order   FOREIGN KEY (order_id)   REFERENCES orders (id),
    CONSTRAINT fk_delivery_courier FOREIGN KEY (courier_id) REFERENCES courier (id)
) ENGINE = InnoDB;

-- ---------------------------------------------------------
-- История смены статусов заказа
-- changed_by может быть пустым, если статус сменила система (например, таймаут)
-- ---------------------------------------------------------
CREATE TABLE order_status_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    order_id    INT      NOT NULL,
    old_status  ENUM(
                    'created', 'paid', 'payment_failed', 'accepted_by_store',
                    'rejected_by_store', 'ready', 'assigned_to_courier',
                    'in_delivery', 'delivered', 'delivery_failed', 'cancelled'
                ),
    new_status  ENUM(
                    'created', 'paid', 'payment_failed', 'accepted_by_store',
                    'rejected_by_store', 'ready', 'assigned_to_courier',
                    'in_delivery', 'delivered', 'delivery_failed', 'cancelled'
                ) NOT NULL,
    changed_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by  INT,
    CONSTRAINT fk_history_order FOREIGN KEY (order_id)   REFERENCES orders (id),
    CONSTRAINT fk_history_user  FOREIGN KEY (changed_by) REFERENCES users (id)
) ENGINE = InnoDB;

USE delivery_service;
SHOW TABLES;