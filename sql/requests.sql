SELECT status, COUNT(*) 
FROM delivery_service.orders
GROUP BY status;
SELECT COUNT(*) FROM delivery_service.order_status_history;


--Общая статистика по заказам.
select count(*) as total_orders, sum(total_amount) as total_cash,
    sum(case
        when status = 'delivered'
        then total_amount
    end) as total_delivered,
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as total_delivered_count
from delivery_service.orders;

--Сумма заказов по статусам.
select count(*) as total_orders, status, sum(total_amount) as total_cash
from delivery_service.orders
group by status;

--Сумма заказов по месяцам.
select sum(total_amount) as total_cash, DATE_FORMAT(created_at, '%Y-%m') as order_date
from delivery_service.orders
group by order_date;

--Средняя сумма заказа с промокодом и без промокода.
select 
    avg(case
        when promo_code_id is not null 
        then total_amount
    end) as total_with_discount,
    avg(case
        when promo_code_id is null
        then total_amount
    end) as total_without_discount
from delivery_service.orders
where status = 'delivered'

--Средняя сумма заказа с промокодом и без промокода.
select avg(total_amount) as average_total_amount
from delivery_service.orders
where status = 'delivered' and promo_code_id is not null;
select avg(total_amount) as average_total_amount
from delivery_service.orders
where status = 'delivered' and promo_code_id is null;

--Топ 5 магазинов по выручке.
select s.name, sum(o.total_amount) as revenue
from delivery_service.orders o
join delivery_service.store s on o.store_id = s.id
where o.status = 'delivered'
group by s.id, s.name
order by revenue desc
limit 5;

--Топ 10 пользователей по выручке.
select u.name, sum(o.total_amount) as revenue, 
    count(*) as orders_cnt
from delivery_service.orders o
join delivery_service.users u on o.user_id = u.id
where o.status = 'delivered'
group by u.id, u.name
order by revenue desc
limit 10;

--Время доставки по часам. Сколько доставок в час и среднее время доставки в минутах.
select count(*) as deliberies_cnt, round(avg(timestampdiff(minute, picked_up_at, delivered_at)),1) as delivery_time_minutes, hour(o.created_at) as order_hour
from delivery_service.delivery d
inner join delivery_service.orders o on d.order_id = o.id
where delivered_at IS NOT NULL
group by order_hour
having count(*) >= 100
order by delivery_time_minutes desc;

--Воронка заказов. Сколько заказов было создано, сколько оплачено, сколько доставлено и какая доля заказов доходит до конца.
select created_cnt, paid_cnt, delivered_cnt,
    round(100 * delivered_cnt / created_cnt, 1) as delivered_conversion_rate,
    round(100 * paid_cnt / created_cnt, 1) as paid_conversion_rate
from (
    select 
        count(distinct case when new_status = 'created' then order_id end) as created_cnt,
        count(distinct case when new_status = 'paid' then order_id end) as paid_cnt,
        count(distinct case when new_status = 'delivered' then order_id end) as delivered_cnt
    from delivery_service.order_status_history
) as status_counts;





    