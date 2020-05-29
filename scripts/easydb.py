#!/usr/bin/env python3
import sqlite3
from os.path import isdir

class EasyDb:
    def __init__(self, options, auto = True):
        self.is_connected = False
        self.errors = []

        if auto:
            if self.connectToDb(options):
                self.is_connected = True

        else:
            # if the autoconnection is disabled, you will have to handle the is_connected variable switch!
            pass
    
    def sendCommand(self, command, want_return = True, one = False) -> list :
        "Send command to the db and returns with that answer"
        self.db_cur.execute(command)
        self.db_con.commit()
        
        if not one:
            result = self.db_cur.fetchall()
        else:
            result = self.db_cur.fetchone() 

        if want_return:
            return result

    def _checkDbState(self, options) -> bool:
        "Check the db state and try to build a correct one if needed"

        def creatorBuilder(table_name, table_infos):
            "Build the create command"
            creator = f"CREATE TABLE '{table_name}' ("
            blocks = table_infos.split(";")

            for i, block in enumerate(blocks):
                block_infos = block.split(":")
                if len(block_infos) > 1:
                    creator += "'" +  block_infos[0] +  "' " + block_infos[1]
                else:
                    creator += block_infos[0] # special commands, like FOREIGN KEYs

                if len(blocks) > 1:
                    if i != len(blocks) - 1:
                        creator += ", "
            
            creator += ");"

            return creator
        
        def checkCorrectivity(table_state) -> str:
            "Checks correctness of a table structure"
            check_str = ""
            for i, row in enumerate(table_state):
                check_str += ":".join(row[1:3])

                if len(table_state) > 1:
                    if i != len(table_state) - 1:
                        check_str += ";"
            
            return check_str

        db_state = True
        tables = options["tables"]
        requires_fill = options["requires_fill"] # this contains those tables and that's columns which requires to be filled
        need_to_fill = len(requires_fill.keys())

        try:
            for table in tables.keys() :
                table_state = self.sendCommand(f"PRAGMA table_info({table});")

                if not table_state:
                    # table is empty, so we have to create it
                    self.sendCommand(creatorBuilder(table, tables[table]), want_return=False)
                else:
                    check_str = checkCorrectivity(table_state)
                    checksum_str = ""

                    # because PRAGMA only gives back the cell names and those descriptions are not included
                    checksum_table_list = tables[table].split(";")
                    for i, cell in enumerate(checksum_table_list): # split the json row config line into blocks
                        cell_list = cell.split(":") # cell name:cell desc.
                        if len(cell_list) > 1:
                            # we the cell is a real cell and not a special setting like FOREIGN KEY
                            checksum_cell = ""
                            if i != 0: checksum_cell += ";" # with this method, i avoid a lot of problem, like what if
                            #> the last parament in the cell_list is a special command ? (like FOREIGN KEY) than
                            #> the structure would be like this "name1:FORMAT;name2:FORMAT;"" (!) i would have one more ";"

                            checksum_cell += f"{cell_list[0]}:{cell_list[1].split()[0]}" # the user has to make tables with cells that has special settings
                            checksum_str += checksum_cell

                    if check_str != checksum_str:
                        raise Exception("Incorrect database: " + f"{check_str} != {checksum_str}")

                if need_to_fill:
                    if table in requires_fill.keys() :
                        if not table_state:
                            # if the table is empty
                            column_dict = requires_fill[table]
                            keys = str(tuple(column_dict.keys()))
                            datas = str(tuple(column_dict.values()))

                            sql_command = "INSERT INTO '{0}' " + keys + " VALUES " + datas + ";"
                            sql_command = sql_command.format(table)
                            self.sendCommand(sql_command, False)

        except Exception as err:
            self.errors.append(err) # TODO: make a logfile
            db_state = False
        
        return db_state

    def connectToDb(self, options) -> bool:
        "Try to connect to database and check that state"
        connected = False
        if "/" in options["src"]:
            path = "/".join(options["src"].split("/")[:-1])
            if not isdir(path):
                self.errors.append("There is no such file or director!")
                return connected

        self.db_con = sqlite3.connect(options["src"])
        self.db_cur = self.db_con.cursor()
   
        if self._checkDbState(options):
            connected = True

        return connected

    def getState(self) -> bool:
        "Returns with the connection state"
        return self.is_connected
    
    def getErrors(self) -> list:
        "Returns with the errors"
        return self.errors

if __name__ == "__main__":
    # test
    test = {"src": "test.db",
            "tables": {"users": "name:TEXT;passw:TEXT",
                       "log": "name:TEXT;info:TEXT",
                       "test": "a:INTEGER;b:TEXT"},
            "requires_fill": {"test": {"a": 15, "b": "alma"}}}
    
    test_obj = EasyDb(test)
