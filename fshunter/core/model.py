from pymongo import MongoClient, ASCENDING, DESCENDING

from fshunter.helper.config import load


class Model:
    def __init__(self):
        self.config = load()
        self.client = MongoClient(
            self.config.get('mongodb', 'host'),
            int(self.config.get('mongodb', 'port')),
            maxPoolSize=50)

    def marketplace(self, start=0, rows=10, order="_id asc", mp_id=None,
                    mp_name=None, mp_link=None, mp_sessions_url=None,
                    mp_item_index_url=None):
        try:
            db = self.client[self.config.get('mongodb', 'database')]
            collection = db[self.config.get('mongodb', 'collection')]

            criteria = []
            where_clause = dict()
            if mp_id:
                criteria.append({"_id": mp_id})
            if mp_name:
                criteria.append({"mp_name": mp_name})
            if mp_link:
                criteria.append({"mp_link": mp_link})
            if mp_sessions_url:
                criteria.append({"mp_sessions_url": mp_sessions_url})
            if mp_item_index_url:
                criteria.append({"mp_item_index_url": mp_item_index_url})
            if criteria:
                where_clause["$and"] = criteria

            field, direction = order.split(' ')
            if direction.lower() == 'desc':
                sort = (field, DESCENDING)
            else:
                sort = (field, ASCENDING)

            data = collection\
                .find(where_clause)\
                .sort([sort])\
                .skip(start)\
                .limit(rows)

            return Return(data=data)
        except Exception:
            raise


class Return:
    def __init__(self, data):
        self.fetchall = [d for d in data]
        self.rows_count = data.count()
        if self.rows_count > 0:
            self.fetchone = self.fetchall[0]
