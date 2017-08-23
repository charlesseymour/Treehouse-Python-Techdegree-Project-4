import sys
import os
import datetime

from peewee import *

welcome = '\n***Welcome to Work Database for Python Command Line***\n'

db = SqliteDatabase('tasks.db')


class Task(Model):
    employee = CharField(max_length=100)
    name = CharField(max_length=100)
    time = IntegerField(default=0)
    date = DateField(default=datetime.date.today())
    notes = TextField()

    class Meta:
        database = db


def initialize():
    '''Create the database and the table if they don't exist.'''
    db.connect()
    db.create_tables([Task], safe=True)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def work_log():
    '''stores information about tasks including name, time spent, and optional
    notes.  Tasks can be searched, edited, and deleted.

    >>> work_log()
    >>> 1

    '''
    menu = """\nSelect from the following options:\n
      1 - Enter new task
      2 - Search for existing task
      3 - Quit\n
    """
    print(menu)
    menu_select = None
    while not menu_select:
        menu_select = input('>>>')
        if menu_select == '1':
            task_entry()
        elif menu_select == '2':
            task_search()
        elif menu_select == '3':
            sys.exit(0)
        elif menu_select.lower() == 'm':
            print(menu)
            menu_select = None
        else:
            print("Please select an option from 1, 2, 3, m=menu")
            menu_select = None


def task_entry():
    '''Allows user to enter a task name, time spent, and optional notes'''
    # define employee, name, time, and notes variables
    # employee = name = time = notes = None
    # get input for each of these
    employee = name_input('Enter employee name (100 characters or less).')
    name = name_input('Enter a name for the task (100 characters or less).')
    time = number_input('Enter time spent on task in minutes.')
    notes = input("Enter any notes about the task (optional).\n>>>")
    if notes.isspace():
        notes = None
    # insert input into file
    Task.create(employee=employee, name=name, time=time, notes=notes)
    # Option to add another entry or return to main menu
    repeat = input("The task was added.  Enter another task? [Y/n]")
    if repeat.lower() == 'y':
        task_entry()
    else:
        work_log()


def task_search():
    '''Allows user to search, edit, and delete task entries from file'''
    menu = '''\nSelect from the following options:\n
        1 - Find by date
        2 - Find by time spent
        3 - Find by exact search
        4 - Find by employee name
        5 - Return to main menu\n
    '''
    print(menu)
    search_mode = None
    while not search_mode:
        search_mode = input('>>>').strip()
        if search_mode == '1':
            date_find()
        elif search_mode == '2':
            time_find()
        elif search_mode == '3':
            exact_find()
        elif search_mode == '4':
            employee_find()
        elif search_mode == '5':
            work_log()
        else:
            print("Please enter a selection from 1 to 5")
            search_mode = None


def number_input(msg):
    '''Takes string as argument and prints it to solicit input,
    and tests that input represents an integer
    '''
    time = None
    print(msg)
    while not time:
        time = input('>>>').strip()
        try:
            time = int(time)
        except ValueError:
            print('Enter a valid number.')
            time = None
        else:
            if not time or time < 0:
                print('Enter a valid time.')
                time = None
    return time


def name_input(msg):
    '''Takes string as argument and prints it to solicit name,
    then checks that input is 100 characters or less in length.
    '''
    name = None
    print(msg)
    while not name or name.isspace():
        name = input('>>>').strip()
        if len(name) > 100 or not name:
            print('Please enter a name from 1-100 characters in length.')
            name = None
    return name


def date_input(date_wrapper):
    '''Asks for date and validates for format YYYY-MM-DD'''
    # Function takes lists rather than strings since strings are immutable
    while len(date_wrapper) == 0:
        try:
            input_string = input('>>>')
            date_wrapper.append(datetime.datetime.strptime(
                                input_string, '%Y-%m-%d'))
        except ValueError:
            print('Date must be valid and in format YYYY-MM-DD. Try again.')


def date_find():
    '''Searches for all entries matching a specific date
    or falling within a date range.
    '''
    # Dates are lists so that they can be passed into date_input and modified
    search_date_1 = []
    search_date_2 = []
    search_mode = None
    while not search_mode:
        search_mode = input('Enter 1 to browse all dates '
                            'or 2 to search within a date range.\n>>>').strip()
        if search_mode not in ['1', '2']:
            print('Not a valid selection')
            search_mode = None
    if search_mode == '2':
        print('Input start date in format YYYY-MM-DD')
        date_input(search_date_1)
        print('Input end date in format YYYY-MM-DD')
        while not search_date_2:
            date_input(search_date_2)
            # make sure search_date1 is no later than search_date2
            if search_date_1[0].timestamp() > search_date_2[0].timestamp():
                print('First date cannot be later than second date. '
                      'Enter end date again.')
                search_date_2 = []
    # run search
    search_results = []
    tasks = Task.select().order_by(Task.date.desc())
    if search_mode == '2':
        tasks = tasks.where(Task.date >= search_date_1[0].date())
        tasks = tasks.where(Task.date <= search_date_2[0].date())
    if not tasks.count():
        print('\nNo results found.\n')
        task_search()
    else:
        entry_dates = []
        count = 1
        for task in tasks:
            if task.date not in entry_dates:
                entry_dates.append(task.date)
        print('Pick one of the following dates to view entries from')
        for date in entry_dates:
            date_entries_count = Task.select().where(
                Task.date == str(date)).count()
            print(str(count) + ": " + str(date) + " (" +
                  str(date_entries_count) + " entr{})".format(
                'ies' if date_entries_count > 1 else 'y'))
            count += 1
        selection = None
        print('Enter number corresponding to the desired date.')
        while not selection:
            selection = input('>>>').strip()
            try:
                selection = int(selection)
            except ValueError:
                print('Please enter a valid number')
                selection = None
            else:
                if selection > len(entry_dates) or selection < 0:
                    print('Please enter a valid number{}'.format(
                        ' between 1 and {}.'.format(
                            len(entry_dates)) if len(entry_dates) > 1
                        else '.'))
                    selection = None
        search_results = []
        query = Task.select().where(
            Task.date == str(entry_dates[selection - 1]))
        for result in query:
            search_results.append(result)
        display_results(search_results)


def time_find():
    search_results = []
    search_time = number_input("Enter task time to the nearest minute")
    query = Task.select().where(Task.time == search_time)
    for result in query:
        search_results.append(result)
    if len(search_results) == 0:
        print('\nNo results found.\n')
        task_search()
    else:
        display_results(search_results)


def exact_find():
    search_string = None
    search_results = []
    print('Enter text to be searched')
    while search_string is None or search_string.isspace():
        search_string = input('>>>')
        if search_string.strip() == '':
            print("Please enter some text to be searched.")
            search_string = None
    query = Task.select().where(
        (Task.name.contains(search_string)) |
        (Task.notes.contains(search_string))
    )
    for result in query:
        search_results.append(result)
    if len(search_results) == 0:
        print('\nNo results found.\n')
        task_search()
    else:
        print('Number of results = ' + str(len(search_results)))
        display_results(search_results)


def employee_find():
    tasks = Task.select().order_by(Task.employee.asc())
    employee_names = []
    count = 1
    for task in tasks:
        if task.employee not in employee_names:
            employee_names.append(task.employee)
    print('Pick one of the following employees to view entries from:')
    for person in employee_names:
        number_of_entries = Task.select().where(
            Task.employee == person).count()
        print(str(count) + ": " + person + " (" + str(number_of_entries)
              + " entr{})".format('ies' if number_of_entries > 1 else 'y'))
        count += 1
    selection = None
    while not selection:
        print('Enter number corresponding to the desired employee.')
        selection = input('>>>').strip()
        try:
            selection = int(selection)
        except ValueError:
            print('Please enter a valid number')
            selection = None
        else:
            if selection > len(employee_names):
                print('Please enter a valid number{}'.format(
                    ' between 1 and {}.'.format(
                      len(employee_names) if len(employee_names) > 1
                      else '.')))
                selection = None
    search_results = []
    query = Task.select().where(Task.employee == employee_names[selection - 1])
    for result in query:
        search_results.append(result)
    display_results(search_results)


def display_results(results_list):
    '''Displays search results one by one,
allowing each entry to be edited or deleted.'''
    count = 1
    for entry in results_list:
        print('''
            Result {} of {}\n
            Employee name: {}
            Task name: {}
            Work time: {}
            Date: {}
            Notes: {}
'''.format(count, len(results_list), entry.employee, entry.name,
              entry.time, entry.date, entry.notes))
        selection = None
        while not selection:
            selection = input('Select {}[E]dit entry, '
                              '[D]elete entry, [S]earch menu \n>>>'
                              .format('[N]ext result, ' if count <
                                      len(results_list) else ''))
            if selection.lower() == 'e':
                edit_entry(entry)
            elif selection.lower() == 'd':
                delete_entry(entry)
            elif selection.lower() == 's':
                # quit display results and go back to search menu
                return task_search()
            elif selection.lower() != 'n':
                selection = None
        count += 1
    print("\nEnd of search results.\n")
    task_search()


def edit_entry(table_row):
    '''Allows user to edit specific field of task entry'''
    field_dict = {'1': 'name', '2': 'time', '3': 'date', '4': 'notes'}
    field = None
    while not field:
        field = input('''Select field to edit: 1 - task name, 2 - time, 3 - date, 4 - notes.
Enter 5 to go back to search results, 6 to go back to search menu\n>>>''')
        if field == '5':
            return
        if field == '6':
            return task_search()
    print('Enter new {}.'.format(field_dict[field]))
    new_info = None
    while not new_info:
        new_info = input('>>>')
        if new_info.isspace():
            print('Please enter non-empty string.')
            new_info = None
            continue
        if field == '2':
            try:
                new_info = int(new_info)
            except ValueError:
                print("Please enter a valid number")
                new_info = None
            else:
                new_info = str(new_info)
        if field == '3':
            try:
                datetime.datetime.strptime(new_info, '%Y-%m-%d')
            except ValueError:
                print("Dates should be valid and in format YYYY-MM-DD")
                new_info = None
    if field == '1':
        query = Task.update(name=new_info).where(Task.id == table_row.id)
    elif field == '2':
        query = Task.update(time=new_info).where(Task.id == table_row.id)
    elif field == '3':
        query = Task.update(date=new_info).where(Task.id == table_row.id)
    else:
        query = Task.update(notes=new_info).where(Task.id == table_row.id)
    query.execute()
    print("\nEntry edited!\n")


def delete_entry(table_row):
    '''Allows user to delete task entry'''
    print("Confirm delete? [yN]")
    confirm = input('>>>')
    if confirm.lower() == 'y':
        row = Task.get(Task.id == table_row.id)
        row.delete_instance()
        print("\nEntry deleted!\n")
    else:
        print("Delete cancelled!\n")


if __name__ == "__main__":
    print(welcome)
    initialize()
    work_log()