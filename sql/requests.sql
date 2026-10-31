SELECT status, COUNT(*) 
FROM delivery_service.orders
GROUP BY status;
SELECT COUNT(*) FROM delivery_service.order_status_history;

select count(*) as total_orders, sum(total_amount) as total_cash,
    sum(case
        when status = 'delivered'
        then total_amount
    end) as total_delivered,
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as total_delivered_count
from delivery_service.orders;

select count(*) as total_orders, status, sum(total_amount) as total_cash
from delivery_service.orders
group by status;

select sum(total_amount) as total_cash, DATE_FORMAT(created_at, '%Y-%m') as order_date
from delivery_service.orders
group by order_date;

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

select avg(total_amount) as average_total_amount
from delivery_service.orders
where status = 'delivered' and promo_code_id is not null;
select avg(total_amount) as average_total_amount
from delivery_service.orders
where status = 'delivered' and promo_code_id is null;

select s.name, sum(o.total_amount) as revenue
from delivery_service.orders o
join delivery_service.store s on o.store_id = s.id
where o.status = 'delivered'
group by s.id, s.name
order by revenue desc
limit 5;



    