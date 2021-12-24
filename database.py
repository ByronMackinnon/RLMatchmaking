import os
import json

import aiosqlite

DB_PATH = "data.db"

class Database:
    def __init__(self, database):
        if database.endswith(".db"):
            self.db = DB_PATH.format(database)
        else:
            self.db = f"{DB_PATH.format(database)}.db"
        self.conn = None

    async def __aenter__(self):
        self.conn = await aiosqlite.connect(self.db)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            await self.conn.commit()
        except Exception as e:
            print(e)
        
        try:
            await self.conn.commit()
        except Exception as e:
            print(e)

    async def select(self, sql=None, variables=tuple(), chunked=False):
        """Helper method for grabbing information from database."""
        org_conn = self.conn
        if org_conn is None:
            self.conn = await aiosqlite.connect(self.db)
        db = self.conn
        cursor = await db.execute(sql, variables)

        if chunked:
            rows = await cursor.fetchall()
            await cursor.close()

            values = [item for t in rows for item in t]
            if sql.count(",") == 0:
                new_values = []
                for value in values:
                    try:
                        test_value = json.loads(value)
                        new_values.append(test_value)
                    except Exception as e:
                        new_values.append(value)
                return new_values

            async def chunks(lst, length): #* This is a helper function to organize the data so it returns a list of lists.
                length = max(1, length)
                raw_list = list(lst[i:i+length] for i in range(0, len(lst), length))
                # processed_list = []
                # for element in raw_list:
                #     temp_list = []
                #     for item in element:
                #         try:
                #             test = json.loads(item)
                #             temp_list.append(test)
                #         except Exception:
                #             temp_list.append(item)
                #     processed_list.append(temp_list)
                # return processed_list
                return raw_list

            chunk_length = len(sql.split(','))

            if org_conn is None:
                await self.conn.close()

            return await chunks(values, chunk_length)

        else:
            row = await cursor.fetchone()
            await cursor.close()

            #* If nothing is returned - Nothing happens
            if row is None:
                pass

            #* If only a single result is returned. It gets turned to it's proper data type
            elif len(row) == 1:
                try:
                    row = int(row[0])
                except (TypeError, ValueError):
                    try:
                        row = json.loads(row[0])
                    except Exception as e:
                        row = str(row[0])

            #* Otherwise it is returned as a list
            else:
                row = list(row)
                temp_row = []
                for element in row:
                    if isinstance(element, str):
                        try:
                            element = json.loads(element)
                        except:
                            pass
                    temp_row.append(element)
                row = temp_row

            if row == "None":
                row = None

            if org_conn is None:
                await self.conn.close()

            return row

    async def update(self, sql=None, variables=dict()):
        """Edit data from the database."""
        if not isinstance(variables, dict):
            raise ValueError("VARIABLES KWARG IN UPDATE METHOD FOR DATABASE CAN'T BE ANYTHING OTHER THAN DICT YOU STUPID FUCKING CUNT")

        for k, v in variables.items():
            if isinstance(v, (dict, list, tuple)):
                variables[k] = json.dumps(v)

        org_conn = self.conn
        if org_conn is None:
            self.conn = await aiosqlite.connect(self.db)

        db = self.conn
        await db.execute(sql, variables)
        if org_conn is None:
            await self.conn.close()

    async def found_in(self, sql=None, variables=tuple()) -> bool:
        """Returns a boolean based on whether or not the SQL query was able to return any data."""
        org_conn = self.conn
        if org_conn is None:
            self.conn = await aiosqlite.connect(self.db)
        db = self.conn
        async with db.execute(sql, variables) as cursor:
            check = await cursor.fetchone()
            org_conn = self.conn
            if org_conn is None:
                self.conn = await aiosqlite.connect(self.db)

            if check is None:
                return False
            return True
