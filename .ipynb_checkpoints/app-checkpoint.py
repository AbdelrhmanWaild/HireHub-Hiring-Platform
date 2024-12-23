from flask import Flask, render_template, request, redirect, session
import pandas as pd
import os


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load or initialize DataFrames
if not os.path.exists('data'):
    os.makedirs('data')

candidates_file = 'data/candidates.csv'
companies_file = 'data/companies.csv'
jobs_file = 'data/jobs.csv'
applications_file = 'data/applications.csv'

candidates = pd.read_csv(candidates_file) if os.path.exists(candidates_file) else pd.DataFrame(columns=['Name', 'Email', 'Password', 'Phone'])
companies = pd.read_csv(companies_file) if os.path.exists(companies_file) else pd.DataFrame(columns=['Name', 'Email', 'Password', 'Phone'])
jobs = pd.read_csv(jobs_file) if os.path.exists(jobs_file) else pd.DataFrame(columns=['Company', 'Title', 'Description', 'Qualifications', 'Responsibilities', 'Salary', 'Location'])
applications = pd.read_csv(applications_file) if os.path.exists(applications_file) else pd.DataFrame(columns=['Candidate', 'Job', 'Status'])

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global candidates, companies
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Authenticate user
        user = candidates[(candidates['Email'] == email) & (candidates['Password'] == password)]
        company = companies[(companies['Email'] == email) & (companies['Password'] == password)]
        
        if not user.empty:
            session['user'] = email
            session['type'] = 'candidate'
            return redirect('/candidate/dashboard')
        elif not company.empty:
            session['user'] = email
            session['type'] = 'company'
            return redirect('/company/dashboard')
        else:
            return "Invalid credentials or user does not exist."
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    global candidates, companies
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        user_type = request.form['type']
        
        if user_type == 'candidate':
            new_entry = pd.DataFrame([[name, email, password, phone]], columns=candidates.columns)
            candidates = pd.concat([candidates, new_entry], ignore_index=True)
            candidates.to_csv(candidates_file, index=False)
        elif user_type == 'company':
            new_entry = pd.DataFrame([[name, email, password, phone]], columns=companies.columns)
            companies = pd.concat([companies, new_entry], ignore_index=True)
            companies.to_csv(companies_file, index=False)
        
        return redirect('/login')
    return render_template('signup.html')

@app.route('/candidate/dashboard')
def candidate_dashboard():
    if 'user' in session and session['type'] == 'candidate':
        email = session['user']
        candidate = candidates[candidates['Email'] == email].iloc[0]
        
        # Application statistics
        applied_jobs = applications[applications['Candidate'] == email]
        accepted = applied_jobs[applied_jobs['Status'] == 'Accepted']
        refused = applied_jobs[applied_jobs['Status'] == 'Refused']
        
        return render_template(
            'candidate_dashboard.html',
            name=candidate['Name'],
            jobs_applied=len(applied_jobs),
            jobs_accepted=len(accepted),
            jobs_refused=len(refused)
        )
    return redirect('/login')

@app.route('/company/dashboard')
def company_dashboard():
    if 'user' in session and session['type'] == 'company':
        return render_template('company_dashboard.html')
    return redirect('/login')

@app.route('/jobs')
def job_list():
    jobs_list = jobs.to_dict(orient='records')
    return render_template('job_list.html', jobs=jobs_list)

@app.route('/company/post-job', methods=['GET', 'POST'])
def post_job():
    if request.method == 'POST':
        global jobs
        new_job = {
            'Company': session['user'],
            'Title': request.form['title'],
            'Description': request.form['description'],
            'Qualifications': request.form['qualifications'],
            'Responsibilities': request.form['responsibilities'],
            'Salary': request.form['salary'],
            'Location': request.form['location']
        }
        jobs = pd.concat([jobs, pd.DataFrame([new_job])], ignore_index=True)
        jobs.to_csv(jobs_file, index=False)
        return redirect('/company/dashboard')
    return render_template('job_posting.html')


@app.route('/candidate/profile')
def candidate_profile():
    if 'user' in session and session['type'] == 'candidate':
        email = session['user']
        candidate = candidates[candidates['Email'] == email].iloc[0]
        return render_template(
            'candidate_profile.html',
            name=candidate['Name'],
            email=candidate['Email'],
            phone=candidate['Phone'],
            resume=candidate.get('Resume', None)
        )
    return redirect('/login')

@app.route('/candidate/upload-cv', methods=['POST'])
def upload_cv():
    if 'user' in session and session['type'] == 'candidate':
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename.endswith(('.pdf', '.doc', '.docx')):
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename))
                # Update DataFrame
                email = session['user']
                candidates.loc[candidates['Email'] == email, 'Resume'] = filename
                candidates.to_csv('data/candidates.csv', index=False)
                return redirect('/candidate/profile')
    return "Invalid request", 400

@app.route('/jobs')
def job_list():
    jobs_dict = jobs.to_dict(orient='records')
    return render_template('job_list.html', jobs=jobs_dict)


from flask_uploads import configure_uploads, UploadSet, DOCUMENTS

docs = UploadSet('docs', DOCUMENTS)

app.config['UPLOADED_DOCS_DEST'] = 'static/uploads'
configure_uploads(app, docs)

@app.route('/candidate/upload-cv', methods=['POST'])
def upload_cv():
    if 'user' in session and session['type'] == 'candidate':
        if 'resume' in request.files:
            file = request.files['resume']
            filename = docs.save(file)
            email = session['user']
            candidates.loc[candidates['Email'] == email, 'Resume'] = filename
            candidates.to_csv('data/candidates.csv', index=False)
            return redirect('/candidate/profile')
    return "Invalid request", 400

@app.route('/apply/<int:job_id>', methods=['POST'])
def apply_for_job(job_id):
    if 'user' in session and session['type'] == 'candidate':
        global applications
        email = session['user']
        application = {
            'Candidate': email,
            'JobID': job_id,
            'Status': 'Pending'
        }
        applications = pd.concat([applications, pd.DataFrame([application])], ignore_index=True)
        applications.to_csv('data/applications.csv', index=False)
        return redirect('/jobs')
    return redirect('/login')

# Additional routes for dashboards, job posting, job listing, and profiles will follow.
if __name__ == '__main__':
    app.run(debug=True)
