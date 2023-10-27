from flask import Flask, request, jsonify, render_template, redirect
import mysql.connector
import base64
import hashlib

app = Flask(__name__)

# Initialize MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="master1",
    password="master1@1Fence",
    database="url_shortener"
)

cursor = db.cursor()

# Create a table to store URLs
cursor.execute(
    "CREATE TABLE IF NOT EXISTS urls (id INT AUTO_INCREMENT PRIMARY KEY, long_url VARCHAR(255), short_url VARCHAR(255), title VARCHAR(255), hits INT)")

# Create the "counter" table
cursor.execute("CREATE TABLE IF NOT EXISTS counter (id INT AUTO_INCREMENT PRIMARY KEY, count INT DEFAULT 1)")

db.commit()


def get_unique_id():
    # Assuming you have a database connection `db` and a cursor `cursor`
    cursor.execute("UPDATE counter SET count = LAST_INSERT_ID(count + 1)")
    cursor.execute("SELECT LAST_INSERT_ID()")
    return cursor.fetchone()[0]


# Function to generate short URL (you can customize this)
def generate_short_url(long_url):
    # Combine a hash of the long URL and a unique ID
    unique_id = get_unique_id()  # Implement your method to get a unique ID
    combined_str = long_url + str(unique_id)
    hash_object = hashlib.sha256(combined_str.encode())
    hex_dig = hash_object.hexdigest()

    # Encode the hash to a shorter string
    short_url = base64.urlsafe_b64encode(hex_dig.encode()).decode()[:8]

    return short_url


@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
    title = request.form.get('title')

    # Generate short URL (you can use any method you prefer)
    short_url = generate_short_url(long_url)

    # Insert data into database
    cursor.execute("INSERT INTO urls (long_url, short_url, title, hits) VALUES (%s, %s, %s, %s)",
                   (long_url, short_url, title, 0))
    db.commit()

    return jsonify({'short_url': short_url})


@app.route('/search/<term>', methods=['GET'])
def search(term):
    cursor.execute("SELECT * FROM urls WHERE title LIKE %s", (f"%{term}%",))
    results = cursor.fetchall()
    return jsonify(results)


@app.route('/<short_url>', methods=['GET'])
def redirect_to_original(short_url):
    cursor.execute("SELECT * FROM urls WHERE short_url = %s", (short_url,))
    result = cursor.fetchone()

    if result:
        long_url = result[1]
        hits = result[4]

        # Update hit count
        cursor.execute("UPDATE urls SET hits = %s WHERE short_url = %s", (hits + 1, short_url))
        db.commit()

        return redirect(long_url)
    else:
        return "Short URL not found", 404


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='192.168.3.223', port=8080, debug=True)
