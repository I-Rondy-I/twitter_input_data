import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
import psycopg2.extras
from datetime import datetime, time
import pytz
from tzlocal import get_localzone

# Load environment variables from .env file
load_dotenv()

# Retrieve database configuration from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

TABLE_NAME_TPD = os.getenv("TABLE_NAME_TPD")
TABLE_NAME_MEDIA = os.getenv("TABLE_NAME_MEDIA")
TABLE_NAME_TPD_WD = os.getenv("TABLE_NAME_TPD_WD")
TABLE_NAME_TPD_TT = os.getenv("TABLE_NAME_TPD_TT")
TABLE_NAME_WD = os.getenv("TABLE_NAME_WD")
TABLE_NAME_TT = os.getenv("TABLE_NAME_TT")
TABLE_NAME_STATS = os.getenv("TABLE_NAME_STATS")

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def select_from_db_view_data():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        # Użycie DictCursor, aby fetchall() zwróciło listę słowników
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # SQL query to join tables and select the desired fields
        select_sql = f"""
        SELECT 
            tpd.id, 
            tpd.name, 
            tpd.text, 
            ARRAY_AGG(DISTINCT media.media_name) AS media_files,
            tpd.is_random, 
            ARRAY_AGG(DISTINCT wd.day_name) AS week_days, 
            ARRAY_AGG(DISTINCT tt.time) AS tweet_times
        FROM 
            {TABLE_NAME_TPD} tpd
        LEFT JOIN 
            {TABLE_NAME_MEDIA} ON tpd.id = media.tpd_id
        LEFT JOIN 
            {TABLE_NAME_TPD_WD} ON tpd.id = tpd_wd.tpd_id
        LEFT JOIN 
            {TABLE_NAME_WD} wd ON tpd_wd.wd_id = wd.id
        LEFT JOIN 
            {TABLE_NAME_TPD_TT} ON tpd.id = tpd_tt.tpd_id
        LEFT JOIN 
            {TABLE_NAME_TT} tt ON tpd_tt.tt_id = tt.id
        GROUP BY 
            tpd.id, tpd.name, tpd.text, tpd.is_random;
        """
        cursor.execute(select_sql)
        results = cursor.fetchall()
        
        for record in results:
            record['tweet_times'] = times_utc_to_local(record['tweet_times'])

        return results

    except Exception as error:
        print(f"Error retrieving data from database: {error}")
        return None

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def times_local_to_utc(local_times_list):
    utc_times_list = []
    for local_time_str in local_times_list:
        utc_time_str = time_local_to_utc(local_time_str)
        utc_times_list.append(utc_time_str)
    return utc_times_list
    
def times_utc_to_local(utc_times_list):
    local_times_list = []
    for utc_time_str in utc_times_list:
        local_time_str = time_utc_to_local(utc_time_str)
        local_times_list.append(local_time_str)
    return local_times_list

def delete_record_from_db(item_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # SQL queries to delete from all related tables
        delete_sqls = [
            "DELETE FROM tpd_tt WHERE tpd_id = %s",
            "DELETE FROM tpd_wd WHERE tpd_id = %s",
            "DELETE FROM media WHERE tpd_id = %s",
            "DELETE FROM tweet_post_data WHERE id = %s"
        ]

        for sql in delete_sqls:
            cursor.execute(sql, (item_id,))

        connection.commit()
        return 0  # Indicate success

    except Exception as error:
        print(f"Error deleting record from database: {error}")
        connection.rollback()
        return 1  # Indicate error

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def select_from_db_stats():
    connection = None
    cursor = None
    results = []

    try:
        connection = get_connection()
        # Użycie DictCursor, aby fetchall() zwróciło listę słowników
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # SQL query to join stats with tweet_post_data and select the desired fields
        select_sql = """
        SELECT s.id, tpd.name, s.date, s.time, wd.day_name, s.status
        FROM public.stats s
        JOIN public.tweet_post_data tpd ON s.tpd_id = tpd.id
        JOIN public.week_days wd ON s.wd_id = wd.id
        """
        cursor.execute(select_sql)
        results = cursor.fetchall()

        for record in results:
            record['time'] = times_utc_to_local(record['time'])

    except Exception as error:
        print(f"Error retrieving data from database: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return results

def insert_into_db_tpd(name, text, is_random):
    connection = None
    cursor = None
    tpd_id = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Insert data into TPD table and return the generated ID
        insert_sql = """
        INSERT INTO {table_name} (name, text, is_random)
        VALUES (%s, %s, %s) RETURNING id
        """
        insert_query = sql.SQL(insert_sql).format(table_name=sql.Identifier(TABLE_NAME_TPD))

        cursor.execute(insert_query, (name, text, is_random))
        tpd_id = cursor.fetchone()[0]  # Fetch the generated id
        connection.commit()

    except Exception as error:
        print(f"Error saving to database(tpd): {error}")
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return tpd_id

def insert_into_db_media(tpd_id, media_files):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        insert_sql = """
        INSERT INTO {table_name} (tpd_id, media_name, media_type, media_data)
        VALUES (%s, %s, %s, %s)
        """
        insert_query = sql.SQL(insert_sql).format(table_name=sql.Identifier(TABLE_NAME_MEDIA))

        for media_file in media_files:
            # Get the file name with extension
            file_name_with_extension = os.path.basename(media_file)
            # Split the file name and extension
            file_name, file_extension = os.path.splitext(file_name_with_extension)

            with open(media_file, 'rb') as file:
                media_data = file.read()
                cursor.execute(insert_query, (tpd_id, file_name, file_extension, psycopg2.Binary(media_data)))
        
        connection.commit()

    except Exception as error:
        print(f"Error saving to database(media): {error}")
        return 1

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return 0

def get_wd_id(day_name):
    """Retrieve week_day ID based on the day name."""
    connection = None
    cursor = None
    wd_id = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        select_sql = """
        SELECT id FROM {table_name} WHERE day_name = %s
        """
        select_query = sql.SQL(select_sql).format(table_name=sql.Identifier(TABLE_NAME_WD))

        cursor.execute(select_query, (day_name,))
        result = cursor.fetchone()

        if result:
            wd_id = result[0]

    except Exception as error:
        print(f"Error retrieving week day ID: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return wd_id

def insert_into_db_tpd_wd(tpd_id, week_days):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        insert_sql = """
        INSERT INTO {table_name} (tpd_id, wd_id)
        VALUES (%s, %s)
        """
        insert_query = sql.SQL(insert_sql).format(table_name=sql.Identifier(TABLE_NAME_TPD_WD))

        for day in week_days:
            wd_id = get_wd_id(day)
            if wd_id is not None:
                cursor.execute(insert_query, (tpd_id, wd_id))
            else:
                print(f"Week day '{day}' not found in the week_days table.")

        connection.commit()

    except Exception as error:
        print(f"Error saving to database(tpd_wd): {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def time_utc_to_local(utc_time_str):
    if utc_time_str is None:
        return None
    if not isinstance(utc_time_str, str):
        utc_time_str = utc_time_str.strftime('%H:%M:%S')

    # Pobierz aktualną datę
    current_date = datetime.now(pytz.utc).date()
    
    # Połącz datę i czas, aby uzyskać pełny obiekt datetime w UTC
    utc_time = datetime.combine(current_date, time.fromisoformat(utc_time_str)).replace(tzinfo=pytz.utc)
    
    # Pobierz lokalną strefę czasową
    local_tz = get_localzone()
    
    # Przekształć czas UTC na lokalny czas
    local_time = utc_time.astimezone(local_tz)
    
    return local_time.strftime('%H:%M:%S')
    
def time_local_to_utc(local_time_str):
    if local_time_str is None:
        return None
    if not isinstance(local_time_str, str):
        local_time_str = local_time_str.strftime('%H:%M:%S')

    # Pobierz aktualną datę
    current_date = datetime.now().date()
    
    # Pobierz lokalną strefę czasową
    local_tz = get_localzone()
    
    # Połącz datę i czas, aby uzyskać pełny obiekt datetime w lokalnej strefie czasowej
    local_time = datetime.combine(current_date, time.fromisoformat(local_time_str)).replace(tzinfo=local_tz)
    
    # Przekształć lokalny czas na czas UTC
    utc_time = local_time.astimezone(pytz.utc)
    
    return utc_time.strftime('%H:%M:%S')

def get_tt_id(tweet_time):
    """Retrieve tweet_time ID based on the tweet time."""
    connection = None
    cursor = None
    tt_id = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        select_sql = """
        SELECT id FROM {table_name} WHERE time = %s
        """
        select_query = sql.SQL(select_sql).format(table_name=sql.Identifier(TABLE_NAME_TT))

        # Convert 'HH:MM' to 'HH:MM:SS' format to match database format
        tweet_time_formatted = f"{tweet_time}:00"
        tweet_time_formatted = time_local_to_utc(tweet_time_formatted)
        
        cursor.execute(select_query, (tweet_time_formatted,))
        result = cursor.fetchone()

        if result:
            tt_id = result[0]

    except Exception as error:
        print(f"Error retrieving tt ID: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return tt_id

def insert_into_db_tpd_tt(tpd_id, tweet_times):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        insert_sql = """
        INSERT INTO {table_name} (tpd_id, tt_id)
        VALUES (%s, %s)
        """
        insert_query = sql.SQL(insert_sql).format(table_name=sql.Identifier(TABLE_NAME_TPD_TT))

        for time in tweet_times:
            tt_id = get_tt_id(time)
            if tt_id is not None:
                cursor.execute(insert_query, (tpd_id, tt_id))
            else:
                print(f"Tweet time '{time}' not found in the tweet_times table.")

        connection.commit()

    except Exception as error:
        print(f"Error saving to database(tpd_tt): {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def save_complete_tpd(name, text, is_random, media_files, week_days, tweet_times):
    # Insert into TPD table and get the generated ID
    tpd_id = insert_into_db_tpd(name, text, is_random)
    
    if tpd_id:
        # Insert related data into other tables
        insert_into_db_media(tpd_id, media_files)
        insert_into_db_tpd_wd(tpd_id, week_days)
        insert_into_db_tpd_tt(tpd_id, tweet_times)
        print("Done to insert into TPD table.")
        return 0
    else:
        print("Failed to insert into TPD table.")
        return 1
