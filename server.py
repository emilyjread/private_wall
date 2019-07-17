from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL

app = Flask(__name__)
app.secret_key= "so secret"
import humanize
import datetime

import re
EMAIL_REGEX= re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
PW_REGEX= re.compile(r'^[a-zA-Z.+_-]+[0-9._-]+$')

from flask_bcrypt import Bcrypt        
bcrypt = Bcrypt(app)

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/create", methods=["POST"])
def create():
	valid=True

	if request.form['pw']!=request.form['pwconf']:
		flash("Passwords do not match!")
		valid=False
	if len(request.form["username"])<5:
		flash("username must be at least 5 characters")
		valid=False
	if len(request.form["fname"])<2:
		flash("Please enter a first name")
		valid=False
	if len(request.form["fname"])<2:
		flash("Please enter a last name")
		valid=False
	if not EMAIL_REGEX.match(request.form["email"]):
		flash("Please enter valid email")
		valid=False
	if not PW_REGEX.match(request.form['pw']):
		flash("Passwords must be at least 8 characters and contain at least one letter and one number")
		valid=False

	if valid==False:
		return redirect("/")
	if valid==True:
		pw_hash = bcrypt.generate_password_hash(request.form['pw'])

		mysql=connectToMySQL("private_wall_two")
		query= "INSERT INTO users (username, fname, lname, email, pw, created_at, updated_at) VALUES(%(un)s, %(fn)s, %(ln)s, %(em)s, %(pw)s, now(), now())"
		data= {
			'un':request.form["username"], 
			'fn':request.form["fname"], 
			'ln':request.form["lname"], 
			'em':request.form["email"], 
			'pw':pw_hash
		}
		result=mysql.query_db(query, data)

		session['userid'] = result

		return redirect("/wall")

@app.route("/login", methods=["POST"])
def login():
	mysql=connectToMySQL("private_wall_two")
	query=(f"SELECT * FROM users where email= %(email)s")
	data={
	'email': request.form["email"]
	}
	result=mysql.query_db(query, data)
	session['user']=result
	if len(result)>0:
		if bcrypt.check_password_hash(result[0]['pw'], request.form['pw']):
			session['userid'] = result[0]['id']
			return redirect("/wall")
	flash("not valid login credentials")
	return redirect("/")

@app.route("/wall")
def wall():
	if 'userid' in session:
		mysql=connectToMySQL("private_wall_two")
		query= f"SELECT username from users where id={session['userid']}"
		user_name=mysql.query_db(query)

		mysql=connectToMySQL("private_wall_two")
		query=(f"SELECT posts.created_at, sender.fname AS sender, posts.content AS content, user_id AS sender, recipient.fname AS recipient_name, posts.id FROM posts JOIN users AS sender ON sender.id= posts.user_id JOIN users AS recipient ON recipient.id= posts.recipient_id WHERE posts.recipient_id={session['userid']} order by posts.id desc ")
		posts=mysql.query_db(query)
		count=len(posts)

		mysql=connectToMySQL("private_wall_two")
		query=("SELECT fname, id from users order by fname")
		users=mysql.query_db(query)

		mysql=connectToMySQL("private_wall_two")
		query=(f"SELECT posts.id from posts where posts.user_id= {session['userid']}")
		sent=mysql.query_db(query)
		sent_count=len(sent)
		


		return render_template("wall.html", user=user_name, posts=posts, users=users, count=count, sent=sent_count)
	else:
		flash("Please log in again")
		return redirect("/")

@app.route("/create_message", methods=["post"])
def createmessage():

	user= session['userid']
	mysql=connectToMySQL("private_wall_two")
	query= "INSERT INTO posts (content, user_id, recipient_id, created_at, updated_at) VALUES(%(content)s, %(sender_id)s, %(rec_id)s, now(), now())"
	data= {
		'content':request.form["content"], 
		'sender_id': session['userid'], 
		'rec_id': request.form["recipient"]

		}

	mysql.query_db(query, data)
	return redirect("/wall")

@app.route("/delete/<id>")
def delete(id):
	mysql=connectToMySQL("private_wall_two")
	query= mysql.query_db(f"DELETE FROM posts where posts.id={id}")
	return redirect("/wall")

@app.route("/logout")
def logout():
	session.clear()
	return redirect("/")





if __name__ == "__main__":
	app.run(debug=True)