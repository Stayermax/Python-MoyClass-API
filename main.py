"""
Code last update 07.11.2021
This is example use of MoyClass library.
"""

from moyclass import MoyClassAPI
import credentials

import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option("max_colwidth", None)


# Libraries for my example
import os
from pprint import pprint
from datetime import datetime, timedelta
import time
import math
import json

def data_load(func, entity_name, params = None, load_new_data = True):
    """
    Function loads data entities and transfers them into dataframe

    :param func: function that requests data from server and returns data in format:
        {
            "entity_name": [ {...}, {...}] , # list of dictionaries
            "stats": {
                "totalItems": 5
            }
        },
        or in format:
        [ { ... } ] # list of dictionaries
    :param entity_name: name of the data returned
        First format entity_name examples: "users", "lessonRecords", "lessons", "joins"
        Second format entity_name examples: "filials", "rooms", "managers"
    :param params: QUERY PARAMETERS ( options can be seen on https://api.moyklass.com/ for each entity_name)
    :return: dataframe with data

    """
    data_path = f"saved_data/{entity_name}_df.csv"
    if (os.path.exists(data_path) and load_new_data == False):
        df = pd.read_csv(data_path)
    else:
        if (params == None):
            params = []
        first_response = func(params)
        if(type(first_response) == dict):
            items_num = first_response['stats']['totalItems']
            print(f"Number of {entity_name} with requested params: {items_num}")
            pages_num = math.ceil(items_num / 100)
            start = datetime.now()
            full_list = []
            for i in range(pages_num):
                full_list += func(params + [['offset', f'{100 * i}']])[entity_name]
            df = pd.DataFrame(full_list)
            print(f"data loaded in {datetime.now() - start} ")
        else:
            print(entity_name)
            df = pd.DataFrame(first_response)
        df.to_csv(data_path, index=False)
    print(f"{entity_name}_df is loaded")
    return df

if __name__ == '__main__':
    API_KEY = credentials.API_KEY

    api = MoyClassAPI(api_key=API_KEY)

    # # Example 1: Get all managers:
    # print(f"Managers as list : {api.get_company_managers()}")
    # print(f"Managers as dataframe : {data_load(api.get_company_managers, 'managers')}")
    #
    # # Example 2: Get all lessons as dataframe:
    # print(f"lessons as dataframe : {data_load(api.get_lessons, 'lessons')}")

    # Example 3: Get all users as dataframe:
    load = False
    user_df = data_load(api.get_users, 'users', load_new_data=load)
    id_name_dict = pd.Series(user_df.name.values, index=user_df.id.values).to_dict()
    id_status_dict = pd.Series(user_df.clientStateId.values, index=user_df.id.values).to_dict()
    id = user_df[['name', 'clientStateId','id']].set_index('id').to_dict(orient = 'list')
    print(id)
    print('============')
    print('============')
    print('============')
    # Get last month (last 31 days) lessons with lesson records:
    from_date = datetime.today().date() - timedelta(days=31)
    to_date = datetime.today().date()
    params = [['date', f"{from_date}"], ['date', f"{to_date}"], ['includeRecords','true']]
    lessond_with_records_df = data_load(api.get_lessons, 'lessons', params=params, load_new_data=load)

    drop_cols = ['beginTime', 'endTime', 'createdAt', 'filialId', 'roomId', 'comment', 'maxStudents',
            'topic', 'description', 'teacherIds', 'status']
    lessond_with_records_df = lessond_with_records_df.drop(drop_cols, axis = 1)
    # user_visits structure:
    # {userId: {classId: [['date', 'visit_status']]}}
    user_visits = {}
    for index, row in lessond_with_records_df.iterrows():
        classId = row['classId']
        date = row['date']
        record = row['records']
        if(len(record)):
            if(type(record)==str):
                record = record.replace("\'", "\"")
                record = record.replace("True", "\"True\"")
                record = record.replace("False", "\"False\"")
                record = record.replace("None", "\"None\"")
                data = json.loads(record)
            else:
                data = record
            for el in data:
                userId = el['userId']
                lessonId = el['lessonId']
                visit = 1 if el['visit']=='True' else 0
                if(userId in user_visits):
                    if(classId in user_visits[userId].keys()):
                        user_visits[userId][classId].append([date, visit])
                    else:
                        user_visits[userId][classId] = [[date, visit]]
                else:
                    user_visits[userId] = {classId : [[date, visit]]}


    # user_visits[1] = {
    #     1: [['2021-10-13', 0], ['2019-10-13', 0], ['2020-10-13', 0]],
    #     2: [['2021-10-13', 1], ['2021-01-13', 0]],
    #     3: [['2021-10-13', 1]]
    # }
    # user_status[1]=98582


    good_students = []
    bad_students = []
    for userId in user_visits.keys():
        isBad = True
        # Статус учится - 98582
        if (id_status_dict[userId] != 98582):
            continue
        for classId in user_visits[userId]:
            dates_visits = user_visits[userId][classId]
            dates_visits.sort(key=lambda el : datetime.strptime(el[0], "%Y-%m-%d"))
            if(len(dates_visits)==1):
                if(dates_visits[-1][1] == 1):
                    isBad = False
            elif (len(dates_visits) > 1):
                if (dates_visits[-1][1] == 1 or dates_visits[-2][1] == 1 ):
                    isBad = False
        user_visits[userId]['isBad'] = isBad
        if(isBad == True):
            bad_students.append(userId)
        else:
            good_students.append(userId)
    # print(user_status_id)
    # pprint(user_visits)

    print(f"{len(bad_students)} BAD STUDENTS:")
    for sId in bad_students:
        print(f"{sId}: {id_name_dict[sId]}")




# Joins:
    # joins_classes = {join['id']:join['classId'] for join in u_info['joins']}
    # classes_joins = {join['classId']:join['id'] for join in u_info['joins']}
    # print(f"User {uid} joins_ids to classes_ids: {joins_classes}")
    # print(f"User {uid} classes_ids to joins_ids: {classes_joins}"


    # #Lesson records:
    # Get last month (last 31 days) lesson records:
    # from_date = datetime.today().date() - timedelta(days=31)
    # to_date = datetime.today().date()
    #
    # params = [['date', f"{from_date}"], ['date', f"{to_date}"]]
    # lr_df_path = 'saved_data/lessonRecords_df.csv'
    # lr_df = last_month_data_load(api.get_lesson_records, 'lessonRecords', lr_df_path, params, False)
    # print(f"lesson_records columns: {list(lr_df.columns)}")
    #
    # drop_cols = ['free', 'goodReason', 'test', 'paid', 'paid', 'createdAt', 'bill', 'userSubscription']
    # lr_df = lr_df.drop(drop_cols, axis = 1)
    # print(lr_df.head())



"""
    l_df_path = 'saved_data/lessons_df.csv'
    l_df, lr_df = records_from_lessons(True)
    print(f"lesson columns: {list(l_df.columns)}")

    drop_cols = ['createdAt', 'filialId', 'roomId', 'classId', 'comment', 'maxStudents',
                 'topic', 'description', 'teacherIds',]
    l_df = l_df.drop(drop_cols, axis=1)
    print(l_df.head())
    """

    #
    #
    # uid = 1715582 #1741162
    #
    # u_info = api.get_user_info(uid)
    # print("USER INFO:")
    # pprint(u_info)
    # # Joins:
    # joins_classes = {join['id']:join['classId'] for join in u_info['joins']}
    # classes_joins = {join['classId']:join['id'] for join in u_info['joins']}
    # print(f"User {uid} joins_ids to classes_ids: {joins_classes}")
    # print(f"User {uid} classes_ids to joins_ids: {classes_joins}")
    #
    #
    #
    # less = api.get_lessons(params)
    # l_df = resp_df(less)
    # print(f"LESSONS: ")
    # print(l_df.head())
    #
    #
    # lr_df = resp_df(less)
    # print(f"LESSONS RECORDS: ")
    # print(lr_df.head(30))
    #
    #
