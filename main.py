"""
Code last update 14.11.2021
This is example use of MoyClass library.
"""

from moyclass import MoyClassAPI, data_load
import credentials
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option("max_colwidth", None)

# Libraries for my example
from datetime import datetime, timedelta
import json
from pprint import pprint

def badUsersSearch(api : MoyClassAPI, load_new_data = True):
    """
    We assume that user is good if he attended at least one of the
     last two lessons in at least one of his groups (classes) during the last month.
     If there were no lessons last month for this user he's not good.
     The user is bad if he isn't good.

    :param api: MoyClassAPI object
    :param load_new_data: load new data from the server if True, load from 'saved_data' folder o.w.
    :return: list of bad users ids and names: [[uId, uName], ... ]
    """

    # Get all users as dataframe and turn them into dictionary {uId: {'name': 'Oleg', 'clientStateId': 179}}
    user_df = data_load(api.get_users, 'users', load_new_data=load_new_data)
    user_data_dict = user_df[['name', 'clientStateId', 'id']].set_index('id').to_dict(orient='index')

    # Get last month (last 31 days) lessons with lesson records:
    from_date = datetime.today().date() - timedelta(days=31)
    to_date = datetime.today().date()
    params = [['date', f"{from_date}"], ['date', f"{to_date}"], ['includeRecords', 'true']]
    lessons_with_records_df = data_load(api.get_lessons, 'lessons', params=params, load_new_data=load_new_data)

    drop_cols = ['beginTime', 'endTime', 'createdAt', 'filialId', 'roomId', 'comment', 'maxStudents',
                 'topic', 'description', 'teacherIds', 'status']
    lessons_with_records_df = lessons_with_records_df.drop(drop_cols, axis=1)

    # user_visits structure:
    # {userId: {classId: [['date', 'visit_status']]}}
    user_visits = {}
    for index, row in lessons_with_records_df.iterrows():
        classId = row['classId']
        date = row['date']
        record = row['records']
        if (len(record)):
            if(type(record)==str):
                record = record.replace("\'", "\"")
                record = record.replace("True", "\"True\"")
                record = record.replace("False", "\"False\"")
                record = record.replace("None", "\"None\"")
                record = json.loads(record)
            for el in record:
                userId = el['userId']
                lessonId = el['lessonId']
                if(type(el['visit']) == bool and el['visit'] == True):
                    visit = 1
                elif(type(el['visit']) == str and el['visit'] == "True"):
                    visit = 1
                else:
                    visit = 0
                if (userId in user_visits.keys()):
                    if (classId in user_visits[userId].keys()):
                        user_visits[userId][classId].append([date, visit])
                    else:
                        user_visits[userId][classId] = [[date, visit]]
                else:
                    user_visits[userId] = {classId: [[date, visit]]}

    # pprint(user_visits)

    good_users = []
    bad_users = []
    for userId in user_visits.keys():
        isBad = True
        # Статус учится - 98582
        if (user_data_dict[userId]['clientStateId'] != 98582):
            continue
        for classId in user_visits[userId]:
            dates_visits = user_visits[userId][classId]
            dates_visits.sort(key=lambda el: datetime.strptime(el[0], "%Y-%m-%d"))
            if (len(dates_visits) == 1):
                if (dates_visits[-1][1] == 1):
                    isBad = False
            elif (len(dates_visits) > 1):
                if (dates_visits[-1][1] == 1 or dates_visits[-2][1] == 1):
                    isBad = False
        user_visits[userId]['isBad'] = isBad
        if (isBad == True):
            bad_users.append([userId, user_data_dict[userId]['name']])
        else:
            good_users.append([userId, user_data_dict[userId]['name']])

    file = open(f'saved_data/bu_{datetime.now()}.txt', 'w')
    pprint(bad_users, file)
    file.close()

    return bad_users

def examplesFunction(api : MoyClassAPI):
     # Example 1: Get all managers:
    print(f"Managers as list : {api.get_company_managers()}")
    print(f"Managers as dataframe : {data_load(api.get_company_managers, 'managers')}")

    # Example 2: Get all users as dataframe
    user_df = data_load(api.get_users, 'users')
    print(f"Users as dataframe : {user_df}")

    # Example 3: Get all lessons as dataframe:
    print(f"Lessons as dataframe : {data_load(api.get_lessons, 'lessons')}")

    # Example 4: Get last month (last 31 days) lessons with lesson records:
    from_date = datetime.today().date() - timedelta(days=31)
    to_date = datetime.today().date()
    params = [['date', f"{from_date}"], ['date', f"{to_date}"], ['includeRecords', 'true']]
    lessons_with_records_df = data_load(api.get_lessons, 'lessons', params=params)
    print(f"Lessons with records dataframe : {lessons_with_records_df}")

def API_test_functions(api: MoyClassAPI):
    pass

if __name__ == '__main__':

    API_KEY = credentials.API_KEY
    api = MoyClassAPI(api_key=API_KEY)

    # bu = badUsersSearch(api, load_new_data=True)
    # print(f'bad users number: {len(bu)}')

    API_test_functions(api)

