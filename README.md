# Delivery Service: аналитика и проектирование

Учебный проект: проектирование сервиса доставки заказов и аналитика на данных.

## Что внутри
- **docs/**: BPMN-процесс заказа, диаграмма состояний, ER-диаграмма
- **sql/**: схема MySQL (`schema.sql`) и аналитические запросы (`requests.sql`)
- **scripts/**: генератор тестовых данных на Python (numpy, pandas)

## Как запустить
1. Создать базу: выполнить `sql/schema.sql` в MySQL 8
2. Установить зависимости: `pip install numpy pandas sqlalchemy pymysql`
3. Загрузить данные: `python scripts/generate_data.py --url "mysql+pymysql://USER:PASSWORD@localhost:3306/delivery_service" --truncate`

## Стек
MySQL, Python (numpy, pandas), draw.io (BPMN, UML, ER), Jira, Confluence