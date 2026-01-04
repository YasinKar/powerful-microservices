CREATE EXTENSION IF NOT EXISTS citus;

SELECT master_add_node('users_citus_worker1', 5433);
SELECT master_add_node('users_citus_worker2', 5433);

-- SELECT create_distributed_table('api_user', 'id');

-- SELECT create_reference_table('api_user');