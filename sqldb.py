import psycopg2
from datetime import datetime

db = psycopg2.connect(
		host='dpg-ce05egarrk09es9d6tig-a',
		user='sreekanth',
		passwd='tNwdUg69effXSdwvY5KoqvgO5jFrQ4zG',
		database = 'mysql_cecx'
	)

cursor = db.cursor()
cursor.execute("CREATE TABLE if not exists UserIds (UserId VARCHAR(100))")

def add_user(user_id):
	user_id = "user"+str(user_id)
	cursor.execute("INSERT INTO UserIds (UserId) VALUES (%s)", (user_id,))
	cursor.execute("CREATE TABLE if not exists %s (id INT AUTO_INCREMENT PRIMARY KEY, TaskName VARCHAR(255),About VARCHAR(255),Goal INT,Streak INT,WeekStreak INT,DoneToday VARCHAR(3))"%(user_id))
	db.commit()
	return f"Added user with id : {user_id}"

def add_task(user_id,task_dict):
	user_id = "user"+str(user_id)
	#task_dict = {'TaskName':'name','About':"about",'Goal':7,'Streak':0,'WeekStreak':0,'DoneToday':'No'}
	

	keys = ','.join(task_dict.keys())
	values = list(task_dict.values())
	placeholders = ','.join(['%s']*len(values))

	cursor.execute("INSERT INTO %s (%s) VALUES (%s)" % (user_id,keys,placeholders),values)
	lastrow = cursor.lastrowid
	date_table_name = str(user_id)+str(lastrow)
	time_table_name = date_table_name+"time"
	cursor.execute("CREATE TABLE if not exists %s (Dates VARCHAR(50))"%(date_table_name))
	cursor.execute("CREATE TABLE if not exists %s (Time VARCHAR(10))"%(time_table_name))
	db.commit()
	return f"{user_id} Created new task"

def mark_task(user_id,row_id):
	user_id = "user"+str(user_id)
	cursor.execute("SELECT TaskName FROM %s WHERE id = %s" % (user_id,row_id))
	task_name = cursor.fetchone()[0]
	date_table_name = str(user_id)+str(task_name)

	cursor.execute("SELECT Streak,WeekStreak,DoneToday FROM %s WHERE id=%s" % (user_id,row_id))
	streak,weekstreak,donetoday = cursor.fetchone()
	if donetoday=="Yes":
		return "Task already completed"
	cursor.execute("UPDATE %s SET Streak=%s,WeekStreak=%s,DoneToday='Yes' WHERE id=%s" % (user_id,streak+1,weekstreak+1,row_id))
	time = datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')
	cursor.execute("INSERT INTO %s (Dates) VALUES (%s)" % (date_table_name,'%s'), (time,))
	db.commit()
	return f"Completed task {task_name}"

def check_user(user_id):
	user_id = "user"+str(user_id)
	cursor.execute("SELECT UserId FROM UserIds WHERE UserId='%s'" % (user_id))
	Ids = cursor.fetchall()
	if len(Ids)>0:
		return True
	return False

def check_task(user_id,task_name):
	user_id = "user"+str(user_id)
	cursor.execute("SELECT TaskName FROM %s WHERE TaskName='%s'" % (user_id,task_name))
	names = cursor.fetchall()
	if len(names)>0:
		return True
	return False

def get_tasks(user_id):
	user_id = "user"+str(user_id)
	cursor.execute("SELECT TaskName FROM %s" % (user_id))
	tasks = list(map(lambda x: x[0],cursor.fetchall()))
	return tasks

def get_streak(user_id,index):
	user_id = "user"+str(user_id)
	cursor.execute("SELECT Streak FROM %s WHERE id=%s" % (user_id,index))
	streak = cursor.fetchone()[0]
	return streak

def stop():
	db.close()