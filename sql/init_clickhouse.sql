-- Создание базы данных
CREATE DATABASE IF NOT EXISTS cctech_audit_secure;

-- Создание таблицы для логов аудита
CREATE TABLE IF NOT EXISTS cctech_audit_secure.security_and_billing_events (
    timestamp DateTime64(3),
    environment LowCardinality(String),
    scoring_uid String,
    b2b_client_token String,
    charged_rub Float32,
    credit_score UInt16,
    probability_of_default Float32,
    avm_fair_value_now UInt64,
    verdict LowCardinality(String),
    user_agent String,
    client_ip String
)
ENGINE = MergeTree()
PRIMARY KEY (verdict, timestamp)
ORDER BY (verdict, timestamp, scoring_uid);

-- Создание таблицы для биллинга транзакций
CREATE TABLE IF NOT EXISTS cctech_audit_secure.billing_transactions (
    transaction_id UUID,
    client_id String,
    amount Float32,
    service_type LowCardinality(String),
    timestamp DateTime64(3)
)
ENGINE = MergeTree()
ORDER BY timestamp;

-- (Опционально) Создание пользователя для приложения
CREATE USER IF NOT EXISTS app_user IDENTIFIED BY 'app_secure_password';
GRANT SELECT, INSERT ON cctech_audit_secure.* TO app_user;
