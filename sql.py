import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

# Load environment variables from .env file
load_dotenv()

# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL')


def create_members_table():
    # Connect to the database
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    try:
        # Check if the table exists
        cur.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'members')")
        table_exists = cur.fetchone()[0]

        if table_exists:
            # If the table exists, print a sample line
            cur.execute("SELECT * FROM members LIMIT 1")
            sample = cur.fetchone()
            if sample:
                print("The 'members' table exists. Here's a sample row:")
                print(sample)
            else:
                print("The 'members' table exists but is empty.")
        else:
            # If the table doesn't exist, create it
            create_table_query = sql.SQL("""
                CREATE TABLE members (
                    id SERIAL PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    phone_number VARCHAR(20) UNIQUE NOT NULL,
                    date_of_birth DATE NOT NULL,
                    gender VARCHAR(10),
                    street_address VARCHAR(200),
                    city VARCHAR(50),
                    state VARCHAR(2),
                    zip_code VARCHAR(10),
                    email VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute(create_table_query)
            cur.execute("""
                COMMENT ON TABLE members IS 'Table containing member information including id, name and contact information.';
            """)
            conn.commit()
            print("Table 'members' created successfully.")

    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()


def insert_members_records():
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    try:
        # Sample data
        first_names = ['John', 'Jane', 'Michael', 'Emily',
                       'David', 'Sarah', 'Robert', 'Lisa', 'William', 'Emma']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones',
                      'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        genders = ['Male', 'Female']
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
                  'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
        states = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA', 'TX', 'CA']
        zip_codes = ['10001', '90001', '60601', '77001',
                     '85001', '19101', '78201', '92101', '75201', '95101']

        inserted_records = []

        for i in range(10):
            first_name = first_names[i]
            last_name = last_names[i]
            phone_number = f'555-{random.randint(100, 999)}-{random.randint(1000, 9999)}'
            date_of_birth = (datetime.now(
            ) - timedelta(days=random.randint(7300, 25550))).strftime('%Y-%m-%d')
            gender = random.choice(genders)
            street_address = f'{random.randint(100, 999)} Main St'
            city = cities[i]
            state = states[i]
            zip_code = zip_codes[i]  # Add zip code
            email = f'{first_name.lower()}.{last_name.lower()}@example.com'

            record = (first_name, last_name, phone_number, date_of_birth, gender,
                      street_address, city, state, zip_code, email)  # Include zip_code in record
            inserted_records.append(record)

            insert_query = sql.SQL("""
                INSERT INTO members (first_name, last_name, phone_number, date_of_birth, gender, street_address, city, state, zip_code, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """)
            cur.execute(insert_query, record)

        conn.commit()
        print("10 sample records inserted successfully.")

        # Print the inserted records
        print("\nInserted Records:")
        for i, record in enumerate(inserted_records, 1):
            print(f"\nRecord {i}:")
            print(f"Name: {record[0]} {record[1]}")
            print(f"Phone: {record[2]}")
            print(f"Date of Birth: {record[3]}")
            print(f"Gender: {record[4]}")
            # Include zip code in address
            print(
                f"Address: {record[5]}, {record[6]}, {record[7]} {record[8]}")
            print(f"Email: {record[9]}")

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()


def create_providers_table():
    """
    Create the providers table if it doesn't exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS providers (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        phone_number VARCHAR(20) UNIQUE NOT NULL,
        date_of_birth DATE NOT NULL,
        gender VARCHAR(10),
        street_address VARCHAR(200),
        city VARCHAR(50),
        state VARCHAR(2),
        zip_code VARCHAR(10),
        email VARCHAR(100) UNIQUE NOT NULL,
        degree VARCHAR(10),
        procedures VARCHAR[],
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    """
    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            cur.execute("""
                COMMENT ON TABLE members IS 'Table containing provider information including id, name, credentials and contact information.';
            """)
            conn.commit()
            print("Table 'providers' created successfully.")


def insert_providers_records():
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    try:
        # Sample data
        first_names = ['Emma', 'Liam', 'Olivia', 'Noah', 'Ava',
                       'Ethan', 'Sophia', 'Mason', 'Isabella', 'William']
        last_names = ['Johnson', 'Smith', 'Brown', 'Davis', 'Wilson',
                      'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson']
        genders = ['Female', 'Male']
        cities = ['Boston', 'Seattle', 'Miami', 'Denver', 'Atlanta',
                  'Portland', 'Austin', 'Nashville', 'Minneapolis', 'San Francisco']
        states = ['MA', 'WA', 'FL', 'CO', 'GA', 'OR', 'TX', 'TN', 'MN', 'CA']
        zip_codes = ['02108', '98101', '33101', '80201',
                     '30301', '97201', '78701', '37201', '55401', '94101']
        degrees = ['MD', 'NP']
        possible_procedures = ['blood_work',
                               'vision_test', 'mental_health_eval']

        inserted_records = []

        for i in range(10):
            first_name = first_names[i]
            last_name = last_names[i]
            phone_number = f'555-{random.randint(100, 999)}-{random.randint(1000, 9999)}'
            date_of_birth = (datetime.now(
            ) - timedelta(days=random.randint(10950, 25550))).strftime('%Y-%m-%d')
            gender = random.choice(genders)
            street_address = f'{random.randint(100, 999)} Medical Ave'
            city = cities[i]
            state = states[i]
            zip_code = zip_codes[i]
            email = f'{first_name.lower()}.{last_name.lower()}@medprovider.com'
            degree = random.choice(degrees)
            procedures = random.sample(
                possible_procedures, random.randint(0, 3))
            record = (first_name, last_name, phone_number, date_of_birth, gender,
                      street_address, city, state, zip_code, email, degree, procedures)
            inserted_records.append(record)

            insert_query = sql.SQL("""
                INSERT INTO providers (first_name, last_name, phone_number, date_of_birth, gender, street_address, city, state, zip_code, email, degree, procedures)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """)
            cur.execute(insert_query, record)

        conn.commit()
        print("10 sample provider records inserted successfully.")

        # Print the inserted records
        print("\nInserted Provider Records:")
        for i, record in enumerate(inserted_records, 1):
            print(f"\nProvider {i}:")
            print(f"Name: {record[0]} {record[1]}, {record[10]}")
            print(f"Phone: {record[2]}")
            print(f"Date of Birth: {record[3]}")
            print(f"Gender: {record[4]}")
            print(
                f"Address: {record[5]}, {record[6]}, {record[7]} {record[8]}")
            print(f"Email: {record[9]}")
            # Changed from record[10] to record[11]
            print(f"Procedures: {', '.join(record[11])}")

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()


def delete_table(table_name):
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    try:
        cur.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
            sql.Identifier(table_name)))
        conn.commit()
        print(f"Table {table_name} has been deleted successfully.")
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def create_appointments_table():
    """
    Create the appointments table if it doesn't exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS appointments (
        id SERIAL PRIMARY KEY,
        member_id INTEGER REFERENCES members(id),
        provider_id INTEGER REFERENCES providers(id),
        member_phone VARCHAR(20) NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL,
        street_address VARCHAR(200),
        city VARCHAR(50),
        state VARCHAR(2),
        zip_code VARCHAR(10),
        status VARCHAR(20) CHECK (status IN ('scheduled', 'completed', 'cancelled')),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    """
    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            cur.execute("""
                COMMENT ON TABLE appointments IS 'Table containing appointment information.';
            """)
            conn.commit()
            print("Table 'appointments' created successfully.")


def insert_appointments_records():
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    try:
        # Get existing member data
        cur.execute(
            "SELECT id, phone_number, street_address, city, state, zip_code FROM members")
        members = cur.fetchall()

        # Get existing provider data
        cur.execute("SELECT id, procedures FROM providers")
        providers = cur.fetchall()

        possible_procedures = ['blood_work', 'vision_test',
                               'mental_health_eval', 'physical_exam', 'vaccination']

        inserted_records = []

        for _ in range(10):
            member = random.choice(members)
            member_id, member_phone, street_address, city, state, zip_code = member

            provider = random.choice(providers)
            provider_id, provider_procedures = provider

            date = (datetime.now() +
                    timedelta(days=random.randint(-30, 30))).strftime('%Y-%m-%d')
            time = f"{random.randint(9, 17):02d}:{random.choice(['00', '30'])}:00"

            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
            current_date = datetime.now().date()

            if appointment_date < current_date:
                # Past appointment
                status = random.choice(['completed', 'cancelled'])
            else:
                # Future appointment
                status = random.choice(['scheduled', 'cancelled'])

            record = (member_id, provider_id, member_phone, date, time,
                      street_address, city, state, zip_code, status)
            inserted_records.append(record)

            insert_query = sql.SQL("""
                INSERT INTO appointments (member_id, provider_id, member_phone, date, time, street_address, city, state, zip_code, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """)
            cur.execute(insert_query, record)

        conn.commit()
        print("10 sample appointment records inserted successfully.")

        # Print the inserted records
        print("\nInserted Appointment Records:")
        for i, record in enumerate(inserted_records, 1):
            print(f"\nAppointment {i}:")
            print(f"Member ID: {record[0]}")
            print(f"Provider ID: {record[1]}")
            print(f"Member Phone: {record[2]}")
            print(f"Date and Time: {record[3]} {record[4]}")
            print(
                f"Address: {record[5]}, {record[6]}, {record[7]} {record[8]}")
            print(f"Status: {record[9]}")

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()


def create_availability_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS availability (
        provider_id INT,
        date DATE,
        start_time TIME,
        end_time TIME,
        status VARCHAR(20) CHECK (status IN ('available', 'unavailable')),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES providers(id)
    )
    """
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL')

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            cur.execute("""
                COMMENT ON TABLE availability IS 'Table containing provider availability information.';
            """)
            conn.commit()
            print("Table 'availability' created successfully.")


def insert_availability_records():
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL')

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            # Fetch all providers
            cur.execute("SELECT id FROM providers")
            providers = cur.fetchall()

            # Generate availability records for each provider for a 2-week period
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=14)
            availability_records = []

            for provider in providers:
                provider_id = provider[0]
                current_date = start_date
                while current_date < end_date:
                    # Morning slot: 9 AM to 12 PM
                    availability_records.append(
                        (provider_id, current_date, '09:00:00', '12:00:00', 'available'))
                    # Afternoon slot: 12 PM to 5 PM
                    availability_records.append(
                        (provider_id, current_date, '12:00:00', '17:00:00', 'available'))
                    current_date += timedelta(days=1)

            # Insert records into the availability table
            insert_query = """
            INSERT INTO availability (provider_id, date, start_time, end_time, status)
            VALUES (%s, %s, %s, %s, %s)
            """
            cur.executemany(insert_query, availability_records)
            conn.commit()
            print("Availability records inserted successfully.")


def create_escalations_table():
    """
    Create the escalations table if it doesn't exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS escalations (
        id SERIAL PRIMARY KEY,
        phone_number VARCHAR(20) UNIQUE NOT NULL,
        status VARCHAR(20) CHECK (status IN ('escalated', 'de_escalated')),
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    """
    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            cur.execute("""
                COMMENT ON TABLE escalations IS 'Table containing escalation information including phone number, de-escalation status, and description.';
            """)
            conn.commit()
            print("Table 'escalations' created successfully.")



def insert_escalations_records():
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL')

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            # Sample escalation records
            escalation_records = [
                ('555-932-4455', 'escalated', 'Member requested supervisor to call back.'),
                ('215-999-2234', 'de_escalated', 'Issue resolved after follow-up.'),
                ('848-321-4456', 'escalated', 'Member expressed dissatisfaction with service.')
            ]

            # Insert records into the escalations table
            insert_query = """
            INSERT INTO escalations (phone_number, status, description)
            VALUES (%s, %s, %s)
            """
            cur.executemany(insert_query, escalation_records)
            conn.commit()
            print("Escalation records inserted successfully.")




# Call the function
if __name__ == "__main__":
    delete_table('appointments')
    delete_table('providers')
    delete_table('members')
    delete_table('availability')
    delete_table('escalations')
    create_members_table()
    insert_members_records()
    create_providers_table()
    insert_providers_records()
    create_appointments_table()
    insert_appointments_records()
    create_availability_table()
    insert_availability_records()
    create_escalations_table()
    insert_escalations_records()
