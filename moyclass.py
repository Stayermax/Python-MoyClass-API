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
        self.print_Flag = True
        self.token = self._get_token()


    # Requests :
    def __request(self, method, url, headers="tokenOnlyMode", json=None, params=None, void=False):
        """
        Шаблон запроса.

        Request template.
        
        :param url: request url
        :param headers:
            request headers should be empty in request for token ( "getTokenMode" value )
            request headers should be equal {"x-access-token":self.token} in most requests ( "tokenOnlyMode" value )
            request headers can be dictionary with parameters in this case token would be added to it ( dict type )
        :param json: dict object. json is request body. It always includes api key and in some cases also request
            details (for post requests mainly)
        :param params: request parameters should be transferred as list of pairs or as dictionary.
            I recommend using list of pairs since first item in pair can be not unique for some requests.
            For example: params = [ ['name', 'John Doe'], ['date', '2020-01-01'], ['date', '2021-11-19'] ]
        :param void: bool value, equal False if we expect response from server and True if we don't expect response.
            default values False
        """
        if json is None:
            json = {"apiKey":self.api_key}
        elif(type(json)==dict):
            json["apiKey"] = self.api_key

        if(headers == "getTokenMode"):
            headers = None
        elif(headers == "tokenOnlyMode"):
            headers = {"x-access-token":self.token}
        elif(type(headers)==dict):
            headers["x-access-token"] = self.token

        try:
            r = requests.request(
                method=method,
                url=url,
                json=json,
                headers=headers,
                params=params,
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
            print(f"Server error message: {r.json()['code']}")
            print(r.json())
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)
        if not void:
            return r.json()

    # Authorization:
    def _get_token(self):
        """
        Авторизация. Получение токена для работы с API.
        Ключи API вы можете создавать и просматривать в разделе CRM "Мой Класс" - "Настройки - API".
         ( https://app.moyklass.com/settings/settings/api )

        Authorization. Obtaining a token for working with the API.
        You can create and view API keys in the CRM section "My Class" - "Settings - API".
        ( https://app.moyklass.com/settings/settings/api )
        """
        url = "https://api.moyklass.com/v1/company/auth/getToken"
        token = self.__request(method='POST', url=url, headers='getTokenMode')['accessToken']
        if(self.print_Flag):
            print(f"Token obtained")
        return token

    def _refresh_token(self):
        """
        Генерирует новый токен, текущий токен при этом продолжает действовать.

        Generates a new token, old token continues to work.
        """
        url = "https://api.moyklass.com/v1/company/auth/refreshToken"
        new_token = self.__request(method='POST', url=url)['accessToken']
        if (self.print_Flag):
            print(f"Token refreshed")
        return new_token

    def _revoke_token(self):
        """
        Удаляет существующий токен. Токен передается в заголовке x-access-token

        Revokes the existing token. The token is passed in the x-access-token header.
        """
        url = "https://api.moyklass.com/v1/company/auth/revokeToken"
        self.__request(method='POST', url=url, headers='default', void=True)
        if (self.print_Flag):
            print("Token revoked")

    # Company ( Компания )
    def get_company_branches(self):
        """
        Возвращает список филиалов

        Returns a list of company branches
        """
        url = "https://api.moyklass.com/v1/company/filials"
        return self.__request(method = 'GET', url=url)

    def get_company_rooms(self):
        """
        Возвращает список аудиторий компании

        Returns a list of company audiences
        """
        url = "https://api.moyklass.com/v1/company/rooms"
        return self.__request(method = 'GET', url=url)

    # Managers ( Сотрудники )
    def get_company_managers(self):
        """
        Возвращает список сотрудников

        Returns a list of company employees
        """
        url = "https://api.moyklass.com/v1/company/managers"
        return self.__request(method = 'GET', url=url)

    def create_manager(self, manager_info : dict):
        """
        Создает нового сотрудника и возвращает его в формате JSON ( dict )

        Creates new manager and return it in form of JSON ( dict )

        :param manager_info:
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
        resp = self.__request(method = 'POST', url=url, json=manager_info)
        if (self.print_Flag):
            print('Manager created')
        return resp

    def get_manager_info(self, managerId):
        """
        Возвращает информацию о сотруднике

        Returns info about the manager

        :param managerId: ID сотрудника
        """
        url = f"https://api.moyklass.com/v1/company/managers/{managerId}"
        return self.__request(method = 'GET', url=url)

    def delete_manager(self, managerId, replaceToManagerId):
        """
        Удаляет сотрудника

        Deletes manager by id

        :param managerId: ID сотрудника
        :param replaceToManagerId: ID сотрудника, на которого будут назначены все
         невыполненные задачи, предстоящие занятия, если они есть, и клиенты удаляемого сотрудника.
        """
        url = f"https://api.moyklass.com/v1/company/managers/{managerId}"
        json = { "replaceToManagerId" : replaceToManagerId }
        self.__request(method='DELETE', url=url, json=json, void=True)
        if (self.print_Flag):
            print("Manager deleted")

    def change_manager(self, mid, manager_info : dict):
        """
        Изменяет сотрудника и возвращает его обновленные данные в форме JSON ( dict )

        Changes manager info and return it in form of JSON ( dict )

        :param mid: ID сотрудника
        :param manager_info: Новые данные сотрудника ( list of all data fields can be found in create_manager function )
        Required fields:
            name : Полное имя [ string <= 100 characters ]
            phone : Номер телефона [ string <= 15 characters ^[0-9]{10,15}$ ]
            filials : ID филиалов сотрудника [ Array of integers <int64> non-empty ]
            roles : ID ролей сотрудника [ Array of integers <int64> non-empty ]
            enabled : Разрешен вход в CRM [ boolean ], Default: false
            color : Цвет сотрудника. Если цвет не передан при создании, он будет выбран автоматически.
                                                                                    [ string^#[A-Fa-f0-9]{6}$]
            email ( required if manager need to access CRM) : Эл. почта [ string or null <email> <= 100 characters]
            salaryFilialId (required if manager works in more than one branch): ID филиала для занесения ЗП.
                                                                                    [integer or null <int64>]
        """
        url = f"https://api.moyklass.com/v1/company/managers/{mid}"
        resp = self.__request(method = 'POST', url=url, json=manager_info)
        if (self.print_Flag):
            print('Manager updated')
        return resp

    def get_roles(self):
        """
        Возвращает список ролей сотрудников

        Returns a list of employees roles
        """
        url = "https://api.moyklass.com/v1/company/roles"
        return self.__request(method = 'GET', url=url)

    def get_role_info(self, roleId):
        """
        Возвращает информацию о роли сотрудника

        Returns info about the employee role

        roleId: ID роли сотрудника
        """
        url = f"https://api.moyklass.com/v1/company/roles/{roleId}"
        return self.__request(method = 'GET', url=url)

    def get_rates(self):
        """
        Возвращает список ставок сдельной оплаты

        Returns a list of piecework rates
        """
        url = "https://api.moyklass.com/v1/company/rates"
        return self.__request(method = 'GET', url=url)

    def get_rate_info(self, rateId):
        """
        Возвращает информацию о ставке сдельной оплаты

        Returns info about piecework rate

        :param rateId: ID ставки сдельной оплаты
        """
        url = f"https://api.moyklass.com/v1/company/rates/{rateId}"
        return self.__request(method = 'GET', url=url)

    # Users ( Ученики / Лиды )
    def get_users(self, params=None):
        """
        Производит поиск учеников в соответствии с фильтром и возвращает список учеников

        Searches for students according to the filter and return list of them

        :param params: query parameters ( фильтр поиска )
        createdAt : Дата создания. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        updatedAt : Дата изменения. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        stateChangedAt : Дата изменения статуса. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        phone : Номер телефона. Mожно указать часть номера для поиска по подстроке. [ string <= 15 characters ]
        email : Email. Можно указать часть адреса для поиска по подстроке [ string ]
        name : Имя. Можно указать часть имени для поиска по подстроке. [ string ]
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
            Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
            Default: 100
        sort : Сортировка [ string ]
            Default: "id", Enum: "id" "name" "createdAt" "updatedAt"
        sortDirection : Направление сортировки [ string ]
            Default: "asc", Enum: "asc" "desc"
        amoCRMContactId : Id контакта amoCRM [ integer <int64> ]
        bitrixContactId : Id контакта Битрикс24 [ integer <int64> ]
        includePayLink : Включить в ответ ключи оплаты [ boolean ]
            Default: false
        """
        url = "https://api.moyklass.com/v1/company/users"
        return self.__request(method = 'GET', url=url, params=params)

    def create_user(self, user_info : dict):
        """
        Создает нового ученика и возвращает его в формате JSON ( dict )

        Creates new user and return it in form of JSON ( dict )

        :param user_info:
        name ( required ) : Полное имя ученика [ string <= 100 characters ]
        email : Email ученика [ string or null <email> <= 100 characters ]
        phone : Номер телефона ученика [ string or null <= 15 characters ^[0-9]{10,15}$ ]
        advSourceId : ID информационного источника (откуда ученик узнал о компании) [ integer or null <int64> ]
        createSourceId : ID способа заведения (как заведена карточка) [ integer or null <int64> ]
        clientStateId : ID статуса клиента [ integer or null <int64> ]
        filials : ID филиалов ученика [ Array of integers <int64> ]
        responsibles : ID ответственных сотрудников ученика [ Array of integers <int64> ]
        attributes : Дополнительные атрибуты ученика [ Array of Атрибут типа select,
         по ID атрибута (object) or Атрибут типа select, по алиасу атрибута (object) or Атрибут типа phone,
          по ID атрибута (object) or Атрибут типа phone, по алиасу атрибута (object) or Атрибут типа email,
           по ID атрибута (object) or Атрибут типа email, по алиасу атрибута (object) or Атрибут прочих типов,
            по ID атрибута (object) or Атрибут прочих типов, по алиасу атрибута (object) or Атрибут типа multiselect,
             по ID атрибута (object) or Атрибут типа multiselect, по алиасу атрибута (object) ]
        """
        url = f"https://api.moyklass.com/v1/company/users"
        resp = self.__request(method = 'POST', url=url, json=user_info)
        if (self.print_Flag):
            print('Manager created')
        return resp

    def get_user_info(self, userId):
        """
        Возвращает основную информацию об ученике

        Returns basic information about a user

        userId: ID ученика
        """
        url = f"https://api.moyklass.com/v1/company/users/{userId}"
        return self.__request(method = 'GET', url=url)

    def change_user(self, userId, user_info : dict):
        """
        Изменяет информацию об ученике и возвращает его обновленные данные в форме JSON ( dict )

        Changes information about a user info and return it in form of JSON ( dict )

        :param userId: ID ученика
        :param user_info: Новые данные ученика ( list of all data fields can be found in create_user function )
        Required fields:
            name : Полное имя [ string <= 100 characters ]
        """
        url = f"https://api.moyklass.com/v1/company/users/{userId}"
        resp = self.__request(method = 'POST', url=url, json=user_info)
        if (self.print_Flag):
            print('User updated')
        return resp

    def delete_user(self, userId):
        """
        Удаляет ученика из системы. Вместе с ним удаляет также все его записи, платежи, документы и т.д.

        Removes the student from the system. Together with him, he also deletes all his records, payments,
         documents, etc.

        :param userId: ID ученика
        """
        url = f"https://api.moyklass.com/v1/company/users/{userId}"
        self.__request(method='DELETE', url=url, json=json, void=True)
        if (self.print_Flag):
            print("User deleted")

    def change_user_status(self, userId, status_info : dict):
        """
        Изменяет статус ученика

        Changes user status

        :param userId: ID ученика
        :param status_info:
        statusId ( required ) : Статус ученика [ integer <int64> ]
        statusChangeReasonId : ID причины смены статуса [ integer <int32> ]

        """
        url = f"https://api.moyklass.com/v1/company/users/{userId}"
        self.__request(method = 'POST', url=url, json=status_info, void=True)
        if (self.print_Flag):
            print('User updated')

    def change_user_attribute(self, userId, attrId, attribute_info : dict):
        """
        Изменяет информацию в атрибутах ученика

        Changes information in user attributes

        :param userId: ID ученика
        :param attrId: ID атрибута или его alias
            Example: 1 или birthday
        :param attribute_info:
        if attribute is "select" type:
            valueId ( required ) : ID значения атрибута. При передаче null атрибут удаляется.
                [ integer or null <int64> ]
        if attribute is "multiselect" type:
            valueIds ( required ) : Массив ID значений атрибута. При передаче null атрибут удаляется.
                [ Array of integers or null or null <int64> ]
        if attribute is any other type:
            value ( required ) : Значение атрибута. При передаче null атрибут удаляется.
                [ (integer or null) or (boolean or null) or (string or null) ]
        """
        url = f"https://api.moyklass.com/v1/company/users/{userId}/attribute/{attrId}"
        resp = self.__request(method = 'POST', url=url, json=attribute_info)
        if (self.print_Flag):
            print('User updated')
        return resp


    def get_joins(self, params=None):
        """
        Returns a list of joins ( requests / records ) in groups ( Список заявок )
        """
        url = "https://api.moyklass.com/v1/company/joins"
        return self.__request(method = 'GET', url=url, params=params)

    def get_joins_info(self, jid, params=None):
        """
        jid: join id
        Returns info about the join ( request / record ) ( Информация о заявке )
        """
        url = f"https://api.moyklass.com/v1/company/joins/{jid}"
        return self.__request(method = 'GET', url=url, params=params)

    def get_courses(self, params=None):
        """
        Returns a list of courses ( Список программ )
        """
        url = "https://api.moyklass.com/v1/company/courses"
        return self.__request(method = 'GET', url=url, params=params)

    def get_classes(self, params=None):
        """
        Returns a list of classes ( Список групп )
        """
        url = "https://api.moyklass.com/v1/company/classes"
        return self.__request(method = 'GET', url=url, params=params)

    def get_class_info(self, cid, params=None):
        """
        cid: class id
        Returns info about the class ( Информация о группе )
        """
        url = f"https://api.moyklass.com/v1/company/classes/{cid}"
        return self.__request(method = 'GET', url=url, params=params)

    def get_lessons(self, params=None):
        """
        Returns a list of lessons ( Список занятий )
        """
        url = "https://api.moyklass.com/v1/company/lessons"
        return self.__request(method = 'GET', url=url, params=params)

    def get_lesson_info(self, lid, params=None):
        """
        lid: lesson id
        Returns info about the lesson ( Информация о занятии )
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lid}"
        return self.__request(method = 'GET', url=url, params=params)

    def get_lesson_records(self, params=None):
        """
        Returns a list of lessonRecords ( Список записей на занятия )
        """
        url = "https://api.moyklass.com/v1/company/lessonRecords"
        return self.__request(method = 'GET', url=url, params=params)

    def get_lesson_record_info(self, lrid, params=None):
        """
        lrid: lesson record id
        Returns info about the lesson record ( Информация о записи на занятие )
        """
        url = f"https://api.moyklass.com/v1/company/lessonRecords/{lrid}"
        return self.__request(method = 'GET', url=url, params=params)

    def get_(self, params=None):
        """
        Returns a list of
        """
        url = ""
        return self.__request(method = 'GET', url=url, params=params)

    def get__info(self, id, params=None):
        """
        id:  id
        Returns info about the  ( Информация о  )
        """
        url = f"/{id}"
        return self.__request(method = 'GET', url=url, params=params)

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