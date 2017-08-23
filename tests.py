import datetime
import unittest
from unittest.mock import patch
import io
from io import StringIO
from playhouse.test_utils import test_database
from peewee import *

import work_db
from work_db import Task

test_db = SqliteDatabase(':memory:')


class WorkLogTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.task_search')
    @patch('work_db.task_entry')
    @patch('builtins.input', side_effect=['x', 'm', '1', '2', '3'])
    def test_work_log(self, mock_input, mock_entry, mock_search, mock_stdout):
        work_db.work_log()
        self.assertIn("Please", mock_stdout.getvalue())
        self.assertIn("Select", mock_stdout.getvalue())
        self.assertTrue(mock_entry.called)
        work_db.work_log()
        self.assertTrue(mock_search.called)
        with self.assertRaises(SystemExit):
            work_db.work_log()


class TaskEntryTests(unittest.TestCase):
    @patch('work_db.work_log')
    @patch('builtins.input',
           side_effect=['Fred', 'Brewing coffee', '30', 'Starbucks', 'n'])
    def test_task_entry(self, mock_input, mock_work_log):
        with test_database(test_db, [Task]):
            work_db.task_entry()
            query_count = Task.select().where(
                              (Task.employee == 'Fred') &
                              (Task.name == 'Brewing coffee') &
                              (Task.time == '30') &
                              (Task.notes == 'Starbucks')
                          ).count()
            self.assertEqual(query_count, 1)
            self.assertTrue(mock_work_log.called)


class TaskSearchTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.work_log')
    @patch('work_db.employee_find')
    @patch('work_db.exact_find')
    @patch('work_db.time_find')
    @patch('work_db.date_find')
    @patch('builtins.input', side_effect=['x', '1', '2', '3', '4', '5'])
    def test_task_search(self, mock_input, mock_date_find, mock_time_find,
                         mock_exact_find, mock_employee_find,
                         mock_work_log, mock_stdout):
        work_db.task_search()
        self.assertIn("Please enter a selection from 1 to 5",
                      mock_stdout.getvalue())
        self.assertTrue(mock_date_find.called)
        work_db.task_search()
        self.assertTrue(mock_time_find.called)
        work_db.task_search()
        self.assertTrue(mock_exact_find.called)
        work_db.task_search()
        self.assertTrue(mock_employee_find.called)
        work_db.task_search()
        self.assertTrue(mock_work_log.called)


class NumberInputTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['four', '0', '1'])
    def test_number_input_invalid(self, mock_input, mock_stdout):
        result = work_db.number_input("Input number")
        self.assertIn('Enter a valid number', mock_stdout.getvalue())
        self.assertIn('Enter a valid time', mock_stdout.getvalue())
        self.assertEqual(result, 1)


class NameInputTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['a' * 101, 'Brewing coffee'])
    def test_long_name_input(self, mock_input, mock_stdout):
        work_db.name_input('Insert name')
        self.assertIn('Please enter a name from 1-100 characters in length.',
                      mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=[' ', 'Brewing coffee'])
    def test_no_name_input(self, mock_input, mock_stdout):
        work_db.name_input('Insert name')
        self.assertIn('Please enter a name from 1-100 characters in length.',
                      mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['Brewing coffee'])
    def test_good_name_input(self, mock_input, mock_stdout):
        self.assertEqual(work_db.name_input('Insert name'), 'Brewing coffee')


class DateInputTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['2017-01-33', '2017-01-01'])
    def test_nonexistent_date(self, mock_input, mock_stdout):
        work_db.date_input([])
        self.assertIn('Date must be valid and in format YYYY-MM-DD. ' +
                      'Try again.', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['2017/01/01', '2017-01-01'])
    def test_incorrectly_formatted_date(self, mock_input, mock_stdout):
        work_db.date_input([])
        self.assertIn('Date must be valid and in format YYYY-MM-DD. ' +
                      'Try again.', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['2017-01-01'])
    def test_correct_date_format(self, mock_input, mock_stdout):
        time = []
        work_db.date_input(time)
        self.assertEqual(datetime.datetime.strftime(time[0],
                         '%Y-%m-%d'), '2017-01-01')


class DateFindTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.display_results')
    @patch('builtins.input', side_effect=['x', '1', 'one', '2', '1'])
    def test_single_date_search(self, mock_input,
                                mock_display_results, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Richard',
                name='Xeroxing',
                date=datetime.date(2017, 8, 18),
                time='60',
                notes='Richmeister at the copy machine'
            )
            work_db.date_find()
            self.assertIn('Not a valid selection', mock_stdout.getvalue())
            self.assertIn('Pick one of the following dates ' +
                          'to view entries from', mock_stdout.getvalue())
            self.assertIn('1: 2017-08-18 (1 entry)', mock_stdout.getvalue())
            self.assertIn('Please enter a valid number',
                          mock_stdout.getvalue())
            self.assertTrue(mock_display_results.called)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.display_results')
    @patch('builtins.input',
           side_effect=['2', '2017-08-16', '2017-08-18', '2'])
    def test_date_range_search(self, mock_input,
                               mock_display_results, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Rika',
                name='Meeting',
                date=datetime.date(2017, 8, 16),
                time='120',
                notes='Long meeting'
            )
            Task.create(
                employee='Ai',
                name='Writing report',
                date=datetime.date(2017, 8, 17),
                time='30',
                notes='Report for sales'
            )
            work_db.date_find()
            self.assertNotIn('\nNo results found.\n', mock_stdout.getvalue())
            self.assertTrue(mock_display_results.called)


class TimeFindTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.task_search')
    @patch('builtins.input', side_effect=['30'])
    def test_time_find_no_results(self, mock_input, mock_task_search,
                                  mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Rie',
                name='Presentation',
                date=datetime.date(2017, 8, 18),
                time='40',
                notes='Presentation on Asian market'
            )
            work_db.time_find()
            self.assertIn('\nNo results found.\n', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.display_results')
    @patch('builtins.input', side_effect=['40'])
    def test_time_find_with_results(self, mock_input,
                                    mock_display_results, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Rie',
                name='Presentation',
                date=datetime.date(2017, 8, 18),
                time='40',
                notes='Presentation on Asian market'
            )
            work_db.time_find()
            self.assertTrue(mock_display_results.called)


class ExactFindTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.task_search')
    @patch('builtins.input', side_effect=['', 'dancing'])
    def test_exact_find_no_results(self, mock_input,
                                   mock_task_search, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Yumeno',
                name='Answering the phone',
                date=datetime.date(2017, 8, 21),
                time='60',
                notes='Customer service'
            )
            work_db.exact_find()
            self.assertIn('Please enter some text to be searched',
                          mock_stdout.getvalue())
            self.assertIn('\nNo results found.\n', mock_stdout.getvalue())
            self.assertTrue(mock_task_search.called)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.display_results')
    @patch('builtins.input', side_effect=['Answering'])
    def test_exact_find_with_results(self, mock_input,
                                     mock_display_results, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Yumeno',
                name='Answering the phone',
                date=datetime.date(2017, 8, 21),
                time='60',
                notes='Customer service'
            )
            work_db.exact_find()
            self.assertIn('Number of results = 1', mock_stdout.getvalue())
            self.assertTrue(mock_display_results.called)


class EmployeeFindTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.display_results')
    @patch('builtins.input', side_effect=['five', '5', '1'])
    def test_employee_find(self, mock_input,
                           mock_display_results, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Kato',
                name='Shelving books',
                date=datetime.date(2017, 8, 15),
                time='20',
                notes='LC call numbers'
            )
            Task.create(
                employee='Chinami',
                name='Reference work',
                date=datetime.date(2017, 8, 17),
                time='40',
                notes='Phone reference work'
            )
            work_db.employee_find()
            self.assertIn('1: Chinami (1 entry)',
                          mock_stdout.getvalue())
            self.assertIn('2: Kato (1 entry)',
                          mock_stdout.getvalue())
            self.assertIn('Please enter a valid number',
                          mock_stdout.getvalue())
            self.assertIn('Please enter a valid number between 1 and 2',
                          mock_stdout.getvalue())


class DisplayResultsTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('work_db.task_search')
    @patch('work_db.delete_entry')
    @patch('work_db.edit_entry')
    @patch('builtins.input', side_effect=['e', 'd', 'n', 's'])
    def test_display_results(self, mock_input, mock_edit_entry,
                             mock_delete_entry, mock_task_search,
                             mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Anna',
                name='Speaking Russian',
                date=datetime.date(2017, 8, 15),
                time='10',
                notes='FUSHEEMU'
            )
            Task.create(
                employee='Akari',
                name='Acting',
                date=datetime.date(2017, 8, 17),
                time='40',
                notes='Gintama'
            )
            Task.create(
                employee='Airi',
                name='Golfing',
                date=datetime.date(2017, 8, 22),
                time='180',
                notes='Bankaa'
            )
            Task.create(
                employee='Maimi',
                name='Testing okazu',
                date=datetime.date(2017, 8, 22),
                time='25',
                notes='Aji de gallina'
            )
            search_results = []
            query = Task.select().order_by(Task.employee.asc())
            for result in query:
                search_results.append(result)
            work_db.display_results(search_results)
            self.assertIn('''Result 1 of 4\n
                          Employee name: Airi
                          Task name: Golfing
                          Work time: 180
                          Date: 2017-08-22
                          Notes: Bankaa
                          '''.replace(" ", ""),
                          mock_stdout.getvalue().replace(" ", ""))
            self.assertTrue(mock_edit_entry.called)
            self.assertIn('''Result 2 of 4\n
                          Employee name: Akari
                          Task name: Acting
                          Work time: 40
                          Date: 2017-08-17
                          Notes: Gintama
                          '''.replace(" ", ""),
                          mock_stdout.getvalue().replace(" ", ""))
            self.assertTrue(mock_delete_entry.called)
            self.assertIn('''
                          Result 3 of 4\n
                          Employee name: Anna
                          Task name: Speaking Russian
                          Work time: 10
                          Date: 2017-08-15
                          Notes: FUSHEEMU
                          '''.replace(" ", ""),
                          mock_stdout.getvalue().replace(" ", ""))
            self.assertIn('''
                          Result 4 of 4\n
                          Employee name: Maimi
                          Task name: Testing okazu
                          Work time: 25
                          Date: 2017-08-22
                          Notes: Aji de gallina
                          '''.replace(" ", ""),
                          mock_stdout.getvalue().replace(" ", ""))
            self.assertTrue(mock_task_search.called)


class EditEntryTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['1', '    ', 'Drawing'])
    def test_edit_entry_name(self, mock_input, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Saki',
                name='Bowling',
                date=datetime.date(2017, 8, 22),
                time='45',
                notes='Strike')
            query = Task.get(Task.id == 1)
            work_db.edit_entry(query)
            self.assertIn('Please enter non-empty string.',
                          mock_stdout.getvalue())
            self.assertEqual(Task.get(Task.id == 1).name, 'Drawing')
            self.assertIn('Entry edited', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['2', 'ten', '10'])
    def test_edit_entry_time(self, mock_input, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Saki',
                name='Bowling',
                date=datetime.date(2017, 8, 22),
                time='45',
                notes='Strike'
            )
            query = Task.get(Task.id == 1)
            work_db.edit_entry(query)
            self.assertIn("Please enter a valid number",
                          mock_stdout.getvalue())
            self.assertEqual(Task.get(Task.id == 1).time, 10)
            self.assertIn('Entry edited', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['3', '2017/08/21', '2017-08-21'])
    def test_edit_entry_date(self, mock_input, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Saki',
                name='Bowling',
                date=datetime.date(2017, 8, 22),
                time='45',
                notes='Strike'
            )
            query = Task.get(Task.id == 1)
            work_db.edit_entry(query)
            self.assertIn("Dates should be valid and in format YYYY-MM-DD",
                          mock_stdout.getvalue())
            self.assertEqual(Task.get(Task.id == 1).date,
                             datetime.date(2017, 8, 21))
            self.assertIn('Entry edited', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['4', 'P-league'])
    def test_edit_entry_notes(self, mock_input, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Saki',
                name='Bowling',
                date=datetime.date(2017, 8, 22),
                time='45',
                notes='Strike'
            )
            query = Task.get(Task.id == 1)
            work_db.edit_entry(query)
            self.assertEqual(Task.get(Task.id == 1).notes, 'P-league')
            self.assertIn('Entry edited', mock_stdout.getvalue())


class DeleteEntryTests(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['y'])
    def test_delete_entry_confirm(self, mock_input, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Kashiyuka',
                name='Singing',
                date=datetime.date(2017, 8, 22),
                time='5',
                notes='Autotune'
            )
            query = Task.get(Task.id == 1)
            work_db.delete_entry(query)
            self.assertEqual(Task.select().count(), 0)
            self.assertIn('Entry deleted', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['n'])
    def test_delete_entry_cancel(self, mock_input, mock_stdout):
        with test_database(test_db, [Task]):
            Task.create(
                employee='Kashiyuka',
                name='Singing',
                date=datetime.date(2017, 8, 22),
                time='5',
                notes='Autotune'
            )
            query = Task.get(Task.id == 1)
            work_db.delete_entry(query)
            self.assertEqual(Task.select().where(
                Task.employee == 'Kashiyuka').count(), 1)
            self.assertIn('Delete cancelled', mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()