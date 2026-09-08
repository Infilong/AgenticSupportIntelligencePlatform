BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT format(
  'SELECT %L AS table_name, count(*) AS row_count, md5(coalesce(string_agg(row_data, chr(10) ORDER BY row_data COLLATE "C"), '''')) AS content_hash FROM (SELECT to_jsonb(t)::text AS row_data FROM %I.%I t) rows',
  tablename, schemaname, tablename
)
FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename
\gexec
COMMIT;
