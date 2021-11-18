# coding=utf-8
import os
import math
import requests
import pandas as pd
from datetime import datetime
import json
import pickle as pkl

def json_print(json_object):
    """
    Json object pretty print
    """
    parsed = json.loads(json_object)
    print(json.dumps(parsed, indent=4, sort_keys=True))

def data_load(method, entity_name, params = None, load_new_data = True):
    """
    Function loads data entities and transfers them into dataframe. Dataframe then saved as pickle file and
     can be loaded next time you run the code (we use pickle and not to_csv method in order to save types of df columns)

    :param method: function that requests data from server and returns data in format:
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
    :param load_new_data: if True loads data from the server. Otherwise tries to find corresponding pickle
     file in 'saved_data' folder


    :return: dataframe with data
    """
    if(not os.path.exists('saved_data')):
        os.mkdir('saved_data')
    data_path = f"saved_data/{entity_name}_df.pkl"
    if (os.path.exists(data_path) and load_new_data == False):
        with open(data_path, 'rb') as f:
            df = pkl.load(f)
        print(f"{entity_name}_df is loaded from file")
    else:
        page_entities_num = 100 # default value

        # add limit parameter in case it's not in the params
        if(params != None):
            has_limit = False
            for param in params:
                if(param[0]=='limit'):
                    page_entities_num = param[1]
                    has_limit = False
            if (not has_limit):
                params.append(['limit', page_entities_num])
        if (params == None):
            params = [['limit', page_entities_num]]

        first_response = method(params)
        if(type(first_response) == dict):
            items_num = first_response['stats']['totalItems']
            print(f"Number of {entity_name} with requested params: {items_num}")
            pages_num = math.ceil(items_num / page_entities_num)
            start = datetime.now()
            full_list = []
            for i in range(pages_num):
                full_list += method(params + [['offset', f'{page_entities_num * i}']])[entity_name]
            df = pd.DataFrame(full_list)
            print(f"{entity_name[0].upper()}{entity_name[1:]} data loaded in {(datetime.now() - start).seconds} seconds ")
        else:
            print(entity_name)
            df = pd.DataFrame(first_response)
        with open(data_path, 'wb') as f:
            pkl.dump(df,f)
    return df

class MoyClassAPI:

    def __init__(self, api_key):

        self.api_key = api_key  # your access key
        self.token = self._get_token()

    def __get_request(self, url, auth="default", headers="default", params=None):
        """
        Get request template.
        
        :param url: request url
        :param auth: for the most cases should be left as "default"
        :param headers: for the most cases should be left as "default" (
        :param params: request parameters should be transferred as list of pairs or as dictionary.
            I recommend using list of pairs since first item in pair can be not unique for some requests.
            For example: params = [ ['name', 'John Doe'], ['date', '2020-01-01'], ['date', '2021-11-19'] ]
        """
        if(auth == "default"):
            auth = {'apiKey':self.api_key}
        if(headers == "default"):
            headers = {"x-access-token": self.token}
        try:
            r = requests.get(
                url=url,
                json=auth,
                headers=headers,
                params=params
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
            print(f"Server error message: {r.json()['code']}")
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)
        finally:
            return r.json()

    def __post_request(self, url, auth="default", headers="default", params=None):
        """
        Post request template.

        :param url: request url
        :param auth: for the most cases should be left as "default"
        :param headers: for the most cases should be left as "default" (
        :param params: request parameters should be transferred as list of pairs or as dictionary.
            I recommend using list of pairs since first item in pair can be not unique for some requests.
            For example: params = [ ['name', 'John Doe'], ['date', '2020-01-01'], ['date', '2021-11-19'] ]
        """
        if(auth == "default"):
            auth = {'apiKey':self.api_key}
        if(headers == "default"):
            headers = {"x-access-token": self.token}
        try:
            r = requests.post(
                url = url,
                json = auth,
                headers = headers,
                params = params
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
            print(f"Server error message: {r.json()['code']}, error message : {r.json()['message']}")
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)
        return r.json()

    # Autorization:
    def _get_token(self):
        """
        Authorization. Obtaining a token for working with the API.
        You can create and view API keys in the CRM section "My Class" - "Settings - API".
        """
        url = "https://api.moyklass.com/v1/company/auth/getToken"
        token = self.__post_request(url, headers=None)['accessToken']
        print(f"Token obtained")
        return token

    def _refresh_token(self):
        """
        Authorization. Generates a new token, old token continues to work.
        todo: doesn't work
        """
        url = "https://api.moyklass.com/v1/company/auth/refreshToken"
        new_token = self.__post_request(url)['accessToken']
        print(f"Token refreshed")
        return new_token

    def _revoke_token(self):
        """
        Authorization. Revokes the existing token. The token is passed in the x-access-token header.
        todo: doesn't work
        """
        url = "https://api.moyklass.com/v1/company/auth/revokeToken"
        self.__post_request(url)
        print("Token revoked")

    # Company ( Компания )
    def get_company_branches(self, params=None):
        """
        Returns a list of company branches ( филиалы )
        """
        url = "https://api.moyklass.com/v1/company/filials"
        return self.__get_request(url, params=params)

    def get_company_rooms(self, params=None):
        """
        Returns a list of company audiences ( аудитории )
        """
        url = "https://api.moyklass.com/v1/company/rooms"
        return self.__get_request(url, params=params)

    # Managers ( Сотрудники )
    def get_company_managers(self, params=None):
        """
        Returns a list of company employees ( список сотрудников )
        """
        url = "https://api.moyklass.com/v1/company/managers"
        return self.__get_request(url, params=params)

    def create_manager(self, params=None):
        """
        Creates new manager and return it in form of JSON
        name ( required ) : Полное имя [ string <= 100 characters ]
        phone ( required ) : Номер телефона [ string <= 15 characters ^[0-9]{10,15}$ ]
        email ( required if manager need to access CRM) : Эл. почта [ string or null <email> <= 100 characters]
        filials ( required ) : ID филиалов сотрудника [ Array of integers <int64> non-empty ]
        salaryFilialId (required if manager works in more than one branch): ID филиала для занесения ЗП.
                                                                                    [integer or null <int64>]
        roles ( required ) : ID ролей сотрудника [ Array of integers <int64> non-empty ]
        enabled : Разрешен вход в CRM [ boolean ], Default: false
        password ( required if manager need to access CRM) : Пароль для входа в CRM. [ string >= 6 characters ]
        additionalContacts : Дополнительные контакты [ string or null ]
        isStaff : Штатный сотрудник [ boolean ], Default: true
        isWork : Работает [ boolean ], Default: true
        sendNotifies : Отправлять уведомления [ boolean ], Default: true
        startDate : Дата начала работы [ string or null <date> ]
        endDate : Дата окончания работы [ string or null <date> ]
        contractNumber : Номер договора [ string or null ]
        contractDate : Дата договора [ string or null <date> ]
        birthDate : Дата рождения [ string or null <date> ]
        passportData : Паспортные данные [ string or null ]
        comment : Комментарий к сотруднику [ string or null ]
        color : Цвет сотрудника. Если цвет не передан при создании, он будет выбран автоматически.
                                                                                    [ string^#[A-Fa-f0-9]{6}$]
        rateId : ID ставки сдельной оплаты [ integer or null <int64> ]
        isOwner : Является ли владельцем компании. Такой сотрудник может быть только один. [ boolean ], Default: false
        """
        url = "https://api.moyklass.com/v1/company/managers"
        return self.__post_request(url, params=params)

    def get_users(self, params=None):
        """
        Returns a list of Company users (clients / students )
        """
        url = "https://api.moyklass.com/v1/company/users"
        return self.__get_request(url, params=params)

    def get_user_info(self, uid, params=None):
        """
        uid: user id
        Returns info about the user
        """
        url = f"https://api.moyklass.com/v1/company/users/{uid}"
        return self.__get_request(url, params=params)

    def get_joins(self, params=None):
        """
        Returns a list of joins ( requests / records ) in groups ( Список заявок )
        """
        url = "https://api.moyklass.com/v1/company/joins"
        return self.__get_request(url, params=params)

    def get_joins_info(self, jid, params=None):
        """
        jid: join id
        Returns info about the join ( request / record ) ( Информация о заявке )
        """
        url = f"https://api.moyklass.com/v1/company/joins/{jid}"
        return self.__get_request(url, params=params)

    def get_courses(self, params=None):
        """
        Returns a list of courses ( Список программ )
        """
        url = "https://api.moyklass.com/v1/company/courses"
        return self.__get_request(url, params=params)

    def get_classes(self, params=None):
        """
        Returns a list of classes ( Список групп )
        """
        url = "https://api.moyklass.com/v1/company/classes"
        return self.__get_request(url, params=params)

    def get_class_info(self, cid, params=None):
        """
        cid: class id
        Returns info about the class ( Информация о группе )
        """
        url = f"https://api.moyklass.com/v1/company/classes/{cid}"
        return self.__get_request(url, params=params)

    def get_lessons(self, params=None):
        """
        Returns a list of lessons ( Список занятий )
        """
        url = "https://api.moyklass.com/v1/company/lessons"
        return self.__get_request(url, params=params)

    def get_lesson_info(self, lid, params=None):
        """
        lid: lesson id
        Returns info about the lesson ( Информация о занятии )
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lid}"
        return self.__get_request(url, params=params)

    def get_lesson_records(self, params=None):
        """
        Returns a list of lessonRecords ( Список записей на занятия )
        """
        url = "https://api.moyklass.com/v1/company/lessonRecords"
        return self.__get_request(url, params=params)

    def get_lesson_record_info(self, lrid, params=None):
        """
        lrid: lesson record id
        Returns info about the lesson record ( Информация о записи на занятие )
        """
        url = f"https://api.moyklass.com/v1/company/lessonRecords/{lrid}"
        return self.__get_request(url, params=params)

    def get_(self, params=None):
        """
        Returns a list of
        """
        url = ""
        return self.__get_request(url, params=params)

    def get__info(self, id, params=None):
        """
        id:  id
        Returns info about the  ( Информация о  )
        """
        url = f"/{id}"
        return self.__get_request(url, params=params)

    #################################################################
    #################### P O S T   M E T H O D S ####################
    #################################################################

    #################################################################
    ##################### G E T   M E T H O D S #####################
    #################################################################

    # def create_manager(self):
    #     """
    #     Create company employee
    #     """
    #     url = "https://api.moyklass.com/v1/company/managers"
    #     return self._post_request(url)