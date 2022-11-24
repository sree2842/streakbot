import mysql.connector
from datetime import datetime

db = mysql.connector.connect(
		host='localhost',
		user='root',
		passwd='alskdjfhg',
		database = 'UsersData'
	)

cursor = db.cursor()

def add_user(user_id):
	user_id = "user"+str(user_id)
	cursor.execute("INSERT INTO UserIds (UserId) VALUES (%s)", (user_id,))
	cursor.execute("CREATE TABLE %s (TaskName VARCHAR(255),About VARCHAR(255),Goal INT,Streak INT,WeekStreak INT,DoneToday VARCHAR(3))"%(user_id))
	db.commit()
	return f"Added user with id : {user_id}"

def add_task(user_id,task_dict):
	user_id = "user"+str(user_id)
	#task_dict = {'TaskName':'name','About':"about",'Goal':7,'Streak':0,'WeekStreak':0,'DoneToday':'No'}
	date_table_name = str(user_id)+str(task_dict['TaskName'])
	time_table_name = date_table_name+"time"

	keys = ','.join(task_dict.keys())
	values = list(task_dict.values())
	placeholders = ','.join(['%s']*len(values))

	cursor.execute("INSERT INTO %s (%s) VALUES (%s)" % (user_id,keys,placeholders),values)
	cursor.execute("CREATE TABLE %s (Dates VARCHAR(10))"%(date_table_name))
	cursor.execute("CREATE TABLE %s (Time VARCHAR(10))"%(time_table_name))
	db.commit()
	return f"{user_id} Created new task"

def mark_task(user_id,task_name):
	user_id = "user"+str(user_id)
	date_table_name = str(user_id)+str(task_name)
	time = datetime.now().strftime('%d/%m/%Y')
	cursor.execute("SELECT Goal,Streak,WeekStreak FROM %s WHERE TaskName=%s" % (user_id,task_name))
	goal,streak,weekstreak = map(lambda x:x+1,cursor.fetchall())
	cursor.execute("UPDATE %s SET Goal=%s,Streak=%s,WeekStreak=%s,DoneToday='Yes'" % (user_id,goal,streak,weekstreak))
	cursor.execute("INSERT INTO %s (Dates) VALUES (%s)" % (date_table_name), (time,))
	db.commit()
	return f"{user_id} done task"

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

def stop():
	db.close()