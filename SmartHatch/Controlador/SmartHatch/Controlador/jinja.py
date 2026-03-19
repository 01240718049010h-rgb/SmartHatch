from jinja2 import Template
import psycopg2.extras
import psycopg2
import psycopg2-binary

DATABASE_URL = "postgresql://smarthatch_db_user:8zdKUU03sgVXqKfInHKKIkjIxyLqs1sx@dpg-d6t0phfgi27c73dctv6g-a.virginia-postgres.render.com/smarthatch_db"

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor.execute("SELECT * FROM LOTES ORDER BY numero ASC LIMIT 1")
row = cursor.fetchone()

# TEST JINJA RENDER
template = Template("ID: {{ lote.id }} | NUMERO: {{ lote.numero }}")
print(template.render(lote=row))
