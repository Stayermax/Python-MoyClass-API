# coding=utf-8
import os
import math
import requests
import pandas as pd
from datetime import datetime
import pickle as pkl


class MoyClassCompanyAPI:
    """
    moyclass.com API implementation by Vitaly Pankratov.
    For contacts: vitalkrat@gmail.com
    """

    def __init__(self, api_key):

        self.api_key = api_key  # your access key
        self.print_Flag = True
        self.token = self._get_token()

    @staticmethod
    def data_load(method, entity_name, params=None, load_new_data=True):
        """
        Функция загружает объекты данных и передает их во датафрейм. Датафрейм затем сохраняется как pickle файл и
          может быть загружен в следующий раз, когда вы запустите код
          (мы используем метод pickle.dump, а не pandas.to_csv, чтобы сохранить типы столбцов df)

        Function loads data entities and transfers them into dataframe. Dataframe then saved as pickle file and
         can be loaded next time you run the code
          (we use pickle.dump and not pandas.to_csv method in order to save types of df columns)

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
        :param params: list of query parameters ( options can be seen on https://api.moyklass.com/ for each entity_name)
        :param load_new_data: if True loads data from the server. Otherwise tries to find corresponding pickle
         file in 'saved_data' folder

        :return: dataframe with data
        """
        if (not os.path.exists('saved_data')):
            os.mkdir('saved_data')
        data_path = f"saved_data/{entity_name}_df.pkl"
        if (os.path.exists(data_path) and load_new_data == False):
            with open(data_path, 'rb') as f:
                df = pkl.load(f)
            print(f"{entity_name}_df is loaded from file")
        else:
            page_entities_num = 100  # default value

            # add limit parameter in case it's not in the params
            if (params != None):
                has_limit = False
                for param in params:
                    if (param[0] == 'limit'):
                        page_entities_num = param[1]
                        has_limit = True
                if (not has_limit):
                    params.append(['limit', page_entities_num])
            else:
                params = [['limit', page_entities_num]]

            first_response = method(params)
            if (type(first_response) == dict):
                items_num = first_response['stats']['totalItems']
                print(f"Number of {entity_name} with requested params: {items_num}")
                pages_num = math.ceil(items_num / page_entities_num)
                start = datetime.now()
                full_list = []
                for i in range(pages_num):
                    full_list += method(params + [['offset', f'{page_entities_num * i}']])[entity_name]
                df = pd.DataFrame(full_list)
                print(
                    f"{entity_name[0].upper()}{entity_name[1:]} data loaded in {(datetime.now() - start).seconds} seconds ")
            else:
                print(entity_name)
                df = pd.DataFrame(first_response)
            with open(data_path, 'wb') as f:
                pkl.dump(df, f)
        return df

    # General request function :
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

    # Авторизация ( Authorization )
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

    # Компания ( Company )
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

    # Сотрудники ( Managers )
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

    # Ученики / Лиды ( Users )
    def get_users(self, params=None):
        """
        Производит поиск учеников в соответствии с фильтром и возвращает список учеников

        Searches for students according to the filter and return list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
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
            print('User created')
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

        Removes the user from the system. Together with him, he also deletes all his records, payments,
         documents, etc.

        :param userId: ID ученика
        """
        url = f"https://api.moyklass.com/v1/company/users/{userId}"
        self.__request(method='DELETE', url=url, void=True)
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
        url = f"https://api.moyklass.com/v1/company/users/{userId}/status"
        self.__request(method = 'POST', url=url, json=status_info, void=True)
        if (self.print_Flag):
            print('User status updated')

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
            print('User attribute updated')
        return resp

    # Платежи ( Payments )
    def get_payments(self, params=None):
        """
        Производит поиск заявок платежей в соответствии с фильтром и возвращает их список

        Searches for payment requests according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        createdAt : Дата создания. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        date : Дата платежа. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону [ Array of strings <date> <= 2 characters ]
        summa : Сумма платежа. Списания и возвраты указываются с минусом. [ Array of numbers <= 2 characters ]
        invoiceId : Id счета [ integer <int64> ]
        optype : Тип операции. income - входящий платеж, debit - списание,
         refund - возврат [ Array of strings <= 3 characters ]
         Items Enum: "income" "debit" "refund"
        paymentTypeId : Тип платежа [ integer ]
        includeUserSubscriptions : Включить в ответ абонементы ученика [ boolean ]
         Default: false
        userId : ID ученика [ integer <int64> ]
        filialId : ID филиала. [ Array of integers <int64> ]
        appendInvoices : Возвратить вместе с платежами данные счетов [ boolean ]
         Default: false
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        """
        url = "https://api.moyklass.com/v1/company/payments"
        return self.__request(method = 'GET', url=url, params=params)

    def create_payment(self, payment_info : dict):
        """
        Добавляет платеж клиенту. В этом методе можно добавить входящий платеж (income) и возврат (refund).
         Функция возвращает платеж в формате JSON ( dict )

        Creates a payment to the user profile. In this method, you can add an incoming payment (income) and
        a return (refund). The function returns the payment in JSON format (dict)

        :param payment_info:
        userId ( required ): ID ученика [ integer <int64> ]
        date ( required ): Дата платежа [ string <date> ]
        summa ( required ): Сумма [ number <double> ]
        userSubscriptionId : ID абонемента [ integer or null <int64> ]
        optype ( required ): Тип операции. income - приход, debit - списание, refund - возврат [ string ]
        if (optype = 'income'):
            income : Комментарий [ comment ]
            paymentTypeId ( required ): number [ number ]
        if (optype = 'debit'):
            comment : Комментарий [ string or null ]
            invoiceId ( required ): Id счета для списания [ number ]
        if (optype = 'refund'):
            comment : Комментарий [ string or null ]
        """
        url = f"https://api.moyklass.com/v1/company/payments"
        resp = self.__request(method = 'POST', url=url, json=payment_info)
        if (self.print_Flag):
            print('Payment created')
        return resp

    def get_payment_info(self, paymentId):
        """
        Возвращает информацию о платеже

        Returns information about a payment

        paymentId: ID платежа
        """
        url = f"https://api.moyklass.com/v1/company/payments/{paymentId}"
        return self.__request(method = 'GET', url=url)

    def change_payment(self, paymentId, payment_info : dict):
        """
        Изменяет платеж и возвращает его обновленные данные в форме JSON ( dict ).
         Применяется только к приходам (optype=income), для других типов платежей будет возвращен код 403

        Modifies the payment and returns its updated data in JSON (dict) form.
          Applies only to income (optype = income), for other types of payments the code 403 will be returned

        :param paymentId: ID платежа
        :param payment_info: Новые данные платежа
        payment_info fields:
            date ( required ) : Дата платежа [ date ]
            summa ( required ): Сумма [ number <double> ]
            paymentTypeId ( required ): Id типа оплаты [ number ]
            comment : Комментарий [ string or null ]
        """
        url = f"https://api.moyklass.com/v1/company/payments/{paymentId}"
        resp = self.__request(method = 'POST', url=url, json=payment_info)
        if (self.print_Flag):
            print('Payment updated')
        return resp

    def delete_payment(self, paymentId):
        """
        Удаляет платеж из системы.

        Removes the payment from the system.

        :param paymentId: ID платежа
        """
        url = f"https://api.moyklass.com/v1/company/payments/{paymentId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("Payment deleted")

    # Счета ( Invoices ) # todo: check on my CRM
    def get_invoices(self, params=None):
        """
        Производит поиск счетов в соответствии с фильтром и возвращает их список

        Searches for invoices according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        createdAt : Дата создания. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        payUntil : Срок оплаты счета. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону [ Array of strings <date> <= 2 characters ]
        price : Сумма счета. [ Array of numbers <= 2 characters ]
        userSubscriptionId : ID абонемента ученика [ integer <int64> ]
        joinId : ID записи в группу [ integer <int64> ]
        includeUserSubscriptions : Включить в ответ абонементы ученика [ boolean ]
         Default: false
        userId : ID ученика [ integer <int64> ]
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        """
        url = "https://api.moyklass.com/v1/company/invoices"
        return self.__request(method = 'GET', url=url, params=params)

    def get_invoice_info(self, invoiceId):
        """
        Возвращает информацию о счете

        Returns information about a invoice

        paymentId: ID платежа
        """
        url = f"https://api.moyklass.com/v1/company/invoices/{invoiceId}"
        return self.__request(method = 'GET', url=url)

    def change_invoice(self, invoiceId, invoice_info : dict):
        """
        Изменяет счет и возвращает его обновленные данные в форме JSON ( dict ).

        Modifies the invoice and returns its updated data in JSON (dict) form.

        :param invoiceId: ID счета
        :param invoice_info: Новые данные счета
        invoice_info fields:
        payUntil ( required ): Срок оплаты счета [ string <date> ]
        comment : Комментарий [ string or null ]
        """
        url = f"https://api.moyklass.com/v1/company/invoices/{invoiceId}"
        resp = self.__request(method = 'POST', url=url, json=invoice_info)
        if (self.print_Flag):
            print('Invoice updated')
        return resp

    def delete_invoices(self, invoiceId):
        """
        Удаляет платеж из системы.

        Removes the payment from the system.

        :param invoiceId: ID платежа
        """
        url = f"https://api.moyklass.com/v1/company/invoices/{invoiceId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("Invoice deleted")

    # Заявки / Записи ( Joins ) # todo: check on my CRM
    def get_joins(self, params=None):
        """
        Возвращает список заявок (записей) в группы

        Returns a list of joins ( requests / records ) in groups

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fields:
        createdAt : Дата создания. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        updatedAt : Дата изменения. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        stateChangedAt : Дата изменения статуса. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        filialId : ID филиала. [ Array of integers <int64> ]
        classId : ID группы [ Array of integers <int64> ]
        statusId : Статус записи [ integer ]
        userId : ID ученика [ integer <int64> ]
        managerId : ID сотрудника [ integer <int64> ]
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        sort : Сортировка [ string ]
         Default: "id", Enum: "id" "createdAt" "updatedAt"
        sortDirection : Направление сортировки [ string ]
         Default: "asc", Enum: "asc" "desc"

        Process finished with exit code 0

        """
        url = "https://api.moyklass.com/v1/company/joins"
        return self.__request(method = 'GET', url=url, params=params)

    def create_join(self, join_info : dict):
        """
        Добавляет платеж клиенту. В этом методе можно добавить входящий платеж (income) и возврат (refund).
         Функция возвращает платеж в формате JSON ( dict )

        Creates a payment to the user profile. In this method, you can add an incoming payment (income) and
        a return (refund). The function returns the payment in JSON format (dict)

        :param join_info:
        userId ( required ): ID ученика [ integer <int64> ]
        classId ( required ): ID группы [ integer <int64> ]
        price : Цена (для групп с разовой оплатой) [ number or null <double> ]
        statusId ( required ): Статус заявки [ integer <int64> ]
        statusChangeReasonId : ID причины смены статуса [ integer or null <int32> ]
        autoJoin : Автоматически записывать в статусе "Учится" на все занятия в группе [ boolean ]
         Default: true
        remindDate : Срок оплаты долга [ string or null <date> ]
        remindSum : Сумма долга к оплате [ number or null <double> ]
        managerId : ID сотрудника, который создал заявку [ integer or null <int64> ]
        comment : Комментарий [ string or null ]
        advSourceId : ID информационного источника (откуда ученик узнал о компании) [ integer or null <int64> ]
        createSourceId : ID способа заведения (как заведена карточка) [ integer or null <int64> ]
        params : Дополнительные параметры заявки [ object ]
            invoice : Правила создания счета. Если не указаны, то берутся из настроек группы [ object or null ]
                autoCreate : Создавать ли счет автоматически [ boolean ]
                createRule : Когда создавать счет. Актуально при autoCreate=true. create - создать счет при
                 создании заявки, setStatus - создать счет при установке статуса [ string ]
                 Enum: "create" "setStatus"
                joinStateId : Статусы заявки, при установке которых будет создан счет. Актуально при
                 createRule=setStatus [ Array of numbers or null ]
                payDateType : Правила установки срока оплаты. relative - дата определяется относительно даты
                 создания, exact - устанавливается точная дата оплаты [ string or null ]
                 Enum: "retative" "exact"
                payDateDays : Количество дней, через сколько нужно оплатить счет. Например, если сегодня 2020-01-01,
                 и payDateDays=3, то срок оплаты будет установлен в 2020-01-04. Актуально при
                 payDateType=relative [ number or null ]
                payDate : Срок оплаты счета. Актуально при payDateType=exact [ string or null <date> ]
        """
        url = f"https://api.moyklass.com/v1/company/joins"
        resp = self.__request(method = 'POST', url=url, json=join_info)
        if (self.print_Flag):
            print('Join created')
        return resp

    def get_joins_info(self, joinId):
        """
        Возвращает информацию о заявке

        Returns information about a join

        joinId: ID заявки
        """
        url = f"https://api.moyklass.com/v1/company/joins/{joinId}"
        return self.__request(method = 'GET', url=url)

    def change_join(self, joinId, join_info : dict):
        """
        Изменяет основную информацию по заявке и возвращает ee обновленные данные в форме JSON ( dict ).

        Modifies the join and returns its updated data in JSON (dict) form.

        :param joinId: ID счета
        :param join_info: Новые данные счета
        invoice_info fields:
        price ( required ): Цена (для групп с разовой оплатой) [ number <double> ]
        statusId ( required ): Статус заявки [ integer <int64> ]
        statusChangeReasonId ( required ): ID причины смены статуса [ integer or null <int32> ]
        autoJoin ( required ): Автоматически записывать в статусе "Учится" на все занятия в группе [ boolean ]
         Default: true
        managerId : ID сотрудника [ integer or null <int64> ]
        comment ( required ): Комментарий [ string or null ]
        advSourceId ( required ): ID информационного источника (откуда ученик узнал о компании)
                                                                                    [ integer or null <int64> ]
        createSourceId ( required ): ID способа заведения (как заведена карточка) [ integer or null <int64> ]
        params	: Дополнительные параметры заявки [ object ]
            invoice : Правила создания счета. Если не указаны, то берутся из настроек группы [ object or null ]
                autoCreate : Создавать ли счет автоматически [ boolean ]
                createRule : Когда создавать счет. Актуально при autoCreate=true. create - создать счет при
                 создании заявки, setStatus - создать счет при установке статуса [ string ]
                 Enum: "create" "setStatus"
                joinStateId : Статусы заявки, при установке которых будет создан счет. Актуально
                 при createRule=setStatus [ Array of numbers or null ]
                payDateType : Правила установки срока оплаты. relative - дата определяется относительно даты
                 создания, exact - устанавливается точная дата оплаты [ string or null ]
                 Enum: "retative" "exact"
                payDateDays : Количество дней, через сколько нужно оплатить счет. Например, если сегодня 2020-01-01,
                 и payDateDays=3, то срок оплаты будет установлен в 2020-01-04. Актуально
                 при payDateType=relative [ number or null ]
                payDate : Срок оплаты счета. Актуально при payDateType=exact [ string or null <date> ]
        """
        url = f"https://api.moyklass.com/v1/company/joins/{joinId}"
        resp = self.__request(method = 'POST', url=url, json=join_info)
        if (self.print_Flag):
            print('Join updated')
        return resp

    def delete_join(self, joinId):
        """
        Удаляет заявку из системы.

        Removes the join from the system.

        :param joinId: ID заявки
        """
        url = f"https://api.moyklass.com/v1/company/joins/{joinId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("Join deleted")

    def change_join_status(self, joinId, status_info: dict):
        """
        Изменяет статус заявки

        Changes join status

        :param joinId: ID заявки
        :param status_info:
        statusId ( required ) : Статус заявки [ integer <int64> ]
        statusChangeReasonId : ID причины смены статуса. Для изменения статуса заявки на "Отказался" используется
         набор причин клиента [ integer <int32> ]

        """
        url = f"https://api.moyklass.com/v1/company/joins/{joinId}/status"
        self.__request(method='POST', url=url, json=status_info, void=True)
        if (self.print_Flag):
            print('Join status updated')

    def change_join_tags(self, joinId, tags: dict):
        """
        Изменяет теги заявки

        Changes join tags

        :param joinId: ID ученика
        :param tags: обновленные теги заявки
        tags fields:
        tags ( required ) : Id тегов [ Array of integers <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/joins/{joinId}/tags"
        resp = self.__request(method='POST', url=url, json=tags)
        if (self.print_Flag):
            print('Join tags were updated')
        return resp

    # Задачи ( Tasks ) # todo: check on my CRM
    def get_tasks(self, params=None):
        """
        Производит поиск задач в соответствии с фильтром и возвращает их список

        Searches for tasks according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        createdAt : Дата создания. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        filialId : ID филиала. [ Array of integers <int64> ]
        classId : ID группы [ Array of integers <int64> ]
        userId : ID ученика [ integer <int64> ]
        managerId : ID сотрудника [ integer <int64> ]
        isComplete : Статус задачи, завершена или нет. [ boolean ]
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        """
        url = "https://api.moyklass.com/v1/company/tasks"
        return self.__request(method='GET', url=url, params=params)

    def create_task(self, task_info: dict):
        """
        Создает новую задачу. Функция возвращает задачу в формате JSON ( dict )

        Creates a new task. The function returns the task in JSON format (dict)

        :param task_info:
        body ( required ): Текст задачи [ string <= 250 characters ]
        beginDate ( required ): Начало задачи [ string <date-time> ]
        endDate ( required ): Окончание задачи [ string <date-time> ]
        isAllDay : Задача на весь день [ boolean ]
         Default: false
        isComplete : Задача выполнена [ boolean ]
         Default: false
        reminds : За сколько времени напомнить о задаче (в миллисекундах) [ Array of integers or null <int64> ]
        managerIds : Список id ответственных сотрудников (если одновременно указаны managerId и
         managerIds, то используется managerIds) [ Array of integers <int64> ]
        userId : ID ученика [ integer or null <int64> ]
        ownerId : ID сотрудника, который создал задачу, null при автоматическом создании [ integer or null <int64> ]
        classIds : Список ID групп [ Array of integers or null <int64> ]
        filialIds : Список ID филиалов [ Array of integers or null <int64> ]
        categoryId : ID категории задачи [ integer or null <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/tasks"
        resp = self.__request(method='POST', url=url, json=task_info)
        if (self.print_Flag):
            print(' created')
        return resp

    def get_task_info(self, taskId):
        """
        Возвращает информацию о задаче

        Returns information about a task

        paymentId: ID задачи
        """
        url = f"https://api.moyklass.com/v1/company/tasks/{taskId}"
        return self.__request(method='GET', url=url)

    def change_task(self, taskId, _info: dict):
        """
        Изменяет задачу и возвращает его обновленные данные в форме JSON ( dict ).

        Modifies the task and returns its updated data in JSON (dict) form.

        :param taskId: ID задачи
        :param _info: Новые данные задачи
        payment_info fields:
        body ( required ): Текст задачи [ string <= 250 characters ]
        beginDate ( required ): Начало задачи [ string <date-time> ]
        endDate ( required ): Окончание задачи [ string <date-time> ]
        isAllDay : Задача на весь день [ boolean ]
         Default: false
        isComplete : Задача выполнена [ boolean ]
         Default: false
        reminds : За сколько времени напомнить о задаче (в миллисекундах) [ Array of integers or null <int64> ]
        managerIds : Список id ответственных сотрудников (если одновременно указаны managerId
         и managerIds, то используется managerIds) [ Array of integers <int64> ]
        userId : ID ученика [ integer or null <int64> ]
        ownerId : ID сотрудника, который создал задачу, null при автоматическом создании [ integer or null <int64> ]
        classIds : Список ID групп [ Array of integers or null <int64> ]
        filialIds : Список ID филиалов [ Array of integers or null <int64> ]
        categoryId : ID категории задачи [ integer or null <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/tasks/{taskId}"
        resp = self.__request(method='POST', url=url, json=_info)
        if (self.print_Flag):
            print('Task updated')
        return resp

    def delete_task(self, taskId):
        """
        Удаляет задачу из системы.

        Removes the task from the system.

        :param taskId: ID задачи
        """
        url = f"https://api.moyklass.com/v1/company/tasks/{taskId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("Task deleted")

    # Группы ( Courses ) # todo: check on my CRM
    def get_courses(self, params=None):
        """
        Возвращает список программ обучения

        Returns a list of courses

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        includeClasses : Включить в ответ группы [ boolean ]
         Default: false
        """
        url = "https://api.moyklass.com/v1/company/courses"
        return self.__request(method = 'GET', url=url, params=params)

    def get_classes(self):
        """
        Возвращает список групп (наборов)

        Returns a list of classes
        """
        url = "https://api.moyklass.com/v1/company/classes"
        return self.__request(method = 'GET', url=url)

    def get_class_info(self, classId):
        """
        Возвращает основную информацию о группе

        Returns information about a

        :param classId: ID группы
        """
        url = f"https://api.moyklass.com/v1/company/classes/{classId}"
        return self.__request(method = 'GET', url=url)

    def add_file_to_lesson(self, lessonId, file_type, file_data : dict ):
        """
        Добавляет файл задания на занятие

        Adds a task file to the lesson

        :param lessonId: ID занятия [ integer <int64> ]
        :param file_type: Тип задания (Домашнее / за занятие) , Enum: "home" "lesson"
        :param file_data:
        data : Данные в формате base64 [ string ]
        original : Имя файла [ string ]
        mimetype : mimetype файла [ string ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/task/{file_type}/files"
        self.__request(method = 'POST', url=url, json=file_data, void=True)
        if (self.print_Flag):
            print('File added to the lesson')

    def get_task_files(self, lessonId, file_type):
        """
        Возвращает массив файлов прикрепленных к заданию

        Returns an array of files attached to the task

        :param lessonId: ID занятия [ integer <int64> ]
        :param file_type: Тип задания (Домашнее / за занятие) , Enum: "home" "lesson"
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/task/{file_type}/files"
        return self.__request(method = 'GET', url=url)

    def create_or_change_lesson_task(self, lessonId, file_type, text : str):
        """
        Создает или, если уже создано, изменяет задание на занятие

        Creates or, if already created, changes a task for a lesson

        :param lessonId: ID занятия [ integer <int64> ]
        :param file_type: Тип задания (Домашнее / за занятие) , Enum: "home" "lesson"
        :param text: Текст задания в формате HTML [ string ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/task/{file_type}"
        self.__request(method='POST', url=url, json=text, void=True)
        if (self.print_Flag):
            print('Task for the lesson was created or changed')

    def delete_lesson_task(self, lessonId, file_type):
        """
        Удаляет задание из системы.

        Deletes a task for a lesson from the system.

        :param lessonId: ID занятия [ integer <int64> ]
        :param file_type: Тип задания (Домашнее / за занятие) , Enum: "home" "lesson"
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/task/{type}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print('Task for the lesson was deleted')

    def create_answer_for_task(self, lessonId, answer_info: dict):
        """
        Создает ответ на задание

        Creates an answer to a task

        :param lessonId: ID занятия [ integer <int64> ]
        :param answer_info: answer data
        answer_info fields:
        userId ( required ): ID пользователя [ integer <int64> ]
        type ( required ): Тип ответа [ string ] , Enum: "home" "lesson"
        status : Статус [ string ] , Enum: "draft" "sent" "accept" "return"
        text : Текст ответа [ string or null ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer"
        self.__request(method='POST', url=url, json=answer_info, void=True)
        if (self.print_Flag):
            print('Answer for the task created')

    def get_task_answer(self, lessonId, answerId):
        """
        Возвращает ответ на задание

        Returns the answer to the task

        :param lessonId: ID занятия [ integer <int64> ]
        :param answerId: ID ответа [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer/{answerId}"
        return self.__request(method='POST', url=url, )

    # todo: AUTHORIZATIONS
    def edit_task_answer(self, lessonId, answerId, answer_info: dict):
        """
        Создает ответ на задание

        Creates an answer to a task

        :param lessonId: ID занятия [ integer <int64> ]
        :param answerId: ID ответа [ integer <int64> ]
        :param answer_info: answer data
        answer_info fields:
        text : Текст ответа [ string or null ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer/{answerId}"
        self.__request(method='POST', url=url, json=answer_info, void=True)
        if (self.print_Flag):
            print('Answer for the task edited')

    def delete_task_answer(self, lessonId, answerId):
        """
        Удаляет ответ на задание

        Deletes an answer to a task

        :param lessonId: ID занятия [ integer <int64> ]
        :param answerId: ID ответа [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer/{answerId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print('Answer for the task was deleted')

    def change_answer_status(self, lessonId, answerId, status_info: dict):
        """
        Меняет статус ответа на задание

        Changes the status of the response to the task

        :param lessonId: ID занятия [ integer <int64> ]
        :param answerId: ID ответа [ integer <int64> ]
        :param status_info: answer data
        status_info fields:
        status ( required ): Статус [ string ] , Enum: "draft" "sent" "accept" "return"
        managerId ( required ): ID преподавателя, который сменил статус [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer/{answerId}/status"
        self.__request(method='POST', url=url, json=status_info, void=True)
        if (self.print_Flag):
            print('Answer status was changed')

    def add_comment_to_answer(self, lessonId, answerId, comment_info: dict):
        """
        Меняет статус ответа на задание

        Changes the status of the response to the task

        :param lessonId: ID занятия [ integer <int64> ]
        :param answerId: ID ответа [ integer <int64> ]
        :param comment_info: answer data
        comment_info fields:
        text : Текст комментария [ string ]
        managerId : ID преподавателя, который оставил комментарий [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer/{answerId}/comment"
        self.__request(method='POST', url=url, json=comment_info, void=True)
        if (self.print_Flag):
            print('Comment to the answer was added')

    def attach_file_to_answer(self, lessonId, answerId, file_info: dict):
        """
        Прикрепляет файл к ответу на задание

        Attaches a file to a response to an assignment

        :param lessonId: ID занятия [ integer <int64> ]
        :param answerId: ID ответа [ integer <int64> ]
        :param file_info: answer data
        file_info fields:
        data : Данные в формате base64 [ string ]
        name : Имя файла [ string ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer/{answerId}/files"
        self.__request(method='POST', url=url, json=file_info, void=True)
        if (self.print_Flag):
            print('File was added to the answer')

    def delete_file_from_answer(self, lessonId, answerId, fileId):
        """
        Удаляет файла к ответу на задание

        Deletes the file to the answer to the task

        :param lessonId: ID занятия [ integer <int64> ]
        :param answerId: ID ответа [ integer <int64> ]
        :param fileId: ID файла [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer/{answerId}/files/{fileId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print('File was deleted from the answer')

    def delete_comment_from_answer(self, lessonId, answerId, commentId):
        """
        Меняет статус ответа на задание

        Changes the status of the response to the task

        :param lessonId: ID занятия [ integer <int64> ]
        :param answerId: ID ответа [ integer <int64> ]
        :param commentId: ID комментария [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/answer/{answerId}/comment/{commentId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print('Comment was deleted from the answer')

    def create_or_change_lesson_mark(self, lessonId, userId, file_type, grade_info: dict):
        """
        Создает или, если уже создано, изменяет оценку на занятие

        Creates or, if already created, changes the grade for the lesson

        :param lessonId: ID занятия [ integer <int64> ]
        :param userId: ID пользователя [ integer <int64> ]
        :param file_type: Тип оценки (За дз / за занятие) [ string ], Enum: "home" "lesson"
        :param grade_info:
        grade_info fields:
        value : Оценка 	[ number ]
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/mark/{file_type}/{userId}"
        self.__request(method='POST', url=url, json=grade_info, void=True)
        if (self.print_Flag):
            print('Grade for the lesson was created or changed')

    def delete_lesson_grade(self, lessonId, userId, file_type):
        """
        Удаляет оценку из системы.

        Removes a grade from the system.

        :param lessonId: ID занятия [ integer <int64> ]
        :param userId: ID пользователя [ integer <int64> ]
        :param file_type: Тип оценки (За дз / за занятие) [ string ], Enum: "home" "lesson"
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/mark/{file_type}/{userId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print('Mark for the lesson was deleted')

    def get_lessons(self, params=None):
        """
        Производит поиск занятий в соответствии с фильтром и возвращает их список

        Searches for lessons according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fields:
        date : Дата проведения занятий. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону [ Array of strings <date> <= 2 characters ]
        roomId : ID аудитории [ Array of integers <int64> ]
        filialId : ID филиала. [ Array of integers <int64> ]
        classId : ID группы [ Array of integers <int64> ]
        teacherId : ID сотрудника - преподавателя [ Array of integers <int64> ]
        statusId : Статус занятия. 0 - не проведено, 1 - проведено [ integer ]
        userId : ID ученика, записанного на занятие [ integer <int64> ]
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        includeRecords : Включить в ответ записи на занятия [ boolean ]
         Default: false
        includeMarks : Включить в ответ оценки к занятию [ boolean ]
         Default: false
        includeTasks : Включить в ответ задания к занятию [ boolean ]
         Default: false
        includeTaskAnswers : Включить в ответ ответы на задание [ boolean ]
         Default: false
        includeUserSubscriptions : Включить в ответ абонементы ученика [ boolean ]
         Default: false
        """
        url = "https://api.moyklass.com/v1/company/lessons"
        return self.__request(method = 'GET', url=url, params=params)

    def get_lesson_info(self, lessonId, params=None):
        """
        Возвращает информацию о занятии

        Returns information about the lesson

        :param lessonId: ID занятия [ integer <int64> ]
        :param params: query parameters [ list of pairs ]
        params fields:
        includeRecords : Включить в ответ записи на занятия [ boolean ]
         Default: false
        includeMarks : Включить в ответ оценки к занятию [ boolean ]
         Default: false
        includeTasks : Включить в ответ задания к занятию [ boolean ]
         Default: false
        includeTaskAnswers : Включить в ответ ответы на задание [ boolean ]
         Default: false
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}"
        return self.__request(method = 'GET', url=url, params=params)

    def change_lesson_status(self, lessonId, status_info: dict):
        """
        Изменяет статус занятия

        Changes the status of the lesson

        :param lessonId: ID занятия [ integer <int64> ]
        :param status_info:
        status_info fields:
        status ( required ): Статус занятия. 0 - не проведено, 1 - проведено [ integer <int64> ], Enum: 0 1
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lessonId}/status"
        self.__request(method = 'POST', url=url, json=status_info, void=True)
        if (self.print_Flag):
            print('Status for the lesson was changed')

    def get_lesson_records(self, params=None):
        """
        Производит поиск записей на занятия в соответствии с фильтром и возвращает их список

        Searches for lessons records according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fields:
        userId : ID ученика [ Array of integers <int64> <= 50 characters ]
        lessonId : ID занятия [ Array of integers <int64> <= 50 characters ]
        classId : ID группы [ Array of integers <int64> <= 50 characters ]
        date : Дата проведения занятий. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону [ Array of strings <date> <= 2 characters ]
        free : Бесплатная запись (посещение для ученика будет бесплатным) [ boolean ]
        visit : Статус посещения (true - ученик посетил занятие, false - пропустил) [ boolean ]
        test : Пробная запись на занятие [ boolean ]
        skip : Не учитывать запись в количестве занятых мест [ boolean ]
        goodReason : Уважительная причина отсутствия (true - есть уважительная причина, false - нет) [ boolean ]
        paid : Платное занятие (true - платное, false - нет) [ boolean ]
        includeUserSubscriptions : Включить в ответ абонементы ученика (работает при includeBills=true) [ boolean ]
         Default: false
        includeBills : Включить в ответ данные о списании [ boolean ]
         Default: false
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        """
        url = f"https://api.moyklass.com/v1/company/lessonRecords"
        return self.__request(method = 'GET', url=url, params=params)

    def create_lesson_record(self, lessonRecord_info=None):
        """
        Создает новую запись на занятие

        Creates a new lesson record

        :param lessonRecord_info: Информация о записи
        lessonRecord_info fields:
        userId ( required ): ID ученика [ integer <int64> ]
        lessonId ( required ): ID занятия [ integer <int64> ]
        free : Бесплатная запись (посещение для ученика будет бесплатным) [ boolean ]
         Default: false
        visit : Статус посещения (true - ученик посетил занятие, false - пропустил) [ boolean ]
         Default: false
        goodReason : Уважительная причина отсутствия (true - есть уважительная причина, false - нет) [ boolean ]
         Default: false
        test : Пробная запись на занятие [ boolean ]
         Default: false
        userSubscription : Абонемент ученика [ object (UserSubscription) ]
        """
        url = f"https://api.moyklass.com/v1/company/lessonRecords"
        resp = self.__request(method = 'POST', url=url, json=lessonRecord_info)
        if (self.print_Flag):
            print('Lesson record was created')
        return resp

    def get_lesson_record_info(self, recordId):
        """
        Возвращает информацию о записи на занятие

        Returns information about the lesson record
        recordId: ID записи
        """
        url = f"https://api.moyklass.com/v1/company/lessonRecords/{recordId}"
        return self.__request(method = 'GET', url=url)

    def change_lesson_record(self,recordId, lessonRecord_info: dict):
        """
        Изменяет информацию о записи

        Changes information about a record

        :param recordId : ID записи [ integer <int64> ]
        :param lessonRecord_info: Обновленная информация о записи
        lessonRecord_info fields:
        free : Бесплатная запись (посещение для ученика будет бесплатным) [ boolean ]
         Default: false
        visit : Статус посещения (true - ученик посетил занятие, false - пропустил) [ boolean ]
         Default: false
        goodReason : Уважительная причина отсутствия (true - есть уважительная причина, false - нет) [ boolean ]
         Default: false
        """
        url = f"https://api.moyklass.com/v1/company/lessonRecords/{recordId}"
        resp = self.__request(method = 'POST', url=url, json=lessonRecord_info)
        if (self.print_Flag):
            print('Lesson record was changed')
        return resp

    def delete_lesson_record(self,recordId):
        """
        Удаляет запись на занятие

        Deletes an entry for a lesson

        :param recordId : ID записи [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/lessonRecords/{recordId}"
        self.__request(method = 'DELETE', url=url, void=True)
        if (self.print_Flag):
            print('Lesson record was deleted')

    # todo: AUTHORIZATIONS
    def delete_lesson_answer(self,lessonId, answerId):
        """
        Удаляет ответ на задание

        Deletes the answer to the task

        :param lessonId : ID занятия [ integer <int64> ]
        :param answerId : ID ответа [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/user/lessons/{lessonId}/answer/{answerId}"
        self.__request(method = 'DELETE', url=url, void=True)
        if (self.print_Flag):
            print('Lesson record was deleted')

    # Cправочники ( advSources ) # todo: check on my CRM
    def get_advSources(self):
        """
        Возвращает список информационных источников

        Returns a list of information sources
        """
        url = "https://api.moyklass.com/v1/company/createSources"
        return self.__request(method = 'GET', url=url)

    def get_createSources(self):
        """
        Возвращает список возможных способов заведения клиентов и заявок

        Returns a list of possible ways of placing clients and orders
        """
        url = "https://api.moyklass.com/v1/company/createSources"
        return self.__request(method = 'GET', url=url)

    def get_statusReasons(self, params=None):
        """
        Производит поиск  причины изменения статуса записи в соответствии с фильтром и возвращает их список

        Searches for the reason for the change in the status of a record according to the filter and returns
         a list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fields:
        type : Тип причины [ string ], Default: "join", Enum: "join" "client"
        """
        url = "https://api.moyklass.com/v1/company/statusReasons"
        return self.__request(method = 'GET', url=url, params=params)

    def get_userAttributes(self):
        """
        Возвращает список всех доступных признаков ученика

        Returns a list of all available traits for the student
        """
        url = "https://api.moyklass.com/v1/company/userAttributes"
        return self.__request(method = 'GET', url=url)

    def get_joinStatuses(self):
        """
        Возвращает список статусов заявок

        Returns a list of order statuses
        """
        url = "https://api.moyklass.com/v1/company/joinStatuses"
        return self.__request(method = 'GET', url=url)

    def get_clientStatuses(self):
        """
        Возвращает список статусов клиентов

        Returns a list of client statuses
        """
        url = "https://api.moyklass.com/v1/company/clientStatuses"
        return self.__request(method = 'GET', url=url)

    def get_joinTags(self):
        """
        Возвращает список тегов для заявок

        Returns a list of tags for tickets
        """
        url = "https://api.moyklass.com/v1/company/joinTags"
        return self.__request(method = 'GET', url=url)

    def get_paymentTypes(self):
        """
        Возвращает типы платежей

        Returns payment types
        """
        url = "https://api.moyklass.com/v1/company/paymentTypes"
        return self.__request(method = 'GET', url=url)

    # Файлы ( Files ) # todo: check on my CRM
    def upload_free_file(self, file_info: dict):
        """
        Загрузка свободного файла

        Download a free file

        :param file_info: File data
        file_info fields:
        data : Данные в формате base64 [ string ]
        name : Имя файла [ string ]
        comment : Комментарий сотрудника [ string or null ]
        userComment : Комментарий ученика/для ученика [ string or null ]
        managerId : ID сотрудника, который прикрепляет файл [ integer <int64> ]
        visible : Флаг определяющий виден ли файл ученику [ boolean or null ]
         Default: false
        """
        url = f"https://api.moyklass.com/v1/company/files"
        self.__request(method='POST', url=url, json=file_info, void=True)
        if (self.print_Flag):
            print('Free file was uploaded')

    def get_user_files(self, userId):
        """
        Получение списка файлов пользователя

        Getting a list of user's files

        :param userId: ID ученика [ integer <int64> ]
        """
        url = "https://api.moyklass.com/v1/company/files"
        return self.__request(method='GET', url=url, json={'userId': userId})

    def download_file(self, fileId):
        """
        Получение списка файлов пользователя

        Getting a list of user's files

        :param fileId: ID файла [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/files/{fileId}"
        return self.__request(method='GET', url=url)

    def delete_file(self, fileId):
        """
        Удаляет файл  из системы.

        Removes the file from the system.

        :param fileId: ID файла [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/files/{fileId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("File was deleted")

    def edit_file(self, fileId, file_info: dict):
        """
        Редактирование файла

        File editing

        :param fileId: ID файла
        :param file_info: Новые данные файла
        payment_info fields:
        comment : Комментарий сотрудника [ string or null ]
        userComment : Комментарий ученика/для ученика [ string or null ]
        managerId : ID сотрудника, который редактирует файл [ integer or null <int64> ]
        visible : Флаг определяющий виден ли файл ученику [ boolean or null ]
         Default: false
        """
        url = f"https://api.moyklass.com/v1/company/files/{fileId}"
        self.__request(method='POST', url=url, json=file_info, void=True)
        if (self.print_Flag):
            print('File was edited')

    # Абонементы ( Subscriptions ) # todo: check on my CRM
    def get_subsciptions(self, params=None):
        """
        Производит поиск абонементов в соответствии с фильтром и возвращает их список

        Searches for subsriptions according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fields:
        createdAt : Дата создания. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        filialId : ID филиала. [ Array of integers <int64> ]
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        useDiscount : Применять скидку клиента [ boolean ]
        externalId : Пользовательский номер абонемента [ string or Array of strings ]
        subscriptionGroupingId : ID группировки абонементов. [ integer <int64> ]
        """
        url = "https://api.moyklass.com/v1/company/subscriptions"
        return self.__request(method = 'GET', url=url, params=params)

    def create_subsciption(self, subscription_info : dict):
        """
        Создает новый абонемент и возвращает его в формате JSON ( dict )

        Creates a new subscription and returns it in JSON format (dict)

        :param subscription_info: Информация об абонементе
        subscription_info fields:
        if subscription type == Безлимитный :
            name ( required ): Название [ string <= 100 characters ]
            price ( required ): Стоимость [ number <double> >= 1 ]
            filialIds : ID филиалов. [0] - все филиалы [ Array of integers <int64> ]
            subscriptionGroupingId : ID группировки абонементов. [ integer <int64> ]
            period : Срок действия [ string or null^[0-9]+ (day|month|year)$ ]
            yield ( required ): Цена за занятие [ number <double> ]
            useDiscount : Применять скидку клиента [ boolean ]
            courses : ID курсов [ Array of integers <int64> ]
            classes :  [ Array of integers <int64> ]
            params:
                courseIds : Программы, для которых доступен абонемент [ Array of numbers or null ]
                classIds : Группы, для которых доступен абонемент [ Array of numbers or null ]
        if subscription type == С фиксированным количеством посещений :
            name ( required ): Название [ string <= 100 characters ]
            visitCount ( required ): Количество занятий, 0, если абонемент безлимитный [ integer <int64> >= 1 ]
            price ( required ): Стоимость [ number <double> >= 1 ]
            filialIds : ID филиалов. [0] - все филиалы [ Array of integers <int64> ]
            period : Срок действия [ string or null^[0-9]+ (day|month|year)$ ]
            courses : ID курсов [ Array of integers <int64> ]
            classes : ID групп [ Array of integers <int64> ]
            params:
                courseIds : Программы, для которых доступен абонемент [ Array of numbers or null ]
                classIds : Группы, для которых доступен абонемент [ Array of numbers or null ]
        """
        url = f"https://api.moyklass.com/v1/company/subscriptions"
        resp = self.__request(method = 'POST', url=url, json=subscription_info)
        if (self.print_Flag):
            print('Subscription created')
        return resp

    def get_subsciption_info(self, subscriptionId):
        """
        Возвращает информацию об абонементе

        Returns information about a subscription

        :param subscriptionId: ID абонемента [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/subscriptions/{subscriptionId}"
        return self.__request(method = 'GET', url=url)

    def delete_subsciptions(self, subscriptionId):
        """
        Удаляет абонемент из системы.

        Removes the subscription from the system.

        :param subscriptionId: ID абонемента [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/subscriptions/{subscriptionId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("Subscription was deleted")

    def change_subsciption(self, subscriptionId, subscription_info : dict):
        """
        Изменяет абонемент и возвращает его обновленные данные в форме JSON ( dict ).

        Modifies the subsciption and returns its updated data in JSON (dict) form.

        :param subscriptionId: ID абонемента [ integer <int64> ]
        :param subscription_info: Новые данные абонемента
        subscription_info fields:
        if subscription type == Безлимитный :
            name ( required ): Название [ string <= 100 characters ]
            price ( required ): Стоимость [ number <double> >= 1 ]
            filialIds : ID филиалов. [0] - все филиалы [ Array of integers <int64> ]
            subscriptionGroupingId : ID группировки абонементов. [ integer <int64> ]
            period : Срок действия [ string or null^[0-9]+ (day|month|year)$ ]
            useDiscount : Применять скидку клиента [ boolean ]
            courses : ID курсов [ Array of integers <int64> ]
            classes : ID групп [ Array of integers <int64> ]
            params:
                courseIds : Программы, для которых доступен абонемент [ Array of numbers or null ]
                classIds : Группы, для которых доступен абонемент [ Array of numbers or null ]
        if subscription type == С фиксированным количеством посещений :
            name ( required ): Название [ string <= 100 characters ]
            visitCount ( required ): Количество занятий, 0, если абонемент безлимитный [ integer <int64> >= 1 ]
            price ( required ): Стоимость [ number <double> >= 1 ]
            filialIds : ID филиалов. [0] - все филиалы [ Array of integers <int64> ]
            period : Срок действия [ string or null^[0-9]+ (day|month|year)$ ]
            courses : ID курсов [ Array of integers <int64> ]
            classes : ID групп [ Array of integers <int64> ]
            params:
                courseIds : Программы, для которых доступен абонемент [ Array of numbers or null ]
                classIds : Группы, для которых доступен абонемент [ Array of numbers or null ]
        """
        url = f"https://api.moyklass.com/v1/company/subscriptions/{subscriptionId}"
        resp = self.__request(method = 'POST', url=url, json=subscription_info)
        if (self.print_Flag):
            print('Subscription updated')
        return resp

    def get_subscriptionGroupings(self, params=None):
        """
        Производит поиск группировок видов абонементов в соответствии с фильтром и возвращает их список

        Searches for subscription groupings according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fields:
        includeSubscriptions : Включить в ответ виды абонементов [ boolean ]
         Default: false
        """
        url = "https://api.moyklass.com/v1/company/subscriptionGroupings"
        return self.__request(method = 'GET', url=url, params=params)

    # Абонементы учеников ( User's Subscriptions ) # todo: check on my CRM
    def get_userSubscriptions(self, params=None):
        """
        Производит поиск абонементов учеников в соответствии с фильтром и возвращает их список

        Searches for users subscriprions according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fiels:
        userId : ID ученика [ integer <int64> ]
        managerId : ID сотрудника [ integer <int64> ]
        externalId : Пользовательский номер абонемента [ string or Array of strings ]
        courseId : ID программы группы абонемента [ integer or Array of integers ]
        classId : ID группы абонемента [ integer or Array of integers ]
        mainClassId : ID основной группы абонемента [ integer or Array of integers ]
        sellDate : Дата продажи. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону [ Array of strings <date> <= 2 characters ]
        beginDate : Дата начала действия. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону [ Array of strings <date> <= 2 characters ]
        endDate : Дата окончания действия. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону [ Array of strings <date> <= 2 characters ]
        statusId : Статус абонемента [ Array of integers ]
            1 - Не активный
            2 - Активный
            3 - Заморожен
            4 - Окончен
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        """
        url = "https://api.moyklass.com/v1/company/userSubscriptions"
        return self.__request(method = 'GET', url=url, params=params)

    def create_userSubscription(self, userSubscription_info : dict):
        """
        Создает новый абонемент ученика. Функция возвращает абонемент ученика в формате JSON ( dict )

        Creates a new student subscription. The function returns the student's subscription in JSON format (dict)

        :param userSubscription_info: Информация об абонементе ученика
        userSubscription_info fiels:
        externalId : Пользовательский номер абонемента [ string or null ]
        userId ( required ): ID ученика [ integer <int64> ]
        subscriptionId ( required ): ID вида абонемента [ integer <int64> ]
        originalPrice : Цена абонемента (без учета скидки и доп. компенсации). При создании по умолчанию будет
         взята цена основного абонемента [ number <double> ]
        discount : Скидка, % от цены абонемента [ number or null [ 0 .. 100 ] ]
        extraDiscount : Дополнительная компенсация цены абонемента [ number or null <double> >= 0 ]
        comment : Комментарий [ string or null ]
        sellDate ( required ): Дата продажи [ string <date> ]
        beginDate : Дата начала действия. Если не указан, устанавливается в текущую дату. [ string or null <date> ]
        endDate : Дата окончания действия [ string or null <date> ]
        classIds ( required ): Группы, в которых действует абонемент [ Array of integers <int64> ]
        period : Срок действия. При создании по умолчанию значение будет взято из основного
         абонемента [ string or null^[0-9]+ (day|month|year)$ ]
        visitCount : Количество занятий в абонементе. При создании по умолчанию значение будет взято из основного
         абонемента [ integer or null <int64> <= 200 ]
        mainClassId ( required ): ID основной группы абонемента [ integer <int64> ]
        managerId : ID менеджера [ integer or null <int64> ]
        autodebit : Автоматически списывать средства с баланса [ boolean ]
         Default: true
        burnLeftovers : Списывать остатки абонемента после окончания его срока [ boolean ]
         Default: true
        useLeftovers : Использовать оставшиеся посещения абонемента после окончания его срока автоматически [ boolean ]
        Default: true
        """
        url = f"https://api.moyklass.com/v1/company/userSubscriptions"
        resp = self.__request(method = 'POST', url=url, json=userSubscription_info)
        if (self.print_Flag):
            print("User's subscriptions was created")
        return resp

    def get_userSubscription_info(self, userSubscriptionId):
        """
        Возвращает информацию об абонементе ученика

        Returns information about a user subscription

        :param userSubscriptionId: ID абонемента ученика [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/userSubscriptions/{userSubscriptionId}"
        return self.__request(method = 'GET', url=url)

    def delete_userSubscription(self, userSubscriptionId):
        """
        Удаляет абонемент ученика  из системы.

        Removes the user subscription from the system.

        :param userSubscriptionId: ID абонемента ученика [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/userSubscriptions/{userSubscriptionId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("User's subscription was deleted")

    def change_userSubscription(self, userSubscriptionId, userSubscriptionId_info : dict):
        """
        Изменяет абонемент ученика и возвращает его обновленные данные в форме JSON ( dict ).

        Modifies the user's subscription and returns its updated data in JSON (dict) form.

        :param userSubscriptionId: ID абонемента ученика [ integer <int64> ]
        :param userSubscriptionId_info: Новые данные абонемента ученика
        payment_info fields:
        externalId : Пользовательский номер абонемента [ string or null ]
        sellDate ( required ): Дата продажи [ string <date> ]
        beginDate ( required ): Дата начала действия [ string <date> ]
        endDate : Дата окончания действия [ string or null <date> ]
        price ( required ): Стоимость при продаже [ number <double> >= 0 ]
        comment : Комментарий [ string ]
        classIds ( required ): Группы, в которых действует абонемент [ Array of integers <int64> ]
        period : Срок действия [ string or null^[0-9]+ (day|month|year)$ ]
        visitCount : Количество занятий в абонементе [ integer or null <int64> <= 200 ]
         Default: 0
        mainClassId ( required ): ID основной группы абонемента [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/userSubscriptions/{userSubscriptionId}"
        resp = self.__request(method = 'POST', url=url, json=userSubscriptionId_info)
        if (self.print_Flag):
            print("User's subscriptions was updated")
        return resp

    def change_userSubscription_status(self, userSubscriptionId, userSubscription_status_info : dict):
        """
        Изменяет статус абонемента ученика и возвращает его обновленные данные в форме JSON ( dict ).

        Changes the status of the user's subscription and returns its updated data in JSON (dict) form.

        :param userSubscriptionId: ID абонемента ученика
        :param userSubscription_status_info: Статус абонемента ученика
        payment_info fields:
        statusId ( required ) : Статус абонемента [ integer <int64> ], Enum: 1 2
            1 - Не активный
            2 - Активный
        """
        url = f"https://api.moyklass.com/v1/company/userSubscriptions/{userSubscriptionId}/status"
        resp = self.__request(method = 'POST', url=url, json=userSubscription_status_info)
        if (self.print_Flag):
            print("User's subscription status was updated")
        return resp

    def change_userSubscription_freeze(self, userSubscriptionId, userSubscription_freeze_info : dict):
        """
        Изменяет заморозку абонемента ученика и возвращает его обновленные данные в форме JSON ( dict ).

        Changes the freeze of the users's subscription and returns its updated data in JSON (dict) form.

        :param userSubscriptionId: ID абонемента ученика [ integer <int64> ]
        :param userSubscription_freeze_info: Заморозка абонемента ученика
        payment_info fields:
        freezeFrom ( required ): Дата начала заморозки [ string <date> ]
        freezeTo ( required ): Дата окончания заморозки [ string <date> ]
        """
        url = f"https://api.moyklass.com/v1/company/userSubscriptions/{userSubscriptionId}/freeze"
        resp = self.__request(method = 'POST', url=url, json=userSubscription_freeze_info)
        if (self.print_Flag):
            print("User's subscription freeze was updated")
        return resp

    def delete_userSubscription_freeze_status(self, userSubscriptionId):
        """
        Удаляет заморозку абонемента ученика и возвращает его обновленные данные в форме JSON ( dict ).

        Removes the freeze of the user's subscription  and returns its updated data in JSON (dict) form.

        :param userSubscriptionId: ID абонемента ученика [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/userSubscriptions/{userSubscriptionId}/freeze"
        resp = self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("User's subscription freeze was deleted")
        return resp

    # Комментарии учеников ( User's Comments ) # todo: check on my CRM
    def get_userComments(self, params=None):
        """
        Производит поиск комментариям учеников в соответствии с фильтром и возвращает их список

        Searches for users' comments according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fiels:
        createdAt : Дата создания. Если указана одна дата, то происходит поиск только по одной дате.
         Если указаны 2 даты, то производится поиск по диапазону. [ Array of strings <date> <= 2 characters ]
        classId : ID группы [ Array of integers <int64> ]
        userId : ID ученика [ integer <int64> ]
        managerId : ID сотрудника [ integer <int64> ]
        lessonId : ID занятия [ Array of integers <int64> ]
        offset : Номер первой записи. Используется для постраничного вывода. [ integer ]
         Default: 0
        limit : Максимальное количество возвращаемых строк. Используется для постраничного вывода. [ integer ]
         Default: 100
        """
        url = "https://api.moyklass.com/v1/company/userComments"
        return self.__request(method = 'GET', url=url, params=params)

    def create_userComment(self, userComment_info : dict):
        """
        Создает новый комментарий. Функция возвращает комментарий в формате JSON ( dict )

        Creates a new comment. The function returns a comment in JSON format (dict)

        :param userComment_info: Комментарий
        userComment_info fields:
        comment ( required ): Текст комментария [ string ]
        showToUser : Видимость комментария для ученика [ boolean ]
         Default: true
        userId ( required ): ID пользователя [ integer <int64> ]
        lessonId : ID занятия [ integer or null <int64> ]
        classId : ID группы [ integer or null <int64> ]
        managerId : ID менеджера [ integer or null <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/userComments"
        resp = self.__request(method = 'POST', url=url, json=userComment_info)
        if (self.print_Flag):
            print("User's comment was created")
        return resp

    def change_userComment(self, commentId, userComment_info : dict):
        """
        Изменяет комментарий и возвращает его обновленные данные в форме JSON ( dict ).

        Modifies the comment and returns its updated data in JSON (dict) form.

        :param commentId: ID комментария [ integer or null <int64> ]
        :param userComment_info: Новые данные комментария
        payment_info fields:
        comment ( required ): Текст комментария [ string ]
        showToUser : Видимость комментария для ученика [ boolean ], Default: true
        lessonId : ID занятия [ integer or null <int64> ]
        classId : ID группы [ integer or null <int64> ]
        managerId : ID менеджера [ integer or null <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/userComments/{commentId}"
        resp = self.__request(method = 'POST', url=url, json=userComment_info)
        if (self.print_Flag):
            print("User's comment was updated")
        return resp

    def get_userComment_info(self, commentId):
        """
        Возвращает информацию о комментарии

        Returns information about a comment

        :param commentId: ID комментария [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/userComments/{commentId}"
        return self.__request(method = 'GET', url=url)

    def delete_userComment(self, commentId):
        """
        Удаляет комментарий из системы.

        Removes the comment from the system.

        :param commentId: ID комментария [ integer <int64> ]
        """
        url = f"https://api.moyklass.com/v1/company/userComments/{commentId}"
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print("User's comment was deleted")

    # Документы ( Contracts ) # todo: check on my CRM
    def get_(self, params=None):
        """
        Производит поиск документов в соответствии с фильтром и возвращает их список

        Searches for сontracts according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fiels:
        userId : ID ученика [ integer <int64> ]
        """
        url = "https://api.moyklass.com/v1/company/contracts"
        return self.__request(method = 'GET', url=url, params=params)

class MoyClassUserAPI:

    def __init__(self, api_key):

        self.api_key = api_key  # your access key
        self.print_Flag = True
        self.token = self._get_token()

    # General request function :
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
            json = {"apiKey": self.api_key}
        elif (type(json) == dict):
            json["apiKey"] = self.api_key

        if (headers == "getTokenMode"):
            headers = None
        elif (headers == "tokenOnlyMode"):
            headers = {"x-access-token": self.token}
        elif (type(headers) == dict):
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

    # Авторизация ( Authorization )

    # Ученики / Лиды ( Users )

    # Платежи ( Payments )

    # Занятия ( Lessons )

    # Файлы ( Files )

    # Generic :

    def get_(self, params=None):
        """
        Производит поиск  в соответствии с фильтром и возвращает их список

        Searches for  according to the filter and returns list of them

        :param params: query parameters ( фильтр поиска ) [ list of pairs ]
        params fiels:
        """
        url = ""
        return self.__request(method = 'GET', url=url, params=params)

    def create_(self, _info : dict):
        """

         Функция возвращает  в формате JSON ( dict )

        The function returns the  in JSON format (dict)

        :param _info:
        _info fields:

        """
        url = f""
        resp = self.__request(method = 'POST', url=url, json=_info)
        if (self.print_Flag):
            print(" was created")
        return resp

    def get__info(self, Id):
        """
        Возвращает информацию о

        Returns information about a

        :param Id: ID
        """
        url = f""
        return self.__request(method = 'GET', url=url)

    def change_(self, Id, _info : dict):
        """
        Изменяет  и возвращает его обновленные данные в форме JSON ( dict ).


        Modifies the  and returns its updated data in JSON (dict) form.

        :param Id: ID
        :param _info: Новые данные
        payment_info fields:
        """
        url = f""
        resp = self.__request(method = 'POST', url=url, json=_info)
        if (self.print_Flag):
            print(" was updated")
        return resp

    def delete_(self, Id):
        """
        Удаляет  из системы.

        Removes the  from the system.

        :param Id: ID
        """
        url = f""
        self.__request(method='DELETE', url=url, void=True)
        if (self.print_Flag):
            print(" was deleted")
