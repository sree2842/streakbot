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
import sqldb

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


updater = Updater('5712036028:AAF1VQryr9iPxbx8qcMI6dLkGwLB1_qCuFo')
ONE,TWO,THREE,STATE = map(chr,range(4))

HELPTEXT = inspect.cleandoc("""
    Use below Commands to communicate

    /newtask - Create new task
    /mytasks - Get all active tasks
    /streak - To get streak
    /done - To mark the task as completed
    """)
'''
    /todaystats - Status of today tasks
    /weekcharts - Your progress in the week
    /stop - To stop notifications
    """)
'''

TIMERS = (8,22)

states = {STATE:[]}

def start(update:Update, context:CallbackContext):
    chat_id = update.message.chat_id

    user_exists = sqldb.check_user(chat_id)

    if user_exists:
        text = "Hello existing user\nWelcome back"
    else:
        text = "Welcome to streak bot"
        #text += "\n\nThis bot helps you to stay committed to your tasks, it can calculate the streak for your tasks."
        text += "\n\n"+HELPTEXT
        text += "\n/help - Get list of available commands anytime"

        message = sqldb.add_user(chat_id)
        logger.info(message)

    update.message.reply_text(text)

    for hour in TIMERS:
        context.job_queue.run_daily(
                notify,
                time=time(hour,tzinfo=pytz.timezone('Asia/Kolkata')),
                #time = time(22,41,tzinfo=pytz.timezone('Asia/Kolkata')),
                context=context,
                name=str(chat_id)+str(hour),
            )

    context.job_queue.run_daily(
        reset,
        time=time(0,tzinfo=pytz.timezone('Asia/Kolkata')),
        context=context,
        name=str(chat_id)+"date",
        )

def get_tasks_name(tasks):
    names = []
    for task in tasks:
        names.append(task.name)

    return names

########## New task ###########

def add_task(update:Update, context:CallbackContext):
    chat_id = update.message.chat_id
    logger.info(f"Creating new task for user {chat_id}")

    context.user_data['task'] = {}
    context.bot.send_message(chat_id, 
        text = "Give a name to your task\nType 'cancel' anytime to cancel adding a task")

    return ONE

def take_name(update,context):
    '''
    Need to update if task exists ask user to modify are continue with out updating previous task
    '''
    chat_id = update.message.chat_id
    name = update.message.text
    logger.info(f"Got task name {name}")

    task_exists = sqldb.check_task(chat_id,name)
    if task_exists:
        update.message.reply_text("Task alreay exists. Updating the task.")
        return THREE
    else:
        context.user_data['task']['TaskName'] = name

    context.bot.send_message(chat_id,
        text=f'Describe few words about task {name}\nIt may help you to understand purpose of the task')

    return TWO

def take_about(update,context):
    chat_id = update.message.chat_id
    about = update.message.text
    logger.info(f"Got task about {about}")

    context.user_data['task']['About'] = about

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
    task_name = context.user_data['task']['TaskName']
    goal = 7

    try:
        if text=='Complete Week':
            goal = 7    
        else:
            goal = int(text[0])

        text = f'Successfully created task, you need to complete this task {goal} days every week'
        if goal==1:
            text = f'Successfully created task, you need to complete this task {goal} day every week'
    except:
        text = f'Invalid goal selection\nCreated task {task_name}, Task goal is set to {goal} days every week'
    
    logger.info(f"Set task goal {goal}")
    context.user_data['task']['Goal'] = goal
    streaks = {'Streak':0,'WeekStreak':0,'DoneToday':'No'}
    context.user_data['task'].update(streaks)

    task_dict = context.user_data['task']
    message = sqldb.add_task(chat_id,task_dict)

    update.message.reply_text(text=str(text),reply_markup=ReplyKeyboardRemove())
    logger.info(message)

    return ConversationHandler.END

def cancel(update:Update,context:CallbackContext):
    logger.info('Cancelled task Creation')
    update.message.reply_text(
        'Cancelled task Creation!',
    )

    del context.user_data['task']
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

############### Done & Streak #################
def get_keyboard(tasks,callback_func):
    states[STATE] = []
    buttons = []
    temp = []
    count = 0
    for index,task in enumerate(tasks):
        states[STATE].append(CallbackQueryHandler(callback_func, pattern=index))
        button = InlineKeyboardButton(text=task, callback_data=index)
        temp.append(button)
        if count:
            count = 0
            buttons.append(temp)
            temp=[]
            continue
        count+=1
    buttons.append(temp) 
    return buttons

def done(update,context):
    chat_id = update.message.chat_id
    context.user_data['chat_id'] = chat_id
    tasks = sqldb.get_tasks(chat_id)
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
    index = int(index)+1
    chat_id = context.user_data['chat_id']

    text = sqldb.mark_task(chat_id,index)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    logger.info(f'{chat_id} {text}')
    return ConversationHandler.END

def streak(update,context):
    chat_id = update.message.chat_id
    context.user_data['chat_id'] = chat_id
    tasks = sqldb.get_tasks(chat_id)
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
    index = int(index)+1
    chat_id = context.user_data['chat_id']

    streak = sqldb.get_streak(chat_id,index)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=streak)
    return ConversationHandler.END
##########################################



########## Get tasks ############
def get_tasks(update,context):
    chat_id = update.message.chat_id
    tasks = sqldb.get_tasks(chat_id)
    text = 'Active tasks : \n'
    if tasks:
        for i,task in enumerate(tasks):
            text+=str(i+1)+". "+task+"\n"
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

    dp.add_handler(CommandHandler("start",start,pass_args=True))

    task_handler = ConversationHandler(
        entry_points=[CommandHandler('newtask', add_task,pass_args=True)],
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
            CommandHandler('done', done,pass_args=True),
            CommandHandler('streak',streak,pass_args=True)
            ],
        states=states,
        fallbacks = [MessageHandler(Filters.regex('cancel'), cancel),
        ],
    )



    dp.add_handler(task_handler)
    dp.add_handler(done_handler)
    dp.add_handler(CommandHandler("mytasks",get_tasks,pass_args=True))
    dp.add_handler(CommandHandler("help",bot_help,pass_args=True))
    dp.add_handler(CommandHandler("weekcharts",week_stats,pass_args=True))
    dp.add_handler(CommandHandler("todaystats",day_stats,pass_args=True))
    dp.add_handler(CommandHandler("charts",charts,pass_args=True))
    #dp.add_handler(CommandHandler("stats",stats))
    dp.add_handler(CommandHandler("stop",stop,pass_args=True))

    updater.start_polling()
    updater.idle()
###############################################
if __name__ == '__main__':
    main()
