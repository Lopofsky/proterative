UPDATE reservation
SET comment = jsonb_set(comment, '{tax_data}', (comment->>'tax_data')::jsonb || ('{"tax_total_amount":"'|| ((checkout-checkin)*3)::text ||'"}')::jsonb)
WHERE comment->'tax_data' IS NOT NULL AND (comment->'tax_data')::text NOT ILIKE '%tax_total_amount%';

select  jsonb_set(s.calendar, '{2021-01-01}', '{"34":{"working":{"7:00-11:00":"", "16:30-20:30":""}}}'::jsonb)
from "Schedule2021" s
where s."hotel_ID"=48