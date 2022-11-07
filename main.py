#from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
)
from datetime import datetime,time
import logging,pytz
from operator import itemgetter
import inspect

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


updater = Updater('5712036028:AAF1VQryr9iPxbx8qcMI6dLkGwLB1_qCuFo')
ONE,TWO,THREE,STATE = map(chr,range(4))

read_data = open('data.txt','r')
data_lines = read_data.readlines()     #skip first line
data = [d.split("    ") for d in data_lines]

CHAT_IDS = [line[0] for line in data]
TASK_DATA = []
task_details = ["name","about","goal","streak","week_streak","done_today"]
for line in data:
    user_tasks = []
    temp = line[1]
    tasks = temp.split("   ")
    task_data = {}
    for task in tasks:
        task = task.split("  ")
        if len(task)<7:
            task.append("")
            dates_list = []
        else:
            dates_list = task[-1].split(",")
        task_data = dict(zip(task_details,task[:-1]))
        task_data['dates'] = dates_list
        #task_data['streak'] = int(task_data['streak'])
        #task_data['week_streak'] = int(task_data['week_streak'])
        user_tasks.append(task_data)
    TASK_DATA.append(user_tasks)
read_data.close()
print(TASK_DATA)

HELPTEXT = inspect.cleandoc("""
    Use below Commands to communicate

    /newtask - Create new task
    /mytasks - Get all active tasks
    /streak - To get streak
    /done - To mark the task as completed
    /todaystats - Status of today tasks
    /weekcharts - Your progress in the week
    /stop - To stop notifications
    """)

def update_datafile():
    global CHAT_IDS,TASK_DATA
    write_data = open('data.txt','w')
    #print(CHAT_IDS,TASK_DATA)
    file_lines = []
    for ind in range(len(CHAT_IDS)):
        line = str(CHAT_IDS[ind])+" "
        text = ""
        for task in TASK_DATA[ind]:
            text+="   "
            values = list(task.values())
            print(values)
            if values[-1]==[]:
                values.pop(-1)
                text += "  ".join(values)
            else:
                text += "  ".join(values[:-1])
                dates = ",".join(values[-1])
                text += "  "+dates
            
            print(text)
        line += text
        file_lines.append(line)
    print(file_lines)
    write_data.writelines(file_lines)
    write_data.close()
    print("written data")


states = {STATE:[]}
class Task:
    def __init__(self):
        self.name = 'Untitled task'
        self.about = "Task"
        self.goal = 7
        self.streak = 0
        self.dates = []
        self.week_streak = 0
        self.done_today = "No"

    def done(self):
        today = datetime.now().strftime('%d/%m/%Y')
        self.streak+=1
        self.week_streak+=1
        self.done_today = "Yes"
        self.dates.append(today)

    def streak_details(self):
        text = '\n'
        text += f"Streak - {str(self.streak)}"
        text+=f"\nDone today : {str(self.done_today)}"
        return text

    def set_name(self,name):
        self.name = name

    def get_streak(self):
        return self.streak

    def get_streak_calender(self):
        for day in self.dates:
            return day

def start(update:Update, context:CallbackContext):
    context.user_data['tasks'] = []
    chat_id = update.message.chat_id
    context.user_data['chat_id']=chat_id
    print(CHAT_IDS,TASK_DATA)
    if str(chat_id) in CHAT_IDS:
        text = "Hello existing user\nYour data is been Successfully loaded"
        ind = CHAT_IDS.index(str(chat_id))
        tasks = TASK_DATA[ind]
        for t in tasks:
            task = Task()
            task.name = t["name"]
            task.about = t["about"]
            task.streak = int(t["streak"])
            task.week_streak = int(t["week_streak"])    
            task.done_today = t["done_today"]
            task.dates = t["dates"]
            context.user_data['tasks'].append(task)
    else:
        text = "Hello welcome to streak bot"
        text += "\n\nThis bot helps you to stay committed to your tasks, it can calculate the streak for your tasks."
        text += "\n\n"+HELPTEXT
        text += "\n/help - Get list of available commands anytime"
    update.message.reply_text(text)

    now = datetime.now()
    context.job_queue.run_daily(
        notify,
        time=time(int(now.strftime('%H')),int(now.strftime('%M')),tzinfo=pytz.timezone('Asia/Kolkata')),
        #time = time(22,41,tzinfo=pytz.timezone('Asia/Kolkata')),
        #30,
        context=context,
        name=str(chat_id),
        )
    context.job_queue.run_daily(
        reset,
        time=time(0,tzinfo=pytz.timezone('Asia/Kolkata')),
        context=context,
        name=str(chat_id)+"date",
        )
########## New task ###########
def get_tasks_name(tasks):
    names = []
    for task in tasks:
        names.append(task.name)

    return names

def add_task(update:Update, context:CallbackContext):
    chat_id = update.message.chat_id

    task = Task()
    context.user_data['tasks'].append(task)
    context.bot.send_message(chat_id, 
        text = "Give a name to your task\nType 'cancel' anytime to cancel adding a task")
    return ONE

def take_name(update,context):
    chat_id = update.message.chat_id
    name = update.message.text
    tasks = context.user_data['tasks']
    if name in get_tasks_name(tasks):
        update.message.reply_text("Task alreay exists. Updating the task.")
        return THREE
    else:
        context.user_data['tasks'][-1].name = name
    context.bot.send_message(chat_id,
        text=f'Describe few words about task {name}\nIt may help you to understand purpose of the task')

    return TWO

def take_about(update,context):
    chat_id = update.message.chat_id
    about = update.message.text
    context.user_data['tasks'][-1].about = about

    reply_keyboard = [['1 Day', '2 Days'], ['3 Days', '4 Days'], ['5 Days', '6 Days'], ['Complete Week']]
    context.bot.send_message(chat_id,
        text = 'Select a streak goal to stay Commited.',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Days/Week'
        ))

    return THREE

def streak_goal(update,context):
    chat_id = update.message.chat_id
    text = update.message.text
    task = context.user_data['tasks'][-1]
    goal = task.goal
    try:
        if text=='Complete Week':
            goal = 7
        else:
            goal = int(text[0])
        text = f'Successfully created task, you will be notified {goal} days every week'
    except:
        text = f'Invalid goal selection\nCreated task {task.name}, you will be notified {goal} days every week'
    task.goal = goal
    #print(text)
    update.message.reply_text(text=str(text),reply_markup=ReplyKeyboardRemove())

    task_details = {"name":task.name,
                "about":task.about,
                "goal":str(task.goal),
                "streak":str(task.streak),
                "week_streak":str(task.week_streak),
                "done_today":str(task.done_today),
                "dates":task.dates
                }

    if str(chat_id) not in CHAT_IDS:
        CHAT_IDS.append(str(chat_id))
        TASK_DATA.append([task_details])
    else:
        ind = CHAT_IDS.index(str(chat_id))
        TASK_DATA[ind].append(task_details)

    update_datafile()
    return ConversationHandler.END

def cancel(update:Update,context:CallbackContext):
    update.message.reply_text(
        'Cancelled task Creation!',
    )
    #task = context.user_data['tasks'][-1]
    del context.user_data['tasks'][-1]
    return ConversationHandler.END
################################


######## Tasks stats #############
def today_stats(tasks):
    board = list(range(len(tasks)+1))
    space = len(max(get_tasks_name(tasks)))
    board[0] = f'{"Task Name":<15}{"Streak":^{space}}{"Status":>15}'
    text = ''
    start,end = 1,-1
    if len(board)==1:
        return "No tasks created yet use /newtask to create a task"
    for task in tasks:
        task_name = task.name
        streak = task.streak
        if task.done_today=="Yes":
            board[end] = f'{task_name:<15}{streak:>{space}}{"Completed":>20}'
            end-=1
        else:
            board[start] = f'{task_name:<15}{streak:>{space}}{"Pending!":>20}'
            start+=1
        
    temp = False
    if start == 1:
        temp = True

    board = "\n".join(board)
    text+=board
    if temp:
        text+="\n\nCongrats you've completed today tasks"
    else:
        text+="\n\nComplete the pending tasks"
    return text

def day_stats(update,context):
    text="Today Stats...\n\n"
    tasks = context.user_data['tasks']
    text += today_stats(tasks)
    update.message.reply_text(text=text)

def notify(context):
    job = context.job
    chat_id = int(job.name)
    context = job.context
    text="Today stats...\n"
    tasks = context.user_data['tasks']
    text += today_stats(tasks)
    context.bot.send_message(chat_id,text=text)

def reset(context):
    print("Called reset")
    job = context.job
    context = job.context
    chat_id = int(job.name[:-4])
    tasks = context.user_data['tasks']
    for task in tasks:
        task.done_today = "No"

    ind = CHAT_IDS.index(str(chat_id))
    user_tasks = TASK_DATA[ind]
    for t in user_tasks:
        t['done_today'] = str(task.done_today)
    update_datafile()

def week_board(tasks):
    space = len(max(get_tasks_name(tasks)))
    board = [f'{"Task Name":<15}{"Goal":^{space}}{"Streak":>15}']
    for task in tasks:
        task_name = task.name
        week_goal = str(task.goal)
        week_streak = str(task.week_streak)
        row = f'{task_name:<15}{week_goal:>{space}}{week_streak:>20}'
        board.append(row)
    if len(board)==1:
        return "\nNo tasks created yet use /newtask to create a task"
    board = "\n".join(board)
    return board

def week_stats(update,context):
    chat_id = update.message.chat_id
    text="week charts...\n"
    tasks = context.user_data['tasks']
    status = week_board(tasks)    
    text+=status
    context.bot.send_message(chat_id,text=text)

def charts(update,context):
    chat_id = update.message.chat_id
    text="charts...\n"
    tasks = context.user_data['tasks']
    status = week_board(tasks)
    text+=status
    context.bot.send_message(chat_id,text=text)
#################################

############### Keyboards #################
def get_keyboard(tasks,callback_func):
    states[STATE] = []
    buttons = []
    temp = []
    count = 0
    for index,task in enumerate(tasks):
        states[STATE].append(CallbackQueryHandler(callback_func, pattern=index))
        button = InlineKeyboardButton(text=task.name, callback_data=index)
        temp.append(button)
        if count:
            count = 0
            buttons.append(temp)
            temp=[]
        count+=1
    buttons.append(temp)
    return buttons

def done(update,context):
    tasks = context.user_data['tasks']
    if tasks:
        text = "Pick one from below"
        buttons = get_keyboard(tasks,mark_done)
        keyboard = InlineKeyboardMarkup(buttons)
    else:
        text = "No tasks created!"
        update.message.reply_text(text)
        return ConversationHandler.END
    update.message.reply_text(text,reply_markup=keyboard)
    return STATE

def mark_done(update,context):
    index = update.callback_query.data
    tasks = context.user_data['tasks'] 
    task = tasks[int(index)]
    chat_id = context.user_data['chat_id']
    stats = today_stats(tasks)
    if task.done_today=="Yes":
        text="you've already completed this task"
    else:
        task.done()
        text=f"Completed task {task.name}"
        ind = CHAT_IDS.index(str(chat_id))
        user_tasks = TASK_DATA[ind]
        for t in user_tasks:
            name = t["name"]
            if task.name == name:
                t['streak'] = str(task.streak)
                t['week_streak'] =str(task.week_streak)
                t['done_today'] = str(task.done_today)
                t['dates'] = task.dates
        update_datafile()
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    #update.message.reply_text(stats)
    return ConversationHandler.END

def streak(update,context):
    tasks = context.user_data['tasks']
    if tasks:
        text = "Pick one from below"
        buttons = get_keyboard(tasks,get_streak)
        keyboard = InlineKeyboardMarkup(buttons)
    else:
        text = "No tasks created!"
        update.message.reply_text(text)
        return ConversationHandler.END
    update.message.reply_text(text,reply_markup=keyboard)
    return STATE

def get_streak(update,context):
    index = update.callback_query.data
    task = context.user_data['tasks'][int(index)]
    streak = task.streak_details()
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=streak)
    return ConversationHandler.END
##########################################



########## Get tasks ############
def get_tasks(update,context):
    tasks = context.user_data['tasks']
    text = 'Active tasks : \n'
    if tasks:
        for i in range(len(tasks)):
            text+=str(i+1)+". "+tasks[i].name+"\n"
    else:
        text = 'No tasks assigned yet. Use /newtask to create a task'
    update.message.reply_text(text)
#################################



############## Basic Commands ##################
def bot_help(update:Update, context:CallbackContext):
    text=HELPTEXT
    update.message.reply_text(text)

def stop(update,context):
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name(str(name))
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
        text = "No more notfications"
    else:
        text = "You already stopped the notifications"
    update.message.reply_text(text)

def main():
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start",start))

    task_handler = ConversationHandler(
        entry_points=[CommandHandler('newtask', add_task)],
        states={
            ONE: [MessageHandler(Filters.text & ~Filters.regex('cancel'), take_name)],
            TWO: [MessageHandler(Filters.text & ~Filters.regex('cancel'), take_about)],
            THREE: [MessageHandler(Filters.text & ~Filters.regex('cancel'), streak_goal),
            ],
        },
        fallbacks = [MessageHandler(Filters.regex('cancel'), cancel),
        ],
    )

    done_handler = ConversationHandler(
        entry_points=[
            CommandHandler('done', done),
            CommandHandler('streak',streak)
            ],
        states=states,
        fallbacks = [MessageHandler(Filters.regex('cancel'), cancel),
        ],
    )



    dp.add_handler(task_handler)
    dp.add_handler(done_handler)
    dp.add_handler(CommandHandler("mytasks",get_tasks))
    dp.add_handler(CommandHandler("help",bot_help))
    dp.add_handler(CommandHandler("weekcharts",week_stats))
    dp.add_handler(CommandHandler("todaystats",day_stats))
    dp.add_handler(CommandHandler("charts",charts))
    #dp.add_handler(CommandHandler("stats",stats))
    dp.add_handler(CommandHandler("stop",stop))

    updater.start_polling()
    updater.idle()
###############################################
if __name__ == '__main__':
    main()