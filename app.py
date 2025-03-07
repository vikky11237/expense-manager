from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Add error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Add route for root URL
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('welcome'))
    return redirect(url_for('login'))

def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, budget REAL DEFAULT 0)''')
    # Create expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  amount REAL,
                  category TEXT,
                  description TEXT,
                  date TIMESTAMP,
                  FOREIGN KEY (username) REFERENCES users (username))''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Update login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('welcome'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')

# Update signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
        finally:
            conn.close()
    return render_template('signup.html')

# Update welcome route
@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    
    # Get user's budget with proper error handling
    c.execute('SELECT budget FROM users WHERE username = ?', (session['username'],))
    result = c.fetchone()
    budget = result[0] if result else 0
    
    # Get user's expenses
    c.execute('SELECT * FROM expenses WHERE username = ? ORDER BY date DESC', (session['username'],))
    expenses = [{'amount': row[2], 'category': row[3], 'description': row[4]} for row in c.fetchall()]
    
    # Calculate totals
    total_expenses = sum(float(expense['amount']) for expense in expenses)
    remaining_budget = budget - total_expenses if budget > 0 else 0
    budget_percentage = (remaining_budget / budget * 100) if budget > 0 else 0
    
    # Calculate category totals
    c.execute('''SELECT category, SUM(amount) FROM expenses 
                 WHERE username = ? GROUP BY category''', (session['username'],))
    category_totals = dict(c.fetchall() or {})
    
    conn.close()
    
    return render_template('welcome.html',
                         username=session['username'],
                         expenses=expenses,
                         total_expenses=total_expenses,
                         category_totals=category_totals,
                         budget=budget,
                         remaining_budget=remaining_budget,
                         budget_percentage=budget_percentage)

# Update add_expense route
@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    amount = request.form.get('amount')
    category = request.form.get('category')
    description = request.form.get('description')
    
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''INSERT INTO expenses (username, amount, category, description, date)
                 VALUES (?, ?, ?, ?, ?)''', 
              (session['username'], amount, category, description, datetime.now()))
    conn.commit()
    conn.close()
    
    flash(f'Expense added: ${amount} for {category}', 'success')
    return redirect(url_for('welcome'))

# Update set_budget route
@app.route('/set_budget', methods=['POST'])
def set_budget():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    budget = request.form.get('budget')
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('UPDATE users SET budget = ? WHERE username = ?', (budget, session['username']))
    conn.commit()
    conn.close()
    
    flash('Budget updated successfully!', 'success')
    return redirect(url_for('welcome'))

# Update delete_expense route
@app.route('/delete_expense/<int:index>')
def delete_expense(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id = ? AND username = ?', (index, session['username']))
    conn.commit()
    conn.close()
    
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('welcome'))
# Add after the login route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)