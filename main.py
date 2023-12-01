from flask import Flask
from flask import render_template, redirect, url_for, request, session
import sqlite3
import sqlite3 as sql
import mariadb
import bcrypt
import uuid
from datetime import datetime

def get_current_date():
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y-%m-%d")
    return formatted_date

app = Flask(__name__)
app.secret_key = 'my_secret_key'    #for flask session

def dbconnect():
    mariadb_connection = mariadb.connect(
        user= "root",
        password= "PASSWORD123",
        host= "127.0.0.1",
        port= 3306,
        database= "db2"
    )
    return mariadb_connection

#############
#BASIC PAGES#
#############
@app.route("/")                     #default route
def home():
    return render_template('home.html')     #open home page

@app.route('/login/')                       #open login page
def login():
    #check session
    if 'email' not in session:
        return render_template('login.html')
    else:
        msg = "Already logged in!"
        return render_template("result.html", msg=msg)

################
#AUTHENTICATION#
################    
@app.route('/logging/', methods=['POST', 'GET'])
def logging():
    if request.method=='POST':                                                      #if form is submitted
        email=request.form['email']                                             #take the email and password entered and assign it to variables to check
        password=request.form['password']
            
        con = dbconnect()                              #establish the connection
        cur = con.cursor()                                                  #prepare for query
        cur.execute(f"SELECT password FROM users WHERE email='{email}'")    #grabs the password with the condition that the entered email matches an email in the database
                
        result = cur.fetchone()                                             #fetch the first row, which in this case just fetches the row that was selected
        if not result:                                                      #if it's empty, which it will be if it couldn't fetch anything...
            msg = "Login Failed, your email is incorrect!"
            return render_template("result.html", msg=msg)
        stored_password = result[0]                                         #go fetch the hashed password from the row
                
        #Authenticate the user by comparing the encoded (hashed) password to the stored hash in the database
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):       #bcrypt.checkpw() automatically extracts the salt from the stored password and uses it to hash the password for comparison, wasting 6 hours of my time as I angrily and futilely try to extract the salt manually                                             
            session['email'] = email                                        #session key
            cur.execute(f"SELECT role FROM users WHERE email='{email}'")
            user_role = cur.fetchone()[0]
            if user_role:
                session['role'] = user_role
            else:
                session['role'] = 'USER'
            msg = "Welcome"
            return render_template("result.html", msg=msg)
        else:
            msg = "Login Failed, your password is incorrect!"
            return render_template("result.html", msg=msg)
                

###################
#SELF PROVISIONING# 
###################
@app.route('/register/')                                                            #opening the reigster page, which has a form for entering email and password
def register():
        return render_template('register.html')

@app.route('/adduser/', methods=['POST', 'GET'])                                    #directory to self provision yourself
def adduser():
    
    if request.method == 'POST':
        
        email = request.form['email']                                           #takes the email and password from the form
        password = request.form['password']

        #hashing
        bytes = password.encode('utf-8')                    #turn the plaintext password into a bytes format so I can use it with hashpw
        salt = bcrypt.gensalt()                             #generate a salt
        password=bcrypt.hashpw(bytes, salt)                 #hash it with bytes and salt
        ########
            
        con = dbconnect()
        cur = con.cursor()
        cur.execute ("INSERT INTO users (email, password, salt) VALUES (?, ?, ?)", (email, password, salt))         #insert the email, hashed password, and salt into the database
        con.commit()
        msg = "User successfully added"
            
        con.close()
        return render_template("result.html", msg=msg)

########
#LOGOUT#
########
@app.route('/logout/')
def logout():
    if 'email' not in session:
        msg = "You're not logged in!"
        return render_template("result.html", msg=msg)
    else:
        session.pop('email', None)
        msg = "Logged out!"
        return render_template("result.html", msg=msg)
    
#######################################################
#                   JOB PORTAL                        #
#######################################################
# -Has all jobs listed, date posted, and closing date #
# -Button for adding jobs                             #
# -Can apply to jobs if you're an applicant           #
# -Can display the description of the job             #
#######################################################
@app.route('/jobportal/')                   #Lists jobs, date posted, and closing date
def jobportal():
    if 'email' not in session:              #check session
        return redirect(url_for('login'))
    con=dbconnect()         
    #con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("select * from jobs")      
    rows = cur.fetchall()
    return render_template('jobportal.html', rows = rows)   #Displays all jobs and components from jobs table

@app.route('/preaddjob/')            #Check if the user is a manager before they're allowed to add a job
def preaddjob():
    if 'email' not in session:
        return redirect(url_for('login'))
    email=session['email']
    con=dbconnect()
    cur = con.cursor()
    cur.execute(f"SELECT role FROM users WHERE email='{email}'")
    user_role = cur.fetchone()[0]
    if(user_role!='MANAGER'):
        msg = "You're not a manager"
        con.close()
        return render_template("result.html", msg=msg)
    return render_template('addjob.html')

@app.route('/addjob/', methods=['POST', 'GET'])                      #Add jobs with parameters job, description, postdate, enddate
def addjob():
    if 'email' not in session:
        return redirect(url_for('login'))

    #con = None

    if request.method == 'POST':
        
        job_name = request.form['job']
        description = request.form['description']
        postdate = request.form['postdate']
        enddate = request.form['enddate']

        con = dbconnect()
        cur = con.cursor()
        cur.execute("INSERT INTO jobs (job_name, description, postdate, enddate) VALUES (?, ?, ?, ?)", (job_name, description, postdate, enddate))
        con.commit()
        msg = "Job successfully added"
        
        con.close()
        return render_template("result.html", msg=msg)

##############################################################
#                 APPLICATION FUNCTIONS                      #
##############################################################
# -User can apply for jobs.                                  #
# -User clicks link to apply and types of application msg.   #
# -Manager can see applicants by clicking on link.           #
# -Manager can manage application (reject/accept)            #
# -User can view their application status                    #
##############################################################

@app.route('/apply/<job_name>/form', methods=['GET'])
def application_form(job_name):
    return render_template('apply.html', job_name=job_name)

@app.route('/apply/<job_name>/submit', methods=['POST'])
def apply(job_name):
    if 'email' not in session:
        return redirect(url_for('login'))
    current_date = get_current_date()
    email=session['email']
    con=dbconnect()
    cur=con.cursor()
    cur.execute(f"SELECT user_id FROM users WHERE email='{email}'")
    user_id = cur.fetchone()[0]
    cur.execute(f"SELECT job_id FROM jobs WHERE job_name='{job_name}'")
    job_id = cur.fetchone()[0]
    # Entering form info
    if request.method == 'POST':
        message = request.form['message']
    cur.execute("INSERT INTO applications (job_id, user_id, application_date, message) VALUES (?, ?, ?, ?)", (job_id, user_id, current_date, message))
    con.commit()
    con.close()
    msg = "Application sent!"
    return render_template("result.html", msg=msg)

@app.route('/view_applications/<job_name>')
def check_applications(job_name):
    if 'email' not in session:              #check session
        return redirect(url_for('login'))
    con=dbconnect()
    cur=con.cursor()
    cur.execute(f"SELECT job_id FROM jobs WHERE job_name='{job_name}'")
    job_id = cur.fetchone()[0]
    
    cur.execute("""
                SELECT a.application_date, a.message, a.status, u.email, a.user_id, a.job_id
                FROM applications a
                JOIN users u on a.user_id = u.user_id
                WHERE a.job_id = ?
                """, (job_id,))

    rows = cur.fetchall()
    con.close()
    return render_template("applications.html", rows=rows, job_name=job_name)

@app.route('/view_applicant/<user_id>/<job_id>')
def view_applicant(job_id, user_id):
    if 'email' not in session:              #check session
        return redirect(url_for('login'))
    con=dbconnect()
    cur=con.cursor()
    cur.execute("SELECT message FROM applications WHERE job_id = ? AND user_id = ?", (job_id, user_id))
    message = cur.fetchone()[0]
    cur.execute("SELECT application_date FROM applications WHERE job_id = ? AND user_id = ?", (job_id, user_id))
    application_date = cur.fetchone()[0]
    

    cur.execute("SELECT job_name FROM jobs WHERE job_id = ?", (job_id,))
    job_name = cur.fetchone()[0]
    cur.execute("SELECT email FROM users WHERE user_id = ?", (user_id,))
    user_email = cur.fetchone()[0]
    con.close()
    return render_template("applicant.html", message=message, application_date=application_date, job_name=job_name, user_email=user_email, job_id=job_id, user_id=user_id)

@app.route('/process_application/<job_id>/<user_id>', methods=['POST'])
def process_application(job_id, user_id):
    if 'email' not in session:              #check session
        return redirect(url_for('login'))
    con=dbconnect()
    cur=con.cursor()
    decision = request.form['decision'] + "ed"
    cur.execute("UPDATE applications SET status = ? WHERE job_id = ? AND user_id = ?", (decision, job_id, user_id))
    con.commit()
    con.close()
    msg = decision
    return render_template("result.html", msg=msg)

@app.route('/view_user_app/')
def view_user_app():
    if 'email' not in session:              #check session
        return redirect(url_for('login'))
    email=session['email']
    con=dbconnect()
    cur=con.cursor()
    cur.execute("SELECT user_id FROM users WHERE email = ?", (email,))
    user_id = cur.fetchone()[0]
    cur.execute(""" 
                SELECT j.job_name, a.status
                FROM applications a
                JOIN jobs j on a.job_id = j.job_id
                WHERE a.user_id = ?
                """, (user_id,))
    rows = cur.fetchall()
    con.close()
    return render_template("userappstatus.html", rows=rows)
    
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
